# Hoplite — MCP graph runtime

The agent-facing spec for `hoplite_mcp`, an MCP-backed knowledge graph runtime over a vault of markdown notes. Hoplite is the index; agents read content through their own file tools.

## What this is

Hoplite is Obsidian for agents. The vault is a directory of `.md` files with YAML frontmatter — fully Obsidian-compatible. Hoplite builds an in-memory graph from that vault at MCP server startup, exposing four query tools so agents can discover documents, traverse the graph, refresh after writing, and dump state for SQL debugging. Content reads happen through the agent's built-in `Read` tool; writes happen through `Write` and `Edit`. There is no CRUD surface on Hoplite itself.

The corpus of `.md` files is the only persistent state in the system. Everything else — edges, MinHash signatures, the FTS5 text index, alias and casefold lookup tables — is derived at startup and held in RAM.

## Status of each file

- [data-model.md](data-model.md) — [Contract] Entities the graph carries: Document, Tag, Edge, and the result types Hit, TraversalHit, WriteResult.
- [tool-api.md](tool-api.md) — [Contract] Tool signatures and semantics. Four agent-facing tools: `match_nodes`, `traverse_nodes`, `reindex`, `dump_index`.
- [behavior.md](behavior.md) — [Contract] Frontmatter shape, wikilink resolution, tag predicates, edge derivation, reindex semantics, error model.
- [hoplite-skill.md](hoplite-skill.md) — [Contract] The SKILL.md body for the `/hoplite` skill — the protocol the agent follows when working with the vault.
- [implementation.md](implementation.md) — [Implementation] How the contracts map onto an in-memory graph with a disposable in-memory SQLite FTS5 index. Includes the two-pass walker, MinHash details, ghost-promotion semantics, and the `hoplite_dump_index` SQL schema.
- [implementation-plan.md](implementation-plan.md) — [Plan] Day-one delivery sequence — four phases from scaffolding rewrite through Graph + walker, ending in end-to-end smoke.
- [decision-log.md](decision-log.md) — [Log] Chronological record of design decisions from the long pivot session that produced the current shape. Canonical source for "what was decided and why."
- [refactor-ids-and-metadata.md](refactor-ids-and-metadata.md) — [Superseded] Intermediate-pivot snapshot. See [decision-log.md](decision-log.md) for the current state.
- [roadmap.md](roadmap.md) — [Roadmap] Embeddings, Sonnet-driven tag enrichment, file-watcher auto-reindex, MinHash LSH, persistent MinHash cache, multi-writer support, pagination, unified query DSL, legacy-corpus migration.

## Contracts versus implementation

A contract describes what entities exist, what tools do, and how behavior composes — without naming storage, formats, or I/O. The implementation maps the contracts onto a runtime shape. Day one uses an in-memory graph with disposable SQLite for text scoring; the contract layer holds across any future implementation changes (a persistent MinHash cache, a watchdog file-watcher, embeddings via Ollama — all swap into the implementation layer without touching the contracts).

## Navigation

Read in order on first pass:

1. [decision-log.md](decision-log.md) — what's locked in and why (orienting context for the rest)
2. [data-model.md](data-model.md) — entities the system thinks in
3. [tool-api.md](tool-api.md) — the API the agent calls
4. [behavior.md](behavior.md) — how it composes and validates
5. [hoplite-skill.md](hoplite-skill.md) — the protocol the agent follows
6. [implementation.md](implementation.md) — how the day-one shipping version is built
7. [roadmap.md](roadmap.md) — what comes later

## Cross-references

- `[[mcp-server-as-skill-system-runtime]]` — the parent design-exploration note. Records how this design emerged.
- `[[mcp-graph-runtime-data-model]]` — the legacy monolithic spec note, preserved for historical reference. This `docs/mcp/` folder is canonical.
- `[[prototype-the-plugin-mcp-server-in-python]]` — the Python-as-language choice and shape options A through D for the write path.
