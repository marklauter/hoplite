---
title: MCP server as skill-system runtime
summary: The MCP server is the runtime for a knowledge-graph-backed skill system — nodes load on demand through a small stable tool surface, replacing the always-loaded skill-frontmatter cap with O(tool count) overhead.
tags: [note, hoplite, mcp, thesis, architecture]
created: 2026-05-25
aliases: []
---

> See `[[mcp-graph-runtime-data-model]]` for the resolved day-one specification. This note records the design exploration that led there. Sections marked _superseded_ below preserve the discovery path; specifics like tool names, edge types, and label capitalization have since been refined. The data-model is canonical when they conflict.

## The reframe

`[[prototype-the-plugin-mcp-server-in-python]]` motivates the MCP server as a write-path delivery mechanism — transport for `record_note` and `record_journal_entry`, replacing bash scripts that choke on quoting edge cases. The bigger thesis: the MCP server is the runtime for a knowledge-graph-backed content layer. Notes, journal entries, decisions, references — and possibly skill bodies themselves — live as graph nodes on disk. The agent loads any of them on demand through a small, stable MCP tool surface. The write path is one slice of that surface.

## The cost asymmetry

Claude Code skill frontmatter loads forever. Every installed skill costs ~150 chars in the system prompt every session, regardless of use. Cost scales O(skill count). Adding a behavioral skill competes with adding a content-style "skill" for the same fixed budget. The model caps how many skills a plugin can usefully ship.

MCP inverts the dimensionality. One server's tool schemas cost O(tool count) — call it ~1k tokens for a handful of navigation tools — and address an unbounded corpus behind them. Ten nodes or ten thousand: same system-prompt cost. The graph lives on disk; only the entry points sit in context.

## Proposed shape

_Superseded — see `[[mcp-graph-runtime-data-model]]` for the locked tool surface and node-type decisions._

Speculative — the architecture as currently envisioned, not yet built.

