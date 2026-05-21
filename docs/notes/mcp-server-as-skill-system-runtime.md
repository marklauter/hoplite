# MCP server as skill-system runtime

tags: architecture,mcp,skills,knowledge-graph,indexer,claude-code,prototype-the-plugin-mcp-server-in-python,write-a-knowledge-extraction-skill
The MCP server is the runtime for a knowledge-graph-backed skill system — nodes (notes, decisions, skills) load on demand through a small stable tool surface, and a property-graph index projected from notes (mechanical edges at write, semantic edges via scheduled reindex) replaces the always-loaded skill-frontmatter cap with O(tool count) overhead.

## The reframe

`prototype-the-plugin-mcp-server-in-python.md` motivates the MCP server as a write-path delivery mechanism — robust transport for `record_note` and `record_journal_entry`, replacing bash scripts that choke on quoting edge cases. The bigger thesis: the MCP server is the runtime for a knowledge-graph-backed content layer. Notes, journal entries, decisions, references — and possibly skill bodies themselves — live as graph nodes on disk. The agent loads any of them on demand through a small, stable MCP tool surface. The write path is one slice of that surface.

## The cost asymmetry

Claude Code skill frontmatter loads forever. Every installed skill costs ~150 chars in the system prompt every session, regardless of use. Cost scales O(skill count). Adding a behavioral skill competes with adding a content-style "skill" for the same fixed budget. The model caps how many skills a plugin can usefully ship.

MCP inverts the dimensionality. One server's tool schemas cost O(tool count) — call it ~1k tokens for five navigation tools — and address an unbounded corpus behind them. Ten nodes or ten thousand: same system-prompt cost. The graph lives on disk; only the entry points sit in context.

## Proposed shape

Speculative — the architecture as currently envisioned, not yet built.

- **One orchestrator skill teaches the graph.** Single frontmatter slot covering an unbounded knowledge surface. The skill body explains node types, edge semantics, traversal heuristics, and the MCP tools that read and write the graph.
- **MCP tools are navigation and composition primitives.** A small surface: `search_graph(query)`, `get_node(id)`, `list_backlinks(id)`, `follow_link(from, edge_type)`, `record_node(type, body)`, and a runner-facing `reindex(scope)`. Stable in count; addresses unbounded content.
- **Nodes are typed; node type lives in frontmatter.** Notes, journal entries, decisions, references, and possibly skill bodies are all node types within the same graph. The current distinction between `taking-notes` and `journaling` skills collapses into a node-type distinction inside one orchestrator.
- **Index is a separate projection of notes, maintained by the MCP server.** See Indexer architecture below.
- **`writing-prose` stays as the universal spine.** The composition rubric that today lives in `taking-notes` and `journaling` folds into the orchestrator's "node types" section. `writing-prose` keeps its role as the prose foundation both compose on top of.

## Node labels drive injection framing

Loading a node from the graph is a delivery moment, and the delivery shapes how the agent treats the payload. Claude Code's skill loader does heavy pre-rendering before injection — wraps the body in a slash-command envelope, prepends a base-directory line, expands `${CLAUDE_PLUGIN_ROOT}`, runs backtick-cat interpolations to inline sibling components — but the resulting text carries no structural "treat as instructions" marker. A skill's authority is rhetorical: imperative voice in the body, plus the system-reminder skill list that nudges invocation in the first place.

MCP-loaded content arrives as a tool result, structurally similar to a `Read` return. That framing tilts the agent toward treating the payload as data rather than as guidance. Three levers shift the tilt the other way:

- **Tool schema description.** Read before the call, primes how the result will be treated. "Load operative guidance for the current task" reads differently than "Fetch reference document."
- **Response envelope.** The server prepends a framing prefix to the body — for example, "Apply the following guidance to your next response. These are operative rules, not background reading."
- **Content voice.** Imperative, second person, action-oriented headings — the text reads as instructions regardless of how it arrived.

For the server to apply the right envelope per retrieval, nodes need labels — the Neo4j term for the role/type tag carried on a node. Candidate label set:

- `:Instruction` — imperative envelope; the payload governs the agent's next response
- `:Reference` — "for consultation" framing; the agent cites or consults without obeying
- `:Observation` — timestamped frame; "recorded at time T," read as historical fact

