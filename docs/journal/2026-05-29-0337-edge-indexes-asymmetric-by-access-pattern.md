---
title: Edge indexes are asymmetric by access pattern
summary: The SQLite edge traversal indexes lead with different columns by direction — kind-leading forward for by-kind enumeration, dst-leading reverse for backtrack — because seeking by kind-alone and by node-alone need different leading columns. A symmetric anchor-leading pair was tried and reverted; EXPLAIN QUERY PLAN confirms every access pattern seeks.
document.tags: [journal, hoplite, sqlite, schema, decision]
document.created: 2026-05-29
---

# Edge indexes are asymmetric by access pattern

The SQLite edge traversal indexes lead with different columns by direction, because seeking by kind-alone and by node-alone need different leading columns and no single index serves both.

## Context

The graph is SQLite-only, traversal runs as a recursive CTE over `edge` ([[docs/notes/graph-py-design.md]]). So every CTE hop has to be an indexed seek, never a scan. The open question was which edge indexes make all the traversal shapes seek — forward and reverse, any-kind and kind-filtered — plus global "all edges of kind K" enumeration.

## Decision

Two purpose-built indexes, asymmetric on purpose:

- `idx_edge_kind_src (kind, src, dst, confidence)` — kind-leading. Serves global by-kind enumeration (the related-edge pass needs every `mentions` pair) and forward kind-filtered traversal.
- `idx_edge_dst (dst, kind, src, confidence)` — dst-leading. The reverse / "backtrack" index, a covering seek for both any-kind (`dst` alone) and kind-filtered (`dst, kind`) reverse walks.

Forward any-kind rides the `UNIQUE(src, dst)` auto-index. The `id` rowid rides every index for free, so a walk reads each edge's `edge_property` join key without a heap touch.

## Dead end

[Dead end] First reordered both indexes to anchor-leading — `src`-first and `dst`-first — for symmetry. That broke `WHERE kind = ?` enumeration to a full `SCAN edge`, because anchor-leading drops the kind-alone seek. Reverted the forward index to kind-leading. The asymmetry is the design; the symmetric pair was the regression. Seeking by kind-alone (forward enumeration) and by dst-alone (reverse backtrack) genuinely want different leading columns.

## Outcome

[Observation] Verified, not assumed. `EXPLAIN QUERY PLAN` reports all five access patterns — forward any-kind, forward kind-filtered, reverse any-kind, reverse kind-filtered, global by-kind — as `SEARCH` (seek), none as `SCAN`. Four are `COVERING`.
