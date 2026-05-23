# MCP graph runtime

The agent-facing spec for an MCP-backed knowledge graph runtime, split into stable contracts and swappable implementation.

## What this is

The MCP graph runtime is a knowledge-graph-backed knowledge base for agentic systems. Agents discover content through `match`, navigate via typed edges, invoke nodes under explicit framing contracts, and write back through transactional verbs. The graph compounds as the agent learns; the system maintains consistency the agent would otherwise have to remember.

This spec is organized as four contract files (stable, implementation-agnostic) and two implementation files (one per storage substrate). To swap storage backends, change the implementation file. Contracts stay put.

## Status of each file

- [data-model.md](data-model.md) — [Contract] Entity schemas. Stable. The data model the graph carries.
- [tool-api.md](tool-api.md) — [Contract] Tool signatures and semantics. Stable. Nine agent-facing tools.
- [behavior.md](behavior.md) — [Contract] Validation rules, envelope composition, label and edge vocabularies, error model. Stable.
- [orchestrator-skill.md](orchestrator-skill.md) — [Contract] The SKILL.md body the agent loads on first interaction. Stable.
- [implementation-file-based.md](implementation-file-based.md) — [Implementation, day-one] File-based storage. The shipping default.
- [implementation-alternatives.md](implementation-alternatives.md) — [Implementation, future] SQLite-for-relational hybrid, multi-writer support, write-ahead journaling, code-as-content.

## Contracts versus implementation

A contract describes what entities exist, what tools do, and how behavior composes — without naming files, formats, or I/O. An implementation maps the contracts onto a storage substrate. Day one uses files; a future pass may use SQLite for the relational layer with files for prose content.

The boundary is firm. Contract files name no file paths, no formats, no write flows. Implementation files reference contract entities and tools, then describe how each is realized.

## Navigation

Read in order on first pass:

1. [data-model.md](data-model.md) — entities the system thinks in
2. [tool-api.md](tool-api.md) — the API the agent calls
3. [behavior.md](behavior.md) — how it composes and validates
4. [orchestrator-skill.md](orchestrator-skill.md) — the protocol the agent follows
5. [implementation-file-based.md](implementation-file-based.md) — how the day-one shipping version maps onto disk
6. [implementation-alternatives.md](implementation-alternatives.md) — future implementation directions

## Cross-references

- `[[mcp-server-as-skill-system-runtime]]` — the parent design-exploration note. Records how this design emerged.
- `[[mcp-graph-runtime-data-model]]` — the legacy monolithic spec note, preserved for historical reference. This `docs/mcp/` folder is canonical.
- `[[source-files-as-graph-nodes]]` — future-scope analysis of indexing source code alongside markdown notes. Referenced from `implementation-alternatives.md`.
- `[[prototype-the-plugin-mcp-server-in-python]]` — the Python-as-language choice and shape options A through D for the write path.
