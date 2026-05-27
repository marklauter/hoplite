---
title: Hoplite spec index
summary: Index of the Hoplite spec corpus — architecture, tool API, roadmap.
tags: [hoplite, mcp, readme, index]
created: 2026-05-25
---

## What this is

Hoplite is an in-memory knowledge graph over a corpus of markdown documents. The `.md` files under `docs/` are the only persistent state; the graph rebuilds from scratch at MCP server startup. Agents query through four tools — `where`, `relatives`, `refresh`, `export` — and write document bodies through their own file tools. There is no CRUD surface on Hoplite itself.

This folder holds the architectural spec for the runtime. The repo README covers install and usage; the documents here cover the system internals.

## The corpus

- [[hoplite/architecture|architecture.md]] — the system as it is. Corpus, frontmatter contract, graph entities (documents, properties, edges), wikilinks and ghosts, tag predicates, the walker, FTS5/BM25, MinHash, reindex semantics, dump schema, error model.
- [[hoplite/tool-api|tool-api.md]] — the four agent-facing tools. Signatures, parameters, return types, idempotency hints, error-handling semantics at the MCP boundary.
- [[hoplite/roadmap|roadmap.md]] — features deferred past day one. Embeddings, Sonnet-driven tag enrichment, file-watcher auto-reindex, MinHash LSH, persistent MinHash cache, multi-writer support, pagination, unified query DSL, columnar projection for multi-property predicates.

## Where else to look

- [`plugins/hoplite/components/hoplite/mcp-reference.md`](../../plugins/hoplite/components/hoplite/mcp-reference.md) — the agent-loaded tool reference component, injected into `taking-notes` and `journaling` so the authoring skills also know the query surface.
- [`plugins/hoplite/components/shape/frontmatter.md`](../../plugins/hoplite/components/shape/frontmatter.md) — the frontmatter contract component, injected into the same authoring skills.
- [`plugins/hoplite/components/shape/artifact-structure.md`](../../plugins/hoplite/components/shape/artifact-structure.md) — document composition and template, injected into the same authoring skills.
- [`plugins/hoplite/components/prose/writing-prose.md`](../../plugins/hoplite/components/prose/writing-prose.md) — title/summary/body virtues, composition, grammar, validation; injected into the same authoring skills.
- [`plugins/hoplite/mcp/`](../../plugins/hoplite/mcp/) — server source. The implementation is the canonical reference for any behavior the spec doesn't cover.