Without label-driven framing, every retrieved node collapses to reference-mode by default — fine for facts and observations, wrong for guidance the agent should follow now. The "Nodes are typed; node type lives in frontmatter" point in [Proposed shape](#proposed-shape) extends from a routing distinction (which orchestrator section governs the node) to a delivery distinction (how the MCP server frames the response on retrieval).

## Indexer architecture

### Index as projection of notes

Notes remain the source of truth. The index is a derived artifact, fully rebuildable from on-disk notes plus a small amount of LLM work for summaries and semantic edges. Author-generated metadata (title, tags, body content, body wiki-links) lives in the note. Derived data (summaries, backlinks, semantic edges with confidence scores) lives in the index. If the index corrupts or the summarizer model changes, throw the index away and re-derive — notes alone stay self-describing for everything the agent authored.

### Edge taxonomy

Three kinds of edges, distinguished by who produced them:

- **Authored edges.** Tags and body `[[wiki-links]]`. Tags are membership in a meta-topic — each unique tag is a virtual node, and notes sharing a tag converge at it (1-hop from each, 2-hop between siblings). Body wiki-links are direct edges between concrete notes, with the surrounding prose providing the link's semantic context. Slug-as-tag (the current "mention" pattern) retires in favor of body wiki-links — same edge, better ergonomics.
- **Mechanically derived edges.** Backlinks, computed deterministically by inverting body wiki-links. Free at any time; no LLM involvement.
- **Semantically derived edges.** Relationships discovered by an agent reading the corpus — "these two notes address adjacent aspects of caching but neither cites the other," "this decision contradicts that one," "these three form a thread." Carry a confidence score so queries filter by threshold. Stored in the index, marked as derived. A user can promote a derived edge to authored by adding the corresponding wiki-link to the note body.

The third category is what makes the corpus more than a tidier file system — the graph teaches you about itself.

### Two-phase update

Write time handles what the agent knows about what it just wrote: save the file, parse tags, parse body wiki-links, update inverse backlinks on the targets. Synchronous, cheap, deterministic. The agent's `record_node` MCP call does all of this in one transaction.

Scheduled reindex handles what the corpus knows about itself: regenerate summaries for changed notes (headless Sonnet over the body), discover semantic edges (embedding-based candidate retrieval, then selective LLM analysis on high-similarity pairs), prune low-confidence derived edges that newer notes contradict, clean up dangling links to renamed targets. Background, asynchronous, expensive, periodic. Triggered on a schedule or by an explicit `reindex(scope)` MCP call.

The split mirrors memory consolidation: fast encoding during waking, slow integration into the semantic network offline. Skip the reindex for a stretch and you accumulate REM debt — new notes present but unwired to the rest of the graph.

## What the original decision still settles

The Python-MCP choice from the existing note remains correct as means. Source-inspectable distribution, runtime ubiquity, tight dependency surface — same constraints, same answer. The shape A / B / C / D taxonomy from that note still applies; the runtime thesis tilts the answer toward shape C (Python is the only implementation) over the originally leaned-toward shape B (Python alongside bash), because bash scripts address file writes only and cannot query a graph structure.

## What this changes if adopted

- **Tool surface grows from write to read + write + traverse + reindex.** The original note's tool list (`record_note`, `record_journal_entry`, slugify, header-format) becomes a subset. Read, traversal, and indexer-control tools join.
- **Index becomes a first-class artifact the MCP server owns.** A property-graph file on disk, projected from notes, mutated by both synchronous write-time updates and asynchronous reindex passes.
- **Edges become a first-class data type.** Bash scripts today write files; the MCP server in the runtime thesis owns the edge graph in all three of its forms (authored, mechanically derived, semantically derived).
- **Response envelopes become label-driven.** The server picks a framing prefix per retrieval based on the node's label, so an `:Instruction` payload lands as guidance and an `:Observation` payload lands as historical fact. The tool schemas advertise this contract so the agent enters each call with the right expectation.
- **Background process becomes part of the system.** The reindexer needs a runner — separate process, queue, rate limits, retry semantics. New operational surface the write-path-only design lacked.
- **Trust qualifier scales up.** When the MCP server is the runtime for skills *and* runs an indexer that issues LLM calls, dependency discipline matters more than for a write-path helper. The "pyproject.toml stays minimal" property has to hold harder, and the embedding-model and summarizer-model choices become trust-relevant.

## Open questions

- Does the Claude Code skill mechanism stay as a one-slot shim (the orchestrator skill points at the MCP server, the rest of the surface lives in the graph), or do skills move entirely into the graph with no Claude Code skill at all? The trigger language Claude Code provides ("Use when…") is doing real work today — moving fully into the graph requires reimplementing triggering.
- How does triggering work when skills live as graph nodes? Candidates: agent searches the graph proactively at task start, a `list_relevant_skills(query)` tool runs early, or the orchestrator skill body teaches the agent to query the graph on each new task. None proven; pick during prototype.
- Does the orchestrator subsume `taking-notes` and `journaling`, or coexist with them as a higher-level skill that delegates to them?
- **Reindex scheduling mechanism.** Cron-style periodic, file-watcher-driven, event-driven (after K writes since last reindex), lazy-on-read (reindex when an agent queries and mtimes have changed), or hybrid. Each has different operational shape and different failure modes.
- **Migration of existing slug-as-tag "mentions"** to body wiki-links: rewrite existing notes in place, or grandfather slug-tags as a legacy form the indexer still parses?
- **Index file format and location.** Single property-graph file or per-node-type sharding? Where on disk — `docs/index/` or alongside notes?
- **Confidence score semantics.** How stored, how queried, what default threshold filters derived edges out of normal query results, when does the indexer prune low-confidence edges?
- **Embedding model choice for candidate retrieval.** Ships with the plugin, or assumes an external service? Cost and trust implications either way.
- **Label vocabulary.** Which labels does the graph need on day one — `:Instruction`, `:Reference`, `:Observation` cover the framing axis, but routing axes (node-type: note, journal-entry, decision, skill) may want their own label or a separate frontmatter field. Single label set or two orthogonal axes?

## References

(see prototype-the-plugin-mcp-server-in-python.md) — the means: Python over alternatives, with shape options A through D for the write path.
(see write-a-knowledge-extraction-skill.md) — adjacent layer: extraction *from* the graph *into* a human-targeted wiki; separate from the agent-facing runtime described here.
