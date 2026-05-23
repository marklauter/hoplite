# MCP graph runtime

The agent-facing spec for an MCP-backed knowledge graph runtime, split into stable contracts and swappable implementation.

## What this is

The MCP graph runtime is a knowledge-graph-backed knowledge base for agentic systems. Agents discover content through `match`, navigate via typed edges, invoke nodes under explicit framing contracts, and write back through transactional verbs. The graph compounds as the agent learns; the system maintains consistency the agent would otherwise have to remember.

This spec is organized as four contract files (stable, implementation-agnostic) plus two peer implementation files (one per storage substrate — file-based or SQLite-hybrid) and one overlay file (extensions that layer on either substrate). To swap storage backends, change which implementation file is active. Contracts stay put.

## Status of each file

- [data-model.md](data-model.md) — [Contract] Entity schemas. Stable. The data model the graph carries.
- [tool-api.md](tool-api.md) — [Contract] Tool signatures and semantics. Stable. Nine agent-facing tools.
- [behavior.md](behavior.md) — [Contract] Validation rules, envelope composition, label and edge vocabularies, error model. Stable.
- [orchestrator-skill.md](orchestrator-skill.md) — [Contract] The SKILL.md body the agent loads on first interaction. Stable.
- [implementation-file-based.md](implementation-file-based.md) — [Implementation, option A] File-based storage. Notes, sidecars, label envelopes, membership markers all on disk. Greppable, hand-editable, git-friendly.
- [implementation-sqlite-hybrid.md](implementation-sqlite-hybrid.md) — [Implementation, option B] SQLite for the relational layer, files for the prose layer. Notes and envelopes stay as markdown; sidecars, memberships, edges, and FTS5 search live in one SQLite database.
- [implementation-alternatives.md](implementation-alternatives.md) — [Implementation, future] Multi-writer support, write-ahead journaling, code-as-content, embeddings via Ollama. Apply on top of either implementation A or B.

## Contracts versus implementation

A contract describes what entities exist, what tools do, and how behavior composes — without naming files, formats, or I/O. An implementation maps the contracts onto a storage substrate. Day one uses files; a future pass may use SQLite for the relational layer with files for prose content.

The boundary is firm. Contract files name no file paths, no formats, no write flows. Implementation files reference contract entities and tools, then describe how each is realized.

## Navigation

Read in order on first pass:

1. [data-model.md](data-model.md) — entities the system thinks in
2. [tool-api.md](tool-api.md) — the API the agent calls
3. [behavior.md](behavior.md) — how it composes and validates
4. [orchestrator-skill.md](orchestrator-skill.md) — the protocol the agent follows
5. [implementation-file-based.md](implementation-file-based.md) — option A: file-based mapping
6. [implementation-sqlite-hybrid.md](implementation-sqlite-hybrid.md) — option B: SQLite for relational layer, files for prose
7. [implementation-alternatives.md](implementation-alternatives.md) — overlay extensions (multi-writer, embeddings, code-as-content)

## Cross-references

- `[[mcp-server-as-skill-system-runtime]]` — the parent design-exploration note. Records how this design emerged.
- `[[mcp-graph-runtime-data-model]]` — the legacy monolithic spec note, preserved for historical reference. This `docs/mcp/` folder is canonical.
- `[[source-files-as-graph-nodes]]` — future-scope analysis of indexing source code alongside markdown notes. Referenced from `implementation-alternatives.md`.
- `[[prototype-the-plugin-mcp-server-in-python]]` — the Python-as-language choice and shape options A through D for the write path.
