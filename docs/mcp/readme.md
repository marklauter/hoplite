# MCP graph runtime

The agent-facing spec for an MCP-backed knowledge graph runtime, split into stable contracts and the day-one implementation.

## What this is

The MCP graph runtime is a knowledge-graph-backed knowledge base for agentic systems. Agents discover content through `match`, navigate via typed edges, invoke nodes under explicit framing contracts, and write back through transactional verbs. The graph compounds as the agent learns; the system maintains consistency the agent would otherwise have to remember.

This spec is organized as four contract files (stable, implementation-agnostic), one implementation file (the day-one SQLite-hybrid build target), and one roadmap file (deferred features). Contracts stay put across implementation changes.

## Status of each file

- [data-model.md](data-model.md) — [Contract] Entity schemas. The data model the graph carries.
- [tool-api.md](tool-api.md) — [Contract] Tool signatures and semantics. Nine agent-facing tools.
- [behavior.md](behavior.md) — [Contract] Validation rules, envelope composition, label and edge vocabularies, error model.
- [orchestrator-skill.md](orchestrator-skill.md) — [Contract] The SKILL.md body the agent loads on first interaction.
- [implementation-sqlite-hybrid.md](implementation-sqlite-hybrid.md) — [Implementation] SQLite for the relational layer (`docs/index/graph.db` with FTS5), files for the prose layer (notes, label envelopes, embedding blobs).
- [deferred-features.md](deferred-features.md) — [Roadmap] Multi-writer support, source files as graph nodes, external web references as first-class nodes, reindex trigger model.

## Contracts versus implementation

A contract describes what entities exist, what tools do, and how behavior composes — without naming storage, formats, or I/O. The implementation maps the contracts onto a storage substrate. Day one uses SQLite for relational data and files for prose; the layered split means the contracts hold across any future implementation changes.

## Navigation

Read in order on first pass:

1. [data-model.md](data-model.md) — entities the system thinks in
2. [tool-api.md](tool-api.md) — the API the agent calls
3. [behavior.md](behavior.md) — how it composes and validates
4. [orchestrator-skill.md](orchestrator-skill.md) — the protocol the agent follows
5. [implementation-sqlite-hybrid.md](implementation-sqlite-hybrid.md) — how the day-one shipping version maps onto SQLite + files
6. [deferred-features.md](deferred-features.md) — what comes later

## Cross-references

- `[[mcp-server-as-skill-system-runtime]]` — the parent design-exploration note. Records how this design emerged.
- `[[mcp-graph-runtime-data-model]]` — the legacy monolithic spec note, preserved for historical reference. This `docs/mcp/` folder is canonical.
- `[[source-files-as-graph-nodes]]` — future-scope analysis of indexing source code alongside markdown notes. Referenced from `deferred-features.md`.
- `[[prototype-the-plugin-mcp-server-in-python]]` — the Python-as-language choice and shape options A through D for the write path.