- One orchestrator skill teaches the graph. Single frontmatter slot covering an unbounded knowledge surface. The skill body explains node types, edge semantics, traversal heuristics, and the MCP tools that read and write the graph.
- MCP tools are navigation and composition primitives. Minimum viable surface: `get_node(id)`, `find_entry(query)`, `record_node(type, body)`, and a runner-facing `reindex(scope)`. Global-query tools (`search_graph`, `list_backlinks`, `follow_link`) join later if a real query pattern demands them. See [Progressive disclosure](#progressive-disclosure--traversal-pattern).
- Nodes are typed; node type lives in frontmatter. Notes, journal entries, decisions, references, and possibly skill bodies are all node types within the same graph. The current distinction between `taking-notes` and `journaling` skills collapses into a node-type distinction inside one orchestrator.
- Index is a separate projection of notes, maintained by the MCP server. See [Indexer architecture](#indexer-architecture).
- `[[writing-prose]]` stays as the universal spine. The composition rubric that today lives in `[[taking-notes]]` and `[[journaling]]` folds into the orchestrator's "node types" section. `writing-prose` keeps its role as the prose foundation both compose on top of.

## Node labels drive injection framing

_Superseded — framing labels are lowercase (`instruction`, `reference`, `observation`) in the data-model, and framings collapsed into the labels axis. Framing also splits by verb: `invoke` applies the framing-axis label's envelope; `read` applies a fixed label-independent content envelope. The discovery here remains correct; the names and the verb-asymmetry have been refined._

Loading a node from the graph is a delivery moment, and the delivery shapes how the agent treats the payload. Claude Code's skill loader does heavy pre-rendering before injection — wraps the body in a slash-command envelope, prepends a base-directory line, expands `${CLAUDE_PLUGIN_ROOT}`, runs backtick-cat interpolations to inline sibling components — but the resulting text carries no structural "treat as instructions" marker. A skill's authority is rhetorical: imperative voice in the body, plus the system-reminder skill list that nudges invocation in the first place.

MCP-loaded content arrives as a tool result, structurally similar to a `Read` return. That framing tilts the agent toward treating the payload as data rather than as guidance. Three levers shift the tilt the other way:

- Tool schema description. Read before the call, primes how the result will be treated. "Load operative guidance for the current task" reads differently than "Fetch reference document."
- Response envelope. The server prepends a framing prefix to the body — for example, "Apply the following guidance to your next response. These are operative rules, not background reading."
- Content voice. Imperative, second person, action-oriented headings — the text reads as instructions regardless of how it arrived.

For the server to apply the right envelope per retrieval, nodes need labels — the Neo4j term for the role/type tag carried on a node. Candidate label set:

- `:Instruction` — imperative envelope; the payload governs the agent's next response
- `:Reference` — "for consultation" framing; the agent cites or consults without obeying
- `:Observation` — timestamped frame; "recorded at time T," read as historical fact

Without label-driven framing, every retrieved node collapses to reference-mode by default — fine for facts and observations, wrong for guidance the agent should follow now. The "Nodes are typed" point in [Proposed shape](#proposed-shape) extends from a routing distinction (which orchestrator section governs the node) to a delivery distinction (how the MCP server frames the response on retrieval).

The parallel that confirms the broader pattern: an LSP server exposes a graph too — symbols as nodes, edges like `:defined-at`, `:references`, `:implements` — and clients walk it lazily. The graph-shaped retrieval is older than MCP. What's specific to the LLM-facing case is envelope framing; LSP returns structured location data for an editor to render, with no need to tell the consumer how to read the payload.

## Progressive disclosure — traversal pattern

_Superseded — the tools are `match`, `load`, `read`, `write`, `traverse` in the data-model. The traversal model (aid-station, depth-first from landings) is retained._

The agent's query pattern is depth-first from a landing page, not global filter. An aid-station flowchart: enter at "tell me where it hurts," follow the answer to the next page, repeat. The patient never asks for the full table of contents.

A corpus designed this way needs only two reads to be navigable:

- `get_node(id)` — returns the node body, framing envelope, and outgoing edges with labels.
- `find_entry(query)` — locates a landing page when the agent doesn't know where to start.

A wiki home page is one landing. A graph with several domains has several — and any well-connected interior node functions as a sub-landing for its neighborhood. The orchestrator skill enumerates a handful of top-level entries; deeper landings emerge from traversal.

This collapses what the indexer must do at query time. Global queries ("all decisions," "all edges with confidence > 0.8") become later optimizations, not day-one features. The earlier-imagined tool list (`search_graph`, `list_backlinks`, `follow_link`) reduces to `get_node` + `find_entry` until a real query pattern demands more.

Edges carry the navigational weight. `:elaborates`, `:contradicts`, `:requires`, `:next-step`, `:see-also` — the vocabulary is what makes the book navigable. Without rich edge labels, the agent reaches a node but can't choose its next step.

## Composable skills via dependency edges

_Superseded — skills are deferred from the day-one graph; they stay as Claude Code skills bootstrapping from the CLI. The composition pattern described here applies when skills enter the graph in a later pass._

Skills are graph nodes carrying the `:Instruction` label and `:requires` edges to other skill-nodes. A "skill that knows how to load skills" is a meta-node whose body teaches the traversal protocol: enter at a landing, follow `:requires` edges, fetch each target with the instruction envelope.

The foundation/consumer pattern (today `[[taking-notes]]` composes `[[writing-prose]]` via prose reference and an inline backtick-cat) becomes a graph edge. Same coupling, mechanism instead of convention. `taking-notes -[:requires]-> writing-prose`. The loader follows the edge automatically.

Two strategies for how the loader handles dependencies:

- Pre-render. One `get_node` call returns the consumer's body with its `:requires` targets inlined. Simpler for the agent, recreates the heavy-context problem for large composites.
- Lazy. `get_node` returns only the requested node; dependencies appear as edges the agent traverses with follow-on calls. More tool calls; only used dependencies land in context.

Lazy by default fits the aid-station model — pages the agent doesn't traverse to never load. The edge itself can carry `{inline: true}` to opt into pre-render for tightly-coupled compositions where a separate fetch would feel pedantic.

Side benefit: edges can carry versions. A skill node may have several bodies; the `:requires` edge pins which one the consumer reads. Skill versioning emerges from the graph model without a dedicated mechanism.

## Tag-nodes as first-class graph nodes

_Superseded — tags collapsed into the general label axis. Every label is a node-like file at `docs/index/labels/<label>.md` with a members list and optional behavior-modifier body; there is no separate `:Tag` label type and no `:contains` edge. The insight that categorical membership wants first-class node files survives; the naming has been refined._

Categorical membership becomes a node type rather than a flat property or a virtual lookup. Every tag has a sidecar at `docs/index/<tag>.md`, carries the `:Tag` label, owns its membership outbound, and serves as a landing page the agent reaches through `find_entry`.

Why nodes and not properties: in any property graph, finding all notes tagged X requires an index over the property values. In a filesystem-as-graph model with no engine maintaining hidden state, that index has to live on disk as a file mapping tag-name to members — functionally identical to a tag-node's outbound edges, renamed and accessed through a dedicated tool. Surfacing the index as a node keeps the design uniform: every thing the agent reads is a node fetched through `get_node`.

Single-side ownership. The tag-node holds the membership edges outbound (`:contains` from the tag to each member note). A note's authored `tags: [skills]` field in its own markdown frontmatter is input to the indexer, not an edge stored on the note's sidecar. The indexer reads each note's tag list and projects the corresponding `:contains` edges onto the relevant tag-nodes. Adding or removing a tag touches one file (the tag-node); no two-sided storage, no cache invalidation, no write amplification.

Traversal stays clean. From a note, the agent follows direct content edges (`:cites`, `:contradicts`, `:requires`, `:see-also`) to other concrete nodes. To find category siblings, the agent climbs to the tag-node — reached via `find_entry`, not via an edge from inside a member. The wiki analog: an article doesn't list its sister-articles inline; the category page does.

Tag-nodes carry their own metadata. A hand-written summary explains what the category covers; prose in the body holds canonical landing content; outbound edges to parent tags form a hierarchy. Day-one tag-nodes autocreate with empty bodies the first time a note references them; a curator fills in the ones that warrant content.

One trade worth naming. From a note's sidecar, the agent can't directly enumerate "what categories is this in" without scanning tag-nodes or hitting a derived cache. Per [Progressive disclosure](#progressive-disclosure--traversal-pattern), the agent reaches a note through a landing or by name, so the path discloses the topic context. If reverse lookup ever becomes a hot path, add a `docs/index/_meta.json` entry per note mapping note → tags.

## Indexer architecture

_Superseded — the data-model locks: storage layout (`docs/index/<id>.md` flat sidecars; `docs/index/labels/<label>.md` inverted index); two day-one edge types (`mentions`, `related`); reindex deferred (no two-phase update day one — synchronous write-time only); BM25 day one for `match`; embeddings via Ollama later. The discussion below preserves the design exploration; the data-model is canonical for what ships._

### Index as projection of notes

Notes remain the source of truth. The index is a derived artifact, fully rebuildable from on-disk notes plus a small amount of LLM work for summaries and semantic edges. Author-generated metadata (title, body content, body wiki-links) lives in the note. Derived data (summaries, backlinks, semantic edges with confidence scores) lives in the index. If the index corrupts or the summarizer model changes, throw the index away and re-derive — notes alone stay self-describing for everything the agent authored.

### Edge taxonomy

Three kinds of edges, distinguished by who produced them:

- Authored edges. Body `[[wiki-links]]` between concrete notes, with the surrounding prose providing the link's semantic context. Tag-node outbound `:contains` edges, projected by the indexer from each note's authored `tags:` field — see [Tag-nodes](#tag-nodes-as-first-class-graph-nodes).
- Mechanically derived edges. Backlinks, computed deterministically by inverting body wiki-links. Free at any time; no LLM involvement.
- Semantically derived edges. Relationships discovered by an agent reading the corpus — "these two notes address adjacent aspects of caching but neither cites the other," "this decision contradicts that one," "these three form a thread." Carry a confidence score so queries filter by threshold. Stored in the index, marked as derived. A user can promote a derived edge to authored by adding the corresponding wiki-link to the note body.

The third category is what makes the corpus more than a tidier file system — the graph teaches you about itself.

### Two-phase update

Write time handles what the agent knows about what it just wrote: save the file, parse body wiki-links, update inverse backlinks on the targets. Synchronous, cheap, deterministic. The agent's `record_node` MCP call does all of this in one transaction.

Scheduled reindex handles what the corpus knows about itself: regenerate summaries for changed notes (headless Sonnet over the body), discover semantic edges (embedding-based candidate retrieval, then selective LLM analysis on high-similarity pairs), prune low-confidence derived edges that newer notes contradict, clean up dangling links to renamed targets. Background, asynchronous, expensive, periodic. Triggered on a schedule or by an explicit `reindex(scope)` MCP call.

The split mirrors memory consolidation: fast encoding during waking, slow integration into the semantic network offline. Skip the reindex for a stretch and you accumulate REM debt — new notes present but unwired to the rest of the graph.

### Sidecar format — markdown + YAML frontmatter

Per-node sidecar files at `docs/index/<slug>.md`, mirroring the note format the corpus already uses. YAML frontmatter carries the structured edges; the body holds optional prose (derived summary, indexing notes, anything human-readable).

A note-node sidecar carries only direct content edges — no tag edges, since tag membership lives on the tag-node side:

```markdown
---
id: foo
labels: [Note, Reference]
summary: cached one-liner the scanner reads
out_edges:
  - type: cites
    to: bar
  - type: contradicts
    to: baz
    confidence: 0.7
    rationale: foo claims X, baz claims not-X
embedding: foo.npy
---

(optional prose)
```

A tag-node sidecar carries the membership outbound, plus optional hierarchy edges to parent tags:

```markdown
---
id: skills
labels: [Tag]
summary: notes and decisions about the Claude Code skill system
out_edges:
  - type: contains
    to: mcp-server-as-skill-system-runtime
  - type: contains
    to: prototype-the-plugin-mcp-server-in-python
  - type: parent
    to: claude-code
---

(optional prose — what this category covers, canonical landing content)
```

The filesystem becomes the index. One sidecar per node gives free diff locality (one note changes → one sidecar changes), free concurrency (writes to different nodes never contend), free per-node rebuild, and `ls docs/index/` as a node enumerator.

The cost is global queries — "all nodes with label X" or "all edges with confidence > 0.8" goes O(N file reads). Per [Progressive disclosure](#progressive-disclosure--traversal-pattern), global queries defer until needed. When they arrive, a small `docs/index/_meta.json` enumeration cache (`id → labels, summary`) handles the common ones without opening every sidecar.

Backlinks stay derived. Invert outgoing edges across the corpus when asked. Once N hurts, cache the inversion into each sidecar's `in_edges` field at write time.

YAML gotcha worth planning for: implicit string-to-bool/float coercion. `NO`, `ON`, `OFF`, `YES`, `Y`, `N` parse as booleans; `1.0` parses as float; `1.10` parses as version-mangled. If any label name, edge type, or rationale string lands on one of those, the parse silently changes the value. Use `ruamel.yaml` in strict mode, or quote string values consistently in the writer.

## What the original decision still settles

The Python-MCP choice from the existing note remains correct as means. Source-inspectable distribution, runtime ubiquity, tight dependency surface — same constraints, same answer. The shape A / B / C / D taxonomy from that note still applies; the runtime thesis tilts the answer toward shape C (Python is the only implementation) over the originally leaned-toward shape B (Python alongside bash), because bash scripts address file writes only and cannot query a graph structure.

## What this changes if adopted

_Superseded — see the data-model for the concrete day-one delta. Bullets below describe the broader thesis-level changes; specific tool names and labels have been refined._

- Tool surface grows from write to read + write. The original note's tool list (`record_note`, `record_journal_entry`, slugify, header-format) becomes a subset. Read tools (`get_node`, `find_entry`) and indexer control (`reindex`) join. Global-query tools wait for a query pattern that needs them.
- Index becomes a first-class artifact the MCP server owns. Per-node sidecar files on disk, projected from notes, mutated by both synchronous write-time updates and asynchronous reindex passes.
- Edges become a first-class data type. Bash scripts today write files; the MCP server in the runtime thesis owns the edge graph in all three of its forms (authored, mechanically derived, semantically derived).
- Response envelopes become label-driven. The server picks a framing prefix per retrieval based on the node's label, so an `:Instruction` payload lands as guidance and an `:Observation` payload lands as historical fact. The tool schemas advertise this contract so the agent enters each call with the right expectation.
- Lazy traversal becomes the default loading discipline. `get_node` returns only the requested node; the agent walks `:requires` and other edges on demand. Pre-render is opt-in per edge for tight compositions.
- Tags become first-class nodes. Each tag has a `:Tag`-labeled sidecar reachable via `find_entry`, owning its `:contains` edges outbound to member notes. Notes carry `tags: [...]` only as authoring input the indexer projects; note sidecars store no tag edges.
- Background process becomes part of the system. The reindexer needs a runner — separate process, queue, rate limits, retry semantics. New operational surface the write-path-only design lacked.
- Trust qualifier scales up. When the MCP server is the runtime for skills *and* runs an indexer that issues LLM calls, dependency discipline matters more than for a write-path helper. The "pyproject.toml stays minimal" property has to hold harder, and the embedding-model and summarizer-model choices become trust-relevant.

## Open questions

All resolved or explicitly deferred in `[[mcp-graph-runtime-data-model]]`. Refer there for current status; the data-model is canonical when this note's specifics conflict with it.

## References

[[prototype-the-plugin-mcp-server-in-python]] — the means: Python over alternatives, with shape options A through D for the write path.
[[write-a-knowledge-extraction-skill]] — adjacent layer: extraction *from* the graph *into* a human-targeted wiki; separate from the agent-facing runtime described here.
