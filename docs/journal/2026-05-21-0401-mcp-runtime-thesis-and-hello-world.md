---
title: MCP runtime thesis and the hello-world server
summary: MCP hello-world server lands in the skills plugin; the runtime-thesis note captures the reframe — MCP is the runtime for a knowledge-graph-backed content layer, not just write-path transport for bash replacement.
tags: [journal, mcp, thesis, architecture, milestone]
created: 2026-05-21
---

# MCP runtime thesis and the hello-world server

MCP hello-world server lands in the skills plugin; the runtime-thesis note captures the reframe — MCP is the runtime for a knowledge-graph-backed content layer, not just write-path transport for bash replacement.

## Intent

`[[notes/prototype-the-plugin-mcp-server-in-python]]` had framed the MCP server as a delivery mechanism — Python over bash for `record_note` and `record_journal_entry`, motivated by quoting edge cases in shell. That framing was narrow. The shape session opened with that framing and ended somewhere bigger.

The reframe: MCP is not the new write path. It is the runtime for a content layer that lives as a knowledge graph on disk. Notes, journal entries, decisions, references — and possibly skill bodies themselves — are graph nodes. The agent loads any of them on demand through a small, stable MCP tool surface. The write path is one slice of that surface.

## What landed

- 2026-05-21 04:01 — MCP hello-world server added to the skills plugin. A minimal server with a single tool, just enough to verify the plugin manifest registers MCP servers and the stdio transport works end-to-end.
- 2026-05-21 04:01 — Runtime-thesis evolution captured in `[[mcp-server-as-skill-system-runtime]]`. The note traces the design path from write-path delivery to graph-runtime.

## The argument that crystallized

The cost asymmetry was the load-bearing observation:

- Claude Code skill frontmatter loads forever. Every installed skill costs ~150 chars in the system prompt every session, regardless of use. Cost scales O(skill count). Adding a behavioral skill competes with adding a content-style "skill" for the same fixed budget. The model caps how many skills a plugin can usefully ship.
- MCP inverts the dimensionality. One server's tool schemas cost O(tool count) — ~1k tokens for a handful of navigation tools — and address an unbounded corpus behind them. Ten nodes or ten thousand: same system-prompt cost. The graph lives on disk; only the entry points sit in context.

The proposed shape at the time:

- One orchestrator skill teaches the graph. Single frontmatter slot covering an unbounded knowledge surface.
- MCP tools are navigation primitives: `get_node(id)`, `find_entry(query)`, `record_node(type, body)`, runner-facing `reindex(scope)`.
- Nodes are typed; node type lives in frontmatter. The distinction between `taking-notes` and `journaling` collapses into a node-type distinction inside one orchestrator.
- Index is a separate projection of notes, maintained by the MCP server.
- `writing-prose` stays as the universal spine.

## Subsequent moves the thesis foreshadowed

The thesis note also sketched:

- Label-driven response framing — `:Instruction`, `:Reference`, `:Observation` as envelopes the server applies on retrieval. This was the dominant framing-vs-content distinction for several days.
- Tag-nodes as first-class — every tag a node with its own sidecar and members folder.
- Two-phase update — synchronous write-time index, asynchronous reindex for derived data.
- Per-node sidecars in `docs/index/<slug>.md` carrying the structured edges.

Many of these supersede later. The label-as-envelope concept dies during the redesign on the 25th. Sidecars get permanently dismissed. Tag-nodes collapse into tag-as-property. What survives: the graph-runtime framing, the orchestrator-skill role, the small navigation tool surface, the cost-asymmetry argument.

## Decisions captured

- MCP is the runtime, not the API. The skill body bootstraps the agent into the graph; everything else is tool calls against the graph. This is structurally different from the bash-replacement framing that started the day.
- Hello-world first. Wiring up the plugin manifest, the stdio transport, and the tool-registration handshake before anything substantive. A hello-world server that proves the loop closes is worth the small commitment.
- Architecture deserves its own note. The runtime thesis is large enough that it warrants a dedicated artifact. Embedding it in a commit message or a code comment would have lost it.

## Cross-references

- `[[notes/prototype-the-plugin-mcp-server-in-python]]` — the parent that framed Python over alternatives, with shape options A through D for the write path.
- `[[journal/2026-05-21-0403-injection-composition-pivot]]` — the inject-composition pivot, happening minutes after this commit. The two events collided in time but were independent cycles.

## Next

The thesis demands a concrete data-model. The session two days later drafts the spec and runs three cold-review iterations through it. See `[[journal/2026-05-23-1807-data-model-spec-and-cold-review-iteration]]`.
