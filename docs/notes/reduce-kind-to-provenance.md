---
title: Reduce kind to provenance
summary: "`kind` exists only to express an edge's provenance — it is redundant with the locked `provenance` term and should be collapsed into it, across the glossary, schema.sql, and the Python loader. Also fixes the `asserted`→`declared` value drift the assert-genus lock introduced."
tags: [note, todo, hoplite, glossary]
created: 2026-06-20
document.status: evolving
---

# Reduce kind to provenance

`kind` (glossary: *"an edge's provenance, asserted or inferred"*) carries no meaning beyond provenance applied to an edge. An edge **is** a feature (a declared edge is the neighborhood dimension's asserted feature), so an edge's origin is just its `provenance` — the term already locked at `docs/hoplite/glossary:provenance`. `kind` is a redundant name for it. Collapse `kind` (and its closed-enum partner `edge_kind`) into `provenance`.

This is the edge-anatomy tail of the provenance rework started in [[provenance-is-a-tree-fact-versus-claim-split-by-assertion]].

## Two changes, coupled

1. **Rename the concept `kind` → `provenance`.** Retire `kind` and `edge_kind` into `provenance` (the existing locked term). The one fact they add — *an edge is always a claim, never intrinsic, so its provenance is `declared` or `inferred`* — folds into `provenance` as an **Also** note (the 2-value claim subset of provenance's 3 values).
2. **Fix the `asserted`→`declared` value drift.** `kind`/`edge_kind`/`schema.sql` seed the two values as `asserted, inferred`. Under the locked `assert` genus, *asserted* is the genus covering **both** (author **declares**, engine **infers**), so it cannot be one of two sibling values. The author-edge value must be **`declared`**, not `asserted`. End state: the two claim-provenances are `declared`, `inferred`.

## Blast radius

Not just schema.sql — a table/column rename cascades into the loader and query code. Sites found (`plugins/hoplite/mcp/src/hoplite/`):

- **`schema.sql`** — `edge_kind` table (→ `provenance`), its `kind` column, the `edge.kind` FK column, index `idx_edge_kind_src`, the seed `insert ... values (1, 'asserted'), (2, 'inferred')` (→ `'declared'`, `'inferred'`), the `namespace` view branch `'edge/kind/' || kind`, and ~15 explanatory comments using "kind".
- **`tools.py`** — `edge.kind` reads in the traversal filter (`if edge_types and edge.kind not in edge_types`, `_ALWAYS_FOLLOW` check).
- **`row_factories.py`** — `kind=row["kind"]` edge row mapping.
- **`models.py`** — `Edge.kind: str` field (plus its docstring naming `mentions`/`cites`/`related` — note that conflates stereotype values with provenance; review while here).
- **`migrations.py`** — `_EXPECTED_TABLES` includes `"edge_kind"` (→ `"provenance"`).

`wikilinks.py` line 14 mentions `(src, dst, kind)` in a comment only.

## Naming decisions to settle when executing

- **Table name:** `provenance` (unprefixed, matching the `tag`/`stereotype` vocab-table pattern; `edge_kind`'s `edge_` prefix is the inconsistent one).
- **Column name:** the vocab tables split — `tag`/`stereotype` use `label`, `property_key` uses `key`. Pick `label` for consistency with the label-set tables, or `provenance` to echo the concept.
- **`models.py` docstring** wrongly lists `mentions`/`cites`/`related` (those are stereotypes) as `kind` values — fix the example to `declared`/`inferred` when renaming.

## Glossary side (smaller, can go first)

- Retire `kind.md` and `edge_kind.md` into `provenance` (`document.retired: [kind, edge_kind]`, `aliases: [kind, edge_kind]` so links resolve).
- Fold the closed-enum / never-intrinsic fact into `provenance` as an Also note.
- `stereotype.md` currently carries `contrast::docs/hoplite/glossary:kind` — re-point that reciprocal to `provenance` (the `kind`↔`stereotype` contrast becomes `provenance`↔`stereotype`: provenance is the edge's origin, stereotype its meaning).
