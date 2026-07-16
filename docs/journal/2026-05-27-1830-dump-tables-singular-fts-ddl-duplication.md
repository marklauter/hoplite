---
title: Dump tables go singular; FTS DDL remains the lone duplication
summary: Renamed the four dump tables from plural to singular to remove the join-table awkwardness, and surfaced that the FTS5 schema is the only DDL still duplicated between dump and in-memory.
tags: [journal, schema, naming, decision]
created: 2026-05-27
---

# Dump tables go singular; FTS DDL remains the lone duplication

Renamed the four dump tables from plural to singular to remove the join-table awkwardness, and surfaced that the FTS5 schema is the only DDL still duplicated between dump and in-memory.

## Context

Going in, the dump schema in [[docs/specs/hoplite-architecture.md]] carried `documents`, `document_properties`, `edges`, `edge_properties`. The drive for the rename was join-table consistency: the entity tables were plural while the join tables read naturally as singular-of-the-thing-they-annotate (`document_property` is the property of a document; `edge_property` is the property of an edge). `edge_properties.kind REFERENCES edges(kind)` reads as the property-of-many-edges rather than the property-of-an-edge — the mismatch was right in the foreign keys. Aligning every table on the row-name-singular convention (one row = one document) makes the entity tables and their join tables speak the same grammar.

## Decision

Renamed all four (observation: the indexes referencing the old plural names got renamed for consistency too — `idx_edges_src` → `idx_edge_src`, `idx_doc_props_key_value` → `idx_document_property_key_value`):

- `documents` → `document`
- `document_properties` → `document_property`
- `edges` → `edge`
- `edge_properties` → `edge_property`

Left untouched on purpose:

- `Graph.documents`, `Graph.document_properties`, `Graph.out_edges`, `Graph.edge_properties` — Python dict attributes. A dict-of-documents is naturally plural in Python; renaming to singular would read worse, not better. The SQL-shape constraint doesn't reach into the in-memory shape.
- `WriteResult.counts` JSON keys (`documents`, `ghosts`, `edges`) — those are entity counts, not table names; the wire format is a separate decision.
- Journal entries containing the old DDL — historical record.

## Source-of-truth observation

Going in, the user also asked whether the dump and in-memory share a single DDL source. Observation: partial.

- The persistence tables (`document`, `document_property`, `edge`, `edge_property`) have one source — the `DUMP_SCHEMA` constant in `plugins/hoplite/mcp/src/hoplite/graph.py`. The in-memory equivalent isn't SQL at all; it's the dict fields on the `Graph` dataclass. No DDL duplication to drift.
- The FTS5 virtual table *is* declared in two places: once inside `DUMP_SCHEMA` and once inline in `_setup_fts()` against the `:memory:` connection. The two are textually distinct but semantically identical today. That's the one drift risk in the file — the dump's FTS shape and the live FTS shape could fall out of sync if one is edited and the other isn't.

## Next

Factor an `FTS_DDL` constant (or extract the FTS statement out of `DUMP_SCHEMA` and reuse it in both `executescript(DUMP_SCHEMA + FTS_DDL)` and `_setup_fts`) so the FTS schema has the same single-source guarantee the persistence tables now enjoy. Deferred — small, mechanical, worth waiting until the FTS shape needs to change for a reason of its own.
