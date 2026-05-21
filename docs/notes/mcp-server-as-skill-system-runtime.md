# MCP server as skill-system runtime

tags: architecture,mcp,skills,knowledge-graph,claude-code,prototype-the-plugin-mcp-server-in-python,write-a-knowledge-extraction-skill
The MCP server reframes from write-path delivery mechanism to runtime for a knowledge-graph-backed skill system — notes, decisions, and skill bodies become graph nodes loaded on demand, replacing the always-loaded skill-frontmatter cap with a small stable tool surface.


## The reframe

`prototype-the-plugin-mcp-server-in-python.md` motivates the MCP server as a write-path delivery mechanism — robust transport for `record_note` and `record_journal_entry`, replacing bash scripts that choke on quoting edge cases. The bigger thesis: the MCP server is the runtime for a knowledge-graph-backed content layer. Notes, journal entries, decisions, references — and possibly skill bodies themselves — live as graph nodes on disk. The agent loads any of them on demand through a small, stable MCP tool surface. The write path is one slice of that surface.

## The cost asymmetry

Claude Code skill frontmatter loads forever. Every installed skill costs ~150 chars in the system prompt every session, regardless of use. Cost scales O(skill count). Adding a behavioral skill competes with adding a content-style "skill" for the same fixed budget. The model caps how many skills a plugin can usefully ship.

MCP inverts the dimensionality. One server's tool schemas cost O(tool count) — call it ~1k tokens for five navigation tools — and address an unbounded corpus behind them. Ten nodes or ten thousand: same system-prompt cost. The graph lives on disk; only the entry points sit in context.

## Proposed shape

Speculative — the architecture as currently envisioned, not yet built.

- **One orchestrator skill teaches the graph.** Single frontmatter slot covering an unbounded knowledge surface. The skill body explains node types, edge semantics, traversal heuristics, and the MCP tools that read and write the graph.
- **MCP tools are navigation and composition primitives.** A small surface: `search_graph(query)`, `get_node(id)`, `list_backlinks(id)`, `follow_link(from, edge_type)`, `record_node(type, body)`. Stable in count; addresses unbounded content.
- **Nodes are typed; node type lives in frontmatter.** Notes, journal entries, decisions, references, and possibly skill bodies are all node types within the same graph. The current distinction between `taking-notes` and `journaling` skills collapses into a node-type distinction inside one orchestrator.
- **`writing-prose` stays as the universal spine.** The composition rubric that today lives in `taking-notes` and `journaling` folds into the orchestrator's "node types" section. `writing-prose` keeps its role as the prose foundation both compose on top of.

## What the original decision still settles

The Python-MCP choice from the existing note remains correct as means. Source-inspectable distribution, runtime ubiquity, tight dependency surface — same constraints, same answer. The shape A / B / C / D taxonomy from that note still applies; the runtime thesis tilts the answer toward shape C (Python is the only implementation) over the originally leaned-toward shape B (Python alongside bash), because bash scripts address file writes only and cannot query a graph structure.

## What this changes if adopted

- **Tool surface grows from write to read+write+traverse.** The original note's tool list (`record_note`, `record_journal_entry`, slugify, header-format) becomes a subset. Read and traversal tools join.
- **Edges become a first-class data type.** Bash scripts today write files; the MCP server in the runtime thesis owns the edge index. Whether that means parsing `[[wiki-links]]` on the fly, maintaining a derived edge file, or storing edges in node frontmatter is open (see Open questions below).
- **Trust qualifier scales up.** When the MCP server is the runtime for skills, dependency discipline matters more than for a write-path helper. The "pyproject.toml stays minimal" property has to hold harder. Re-read the existing note's Trust qualifier section before each new dependency.

## Open questions

- Does the Claude Code skill mechanism stay as a one-slot shim (the orchestrator skill points at the MCP server, the rest of the surface lives in the graph), or do skills move entirely into the graph with no Claude Code skill at all? The trigger language Claude Code provides ("Use when…") is doing real work today — moving fully into the graph requires reimplementing triggering.
- How does triggering work when skills live as graph nodes? Candidates: agent searches the graph proactively at task start, a `list_relevant_skills(query)` tool runs early, or the orchestrator skill body teaches the agent to query the graph on each new task. None proven; pick during prototype.
- Edge representation. `[[wiki-links]]` inline in body, frontmatter-declared typed edges, or a separate edge file? Affects parser complexity, link discoverability, and edge-type richness.
- Does the orchestrator subsume `taking-notes` and `journaling`, or coexist with them as a higher-level skill that delegates to them? Subsuming is cleaner under the one-slot thesis; coexisting preserves the current rubric layering.

## References

(see prototype-the-plugin-mcp-server-in-python.md) — the means: Python over alternatives, with shape options A through D for the write path.
(see write-a-knowledge-extraction-skill.md) — adjacent layer: extraction *from* the graph *into* a human-targeted wiki; separate from the agent-facing runtime described here.
