---
title: URIs are a tool-layer projection over relational storage
summary: The normalized SQLite schema stays the model-of-record; uris and namespaces live only at the tool boundary. Tools parse an inbound uri into a relational query and project outbound rows back into uris. Records why a DynamoDB-style single-table key-value design was rejected — the uri address space is a projection, not a storage mandate.
tags: [note, hoplite, architecture, decision]
created: 2026-06-05
---

# URIs are a tool-layer projection over relational storage

The uri is the interface contract at the tool boundary. Storage stays relational; the tools translate between the two registers.

## The boundary

[Decision] Two registers, one translation layer between them.

- Outside, at the tool layer — everything is a uri: `node/docs/foo.md`, `node/property/status`, `node/tag/note`, `edge/stereotype/cites`, `edge(src, dst)`. This is what an agent reads, filters on, and walks.
- Inside — the normalized schema: `node`, `node_property` + `property_key`, `node_tag` + `tag`, `edge` + `edge_stereotype` + `stereotype`. The model, explicit and self-documenting.
- The tools are the seam. Inbound, a tool decomposes a uri into a relational query: `node/property/status` seeks `where keyid = …`; `edge/stereotype/cites` resolves a stereotype filter; `node/docs/foo.md` resolves a node by uri. Outbound, a tool projects rows back into uris — the `namespace` view is the surveyable half of that projection.

[Observation] The storage already works this way. The only stored uri is `node.uri`; every namespace path (`node/property/<key>`, `edge/stereotype/<label>`) is projected by a view or built in the loader, never stored as a key. The address space is a projection over relational tables, so the "everything is a uri" coherence is already captured without the storage being key-shaped.

## Why not a key-value single-table design

[Inference] The uri address space is pk/sk-shaped, which tempts a DynamoDB-style single-table store — `item(pk, sk, data)` with each access pattern written at index time (write amplification). Drop-and-recreate even removes amplification's usual cost: there are no updates to reconcile, only full rebuilds. The synergy is real, but the move loses more than it buys:

- [Inference] Single-table design is a workaround for constraints SQLite does not have. It exists because DynamoDB has no joins and bills per request across a network, so every access pattern is pre-baked into one partition. SQLite joins are free, in-process, and planner-optimized — porting the discipline imports its tax (rigid pre-enumerated patterns, amplified writes, model hidden in keys) to solve a problem that is absent here.
- [Inference] The relational schema is the model canon. Collapsing to `item(pk, sk, data)` moves the model out of the DDL and into key-string conventions plus loader code; `schema.sql` stops describing the model. For a documentation-first design that is a regression.
- [Observation] The reads that matter stay relational regardless: full-text search is an `fts5` virtual table, and graph traversal is a recursive CTE — so the store is never actually single-table, and the things key-value would optimize are non-problems.
- [Inference] The access patterns are still in flux (survey, match, walk are half-specified), so baking them into amplified items now is premature.

[Decision] Keep relational storage as the model-of-record; keep uris as the tool-layer projection. If access patterns later stabilize and reads get hot, a key-value read-projection can be materialized at rebuild time as a layer on top — but it stays a derived optimization, never the source of truth.

## See also

- [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]] — the uri address space and the namespaced-form-is-the-addressing-register decision this extends.
- [[docs/hoplite/hoplite-graph.md]] — the relational model of record.
