---
title: Hoplite spec index
summary: Index of the Hoplite spec corpus — architecture, tool API, roadmap.
tags: [hoplite, mcp, readme, index]
created: 2026-05-25
aliases: []
---

## What this is

Hoplite is an in-memory knowledge graph over a vault of markdown documents. The `.md` files under `docs/` are the only persistent state; the graph rebuilds from scratch at MCP server startup. Agents query through four tools — `hoplite_match_nodes`, `hoplite_traverse_nodes`, `hoplite_reindex`, `hoplite_dump_index` — and write document bodies through their own file tools. There is no CRUD surface on Hoplite itself.

This folder holds the architectural spec for the runtime. The repo README covers install and usage; the documents here cover the system internals.

## The corpus

- [architecture.md](architecture.md) — the system as it is. Corpus, frontmatter contract, graph entities (documents, properties, edges), wikilinks and ghosts, tag predicates, the walker, FTS5/BM25, MinHash, reindex semantics, dump schema, error model.
- [tool-api.md](tool-api.md) — the four agent-facing tools. Signatures, parameters, return types, idempotency hints, error-handling semantics at the MCP boundary.
- [roadmap.md](roadmap.md) — features deferred past day one. Embeddings, Sonnet-driven tag enrichment, file-watcher auto-reindex, MinHash LSH, persistent MinHash cache, multi-writer support, pagination, unified query DSL, columnar projection for multi-property predicates.

## Where else to look

- [`plugins/hoplite/components/hoplite/tool-reference.md`](../../plugins/hoplite/components/hoplite/tool-reference.md) — the agent-loaded tool reference component, injected into `taking-notes` and `journaling` so the authoring skills also know the query surface.
- [`plugins/hoplite/components/hoplite/frontmatter.md`](../../plugins/hoplite/components/hoplite/frontmatter.md) — the frontmatter contract component, injected into the same authoring skills.
- [`plugins/hoplite/mcp/`](../../plugins/hoplite/mcp/) — server source. The implementation is the canonical reference for any behavior the spec doesn't cover.
