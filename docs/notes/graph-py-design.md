---
title: graph.py — the SQLite-backed Graph
summary: "`graph.py` defines `Graph`, the one and only graph implementation. It is a thin class over an injected `Database`: every method opens a connection per call, runs SQL against the `node`/`edge`/`edge_kind`/`fts` schema, projects rows through `row_factories.py`, and returns the domain dataclasses. There is no Protocol and no in-memory peer — SQLite is the only store. Traversal is a recursive CTE over the `edge` table."
tags: [note, sqlite, design, graph]
created: 2026-05-28
status: design
---

# graph.py — the SQLite-backed Graph

`graph.py` defines `Graph`, the one and only graph implementation. It is a thin class over an injected `Database`: each method opens a connection per call (`open_ro` for queries, `open_rw` for `refresh`/`export`), runs SQL against the `node`/`edge`/`edge_kind`/`fts` schema in [schema.sql](../../plugins/hoplite/mcp/src/hoplite/schema.sql), projects rows through `row_factories.py`, and returns the domain dataclasses. There is no `Graph` Protocol and no in-memory peer. The in-memory dict-backed graph is retired, and SQLite is the only store.

Sibling design notes: [[docs/todos/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale; [[docs/todos/db-refactor.md]] for the broader plan; [[docs/notes/db-py-design.md]] (the `Database` this depends on), [[docs/notes/migrations-py-design.md]] (the schema this queries), [[docs/notes/row-factories-py-design.md]] (the projection layer this composes with), and [[docs/notes/walker-py-design.md]] (the writer behind `refresh`). This note covers `graph.py` alone.

## What replaces the old `graph.py`

Today's `graph.py` is the in-memory container: dicts for `documents`/`out_edges`/`in_edges`/`aliases`, a `:memory:` FTS connection, the `walk` free function, and the `dump_index` writer. The query logic (`search`/`traverse`/BFS) lives in `tools.py` and reaches into those dicts.


The new `graph.py` is a single class with no in-memory state:

- **No adjacency dicts, no aliases map, no `:memory:` FTS connection.** Every lookup is a SQL query against the file-backed DB.
- **The query logic moves onto the class.** The `match_nodes`/`traverse_nodes`/`_neighbors`/`_escape_fts5_query` bodies from `tools.py` become `Graph.search`/`Graph.traverse` and private helpers here.
- **`walk` moves to its own module** (`walker.py`, see [[docs/notes/walker-py-design.md]]), and `refresh()` calls it. The old `dump_index` writers are replaced by `export()`, which uses `sqlite3`'s online-backup API.

## Schema and vocabulary note

The SQL below targets the *current* `schema.sql`: `node(id, uri, resolved, content_hash, minhash)`, `node_property(id, key, value)`, `edge(id, src, dst, kind, confidence)` where `kind` is an integer FK into `edge_kind(id, kind)`, `edge_property`, and the `fts(uri, title, summary, body)` virtual table. `node.uri`, `node_property.key`, and `edge_kind.kind` carry `COLLATE NOCASE`.

The landed `models.py` and `row_factories.py` still use the older `Document`/`path` vocabulary. The queries here project `n.uri AS path` so the existing factories keep working unchanged. The `node`/`uri` ↔ `Document`/`path` drift between `schema.sql` and `models.py` is a known reconcile item tracked in [[docs/todos/db-refactor.md]]. It is not resolved in this note.

Case-insensitivity is the column's job now. `node.uri COLLATE NOCASE` means `WHERE uri = ?` already matches case-insensitively. The old "walker casefolds paths before insert, resolver casefolds the input" contract is deleted; there is no casefold-on-store anywhere. The walker stores URIs verbatim, and matching is the collation's responsibility.

## Class shape

```python
class Graph:
    def __init__(self, db: Database, corpus_root: Path) -> None:
        self._db = db
        self._corpus_root = corpus_root
```

Two fields: the injected `Database` and the corpus root (load-bearing only for `refresh()`, which dispatches to the walker). There is no connection caching; every method bounds its connection lifetime to a single `with self._db.open_*()` block.

```python
import sqlite3
from pathlib import Path
from typing import Literal

from hoplite import migrations, row_factories, walker
from hoplite.db import Database, write_transaction
from hoplite.filtering import TagExpression  # parsed predicate AST; callable on a tag set
from hoplite.models import Hit, TraversalHit, WriteResult


class Graph:
    def __init__(self, db: Database, corpus_root: Path) -> None:
        self._db = db
        self._corpus_root = corpus_root

    def search(self, text: str | None, tag_ast: TagExpression | None, limit: int) -> list[Hit]: ...
    def traverse(
        self,
        from_: str,
        *,
        edge_types: set[str],
        direction: Literal["out", "in", "both"],
        top_k_related: int | None,
        tag_ast: TagExpression | None,
        depth: int,
    ) -> list[TraversalHit]: ...
    def refresh(self) -> WriteResult: ...
    def export(self, path: Path) -> WriteResult: ...
    # private: _fts_candidates, _tags_for_paths, _resolve_uri, _traverse_cte, _count_rows
```

The four public methods take split scalars, never the Pydantic `MatchPredicate`/`TraversePredicate` from `tools.py`. `tools.py` parses the tag expression at the handler boundary (`parser.parse_predicate`) and passes the `TagExpression` AST (a callable on a tag set, from `hoplite.filtering`) as a primitive. This keeps `graph.py` free of any upward dependency on `tools.py`, so there is no import cycle.

## `search(text, tag_ast, limit) -> list[Hit]`

Backs the `where` tool. `text` is the BM25 query (`None` for tag-only search); `tag_ast` is the parsed tag predicate (`None` for text-only). Returns up to `limit` documents ranked by BM25 and narrowed by the tag predicate.

Open an ro connection, build the FTS candidate set, apply the tag predicate in Python, then truncate to `limit`.

```python
def search(self, text, tag_ast, limit):
    with self._db.open_ro() as conn:
        candidates = self._fts_candidates(conn, text)   # full matched set; no over-fetch
        if tag_ast is None:
            return candidates[:limit]
        tags_by_path = self._tags_for_paths(conn, [hit.path for hit in candidates])
        survivors = [h for h in candidates if tag_ast(frozenset(tags_by_path.get(h.path, ())))]
        return survivors[:limit]
```

The candidate query feeds `row_to_hit` (see [[docs/notes/row-factories-py-design.md]]):

```sql
SELECT n.uri AS path,
       fts.summary,
       (SELECT json_group_array(value) FROM (
          SELECT value FROM node_property
          WHERE id = n.id AND key = 'tags'
        )) AS tags,
       bm25(fts) AS score
FROM fts
JOIN node n ON n.id = fts.rowid
WHERE fts MATCH ?
ORDER BY score
LIMIT ?
```

When `text` is `None`, there is no FTS row to match. The tag-only branch then selects every node (`SELECT n.uri AS path, ... FROM node n`) at score 0, so ghost and URL nodes are discoverable. Those nodes never have FTS rows but carry synthetic `ghost`/`url` tags.

No over-fetch. When a tag predicate is present, the FTS query fetches the full matched set (no `limit * N` shortcut), Python filters, then truncates to `limit`. The tag predicate is evaluated in Python, not compiled to SQL. The grammar (`!`, `&`, `|`, parens) is small enough to run in microseconds per candidate, and arbitrary boolean composition is messy as `EXISTS` clauses. If profiling on large corpora shows the full fetch dominates, the fix is to push the predicate into SQL, not to over-fetch.

The FTS query string is escaped by `_escape_fts5_query` (moved here from `tools.py`, which was the only caller). Each whitespace token is wrapped in double quotes (internal quotes doubled), which neutralizes FTS5 special chars while preserving the implicit-AND-across-terms semantics.

## `traverse(...) -> list[TraversalHit]`

Backs the `relatives` tool. A breadth-first walk from `from_`, with one `TraversalHit` per node reached at distance 1..depth (origin excluded), ordered `(distance, path)` ascending, optionally tag-filtered.

```python
def traverse(self, from_, *, edge_types, direction, top_k_related, tag_ast, depth):
    with self._db.open_ro() as conn:
        origin_id = self._resolve_uri(conn, from_)
        if origin_id is None:
            raise ValueError(f"unknown starting document: {from_!r}")
        rows = self._traverse_cte(conn, origin_id, edge_types, direction, top_k_related, depth)
        hits = [self._project_traversal_hit(conn, r) for r in rows]
        if tag_ast is not None:
            hits = [h for h in hits if tag_ast(frozenset(h.tags))]
        hits.sort(key=lambda h: (h.distance, h.path))
        return hits
```

### Traversal is a recursive CTE

The walk runs in SQL as a recursive CTE over `edge`, not as a Python `deque` loop. The CTE handles depth-bounding, cycle-safety, edge-kind filtering, direction, the `top_k_related` cap, and shortest-distance-per-node in one query.

The hard part: SQLite forbids aggregates and window functions in the recursive term, so the `top_k_related` ranking and the shortest-distance dedupe are done in the non-recursive CTEs that feed and consume the recursion. The recursive term only walks and accumulates.

```sql
WITH RECURSIVE
-- 1. Normalize direction into a (from_id, to_id) step relation, carrying the
--    edge's id, kind string (joined out of edge_kind), and confidence.
--    'out'  -> (src -> dst);  'in' -> (dst -> src);  'both' -> UNION of the two.
step(from_id, to_id, edge_id, kind, confidence) AS (
  SELECT e.src, e.dst, e.id, k.kind, e.confidence
  FROM edge e JOIN edge_kind k ON k.id = e.kind
  -- WHERE k.kind IN (<edge_types>)   -- omitted when edge_types is empty (follow all)
  -- the 'in' direction adds a symmetric UNION ALL selecting e.dst, e.src, ...
),
-- 2. Rank 'related' edges per source node; the window function is legal here
--    (non-recursive). Authored kinds (mentions/cites) are always followable.
ranked_related AS (
  SELECT s.from_id, s.to_id, s.edge_id, s.confidence,
         ROW_NUMBER() OVER (PARTITION BY s.from_id
                            ORDER BY s.confidence DESC, dn.uri ASC) AS rn
  FROM step s JOIN node dn ON dn.id = s.to_id
  WHERE s.kind = 'related'
),
followable(from_id, to_id, edge_id, confidence) AS (
  SELECT from_id, to_id, edge_id, confidence FROM step WHERE kind IN ('mentions', 'cites')
  UNION ALL
  SELECT from_id, to_id, edge_id, confidence FROM ranked_related
  WHERE :top_k IS NULL OR rn <= :top_k
),
-- 3. The walk. Carry a node-id breadcrumb for the cycle guard and a JSON array
--    of edge ids for via_edges reconstruction.
walk(id, distance, trail, via) AS (
  SELECT :origin, 0, '/' || :origin || '/', json_array()
  UNION ALL
  SELECT f.to_id,
         w.distance + 1,
         w.trail || f.to_id || '/',
         json_insert(w.via, '$[#]', f.edge_id)
  FROM walk w
  JOIN followable f ON f.from_id = w.id
  WHERE w.distance < :depth
    AND instr(w.trail, '/' || f.to_id || '/') = 0          -- cycle guard
)
-- 4. Keep the shortest path to each node (excluding origin).
SELECT id, distance, via
FROM (
  SELECT id, distance, via,
         ROW_NUMBER() OVER (PARTITION BY id ORDER BY distance, trail) AS rn
  FROM walk
  WHERE id != :origin
)
WHERE rn = 1
```

Notes on the CTE:

- **`top_k_related` semantics match the old `_neighbors`:** rank a node's outgoing `related` edges by `(confidence DESC, target_uri ASC)` and keep the top K. The cap is per-source-node and independent of the path taken to reach that node, same as before.
- **`edge_types` filtering** restricts the `step` relation up front (`WHERE k.kind IN (...)`); an empty set means follow all kinds.
- **Cycle guard** is the `instr` check against the `/id/`-delimited breadcrumb. The shortest-path dedupe (`ROW_NUMBER ... ORDER BY distance, trail`) picks one row per reached node.
- **`via` is a JSON array of `edge.id` values** along the chosen path. Python expands those ids back into `Edge` objects (one batched `SELECT ... WHERE e.id IN (...)` joined to `node` twice for `src_path`/`dst_path`, projected through `row_to_edge`) and passes the list to `row_to_traversal_hit(row, via_edges)`.
- **Direction `in`/`both`** flips or UNIONs the `step` relation; everything downstream is identical.

This is more SQL than the old Python BFS, and the trade is deliberate: the walk, the cap, and the shortest-path selection happen in one round-trip instead of one `SELECT` per depth level. If the CTE ever proves slower than a Python loop at realistic depths (1–3), it can be swapped behind `traverse` without changing the public surface. The default is the CTE, per [[docs/todos/db-refactor.md]].

### Per-node projection

Each reached node is projected to a `TraversalHit` via the same shape `row_to_traversal_hit` expects: `path`, `summary`, `tags` (as `json_group_array`), and `distance` bound as a literal column, with `via_edges` assembled from the CTE's `via` array:

```sql
SELECT n.uri AS path,
       fts.summary,
       (SELECT json_group_array(value) FROM (
          SELECT value FROM node_property WHERE id = n.id AND key = 'tags'
        )) AS tags,
       ? AS distance
FROM node n
LEFT JOIN fts ON fts.rowid = n.id
WHERE n.id = ?
```

`LEFT JOIN fts` because traversal reaches ghost/URL nodes that have no FTS row. `summary` comes back `NULL`, and `row_to_traversal_hit` falls back to `""`.

## `refresh() -> WriteResult`

Rebuilds the DB from the corpus. Open an rw connection, apply migrations (idempotent), then run the walker inside a `write_transaction`:

```python
def refresh(self):
    with self._db.open_rw() as conn:
        migrations.apply(conn)
        with write_transaction(conn):
            return walker.walk(conn, self._corpus_root)
```

Transaction-nesting note: `migrations.apply(conn)` runs its own `executescript` (which commits any pending transaction) and returns with no open transaction. The outer `write_transaction` then opens a fresh one for the walk. The two run sequentially, not nested: the schema apply commits before the walk's truncate-and-rebuild begins. See [[docs/notes/migrations-py-design.md]].

## `export(path) -> WriteResult`

Backs the `export` tool. Copies the live DB to `path` (default `.hoplite/<ISO>.index.sqlite`) using `sqlite3`'s online-backup API:

```python
def export(self, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with self._db.open_ro() as src:
        dest = sqlite3.connect(path)
        try:
            src.backup(dest)
            counts = self._count_rows(src)   # same snapshot that was backed up
        finally:
            dest.close()
    return WriteResult(path=str(path.resolve()), counts=counts)
```

`conn.backup()` is a byte-for-byte page copy that holds brief read locks. The export schema is identical to the live schema by construction; the old `DUMP_SCHEMA` source-of-truth promise is now structural. `_count_rows` runs inside the `with src:` block, so the counts come from the backed-up snapshot, not a later `open_ro`.

## Private helpers

Each takes an open connection, so one public method's connection covers all its sub-queries.

### `_resolve_uri(conn, target) -> int | None`

Resolves a wikilink target to a `node.id`, or `None`. The chain is shorter than the old one because the casefold step is gone, folded into the column collation:

1. Strip `#anchor` and `|alias` suffixes (display syntax, not part of the key).
2. Exact match: `SELECT id FROM node WHERE uri = ?` — case-insensitive via `node.uri COLLATE NOCASE`.
3. Alias match: `SELECT id FROM node WHERE id IN (SELECT id FROM node_property WHERE key = 'aliases' AND value = ? COLLATE NOCASE)`.
4. If 2–3 miss and the target lacks `.md`, append `.md` and retry the whole chain.

The `.md` retry wraps steps 2–3 (not just one of them), matching the old resolver's behavior.

### `_tags_for_paths(conn, paths) -> dict[str, list[str]]`

One batched query for the `search` tag-filter post-pass. It fetches every candidate's tags keyed by `node.uri`, so N candidates cost one round-trip plus a Python hash-group instead of N queries.

```sql
SELECT n.uri AS path, p.value AS tag
FROM node n JOIN node_property p ON p.id = n.id
WHERE p.key = 'tags' AND n.uri IN (?, ?, ...)
```

### `_count_rows(conn) -> dict[str, int]`

Row counts for `WriteResult.counts`: `documents`/`ghosts`/`urls`/`edges`. `ghosts`/`urls` partition the `resolved = 0` nodes by whether `uri` is an `http(s)://` URL. `documents` is `resolved = 1`, and `edges` is `SELECT COUNT(*) FROM edge`.

## Tests

`:memory:` connections are constructed directly, populated via the shared `_db_fixtures` helpers (the same `_populate_*` helpers `test_row_factories.py` uses, factored into `tests/_db_fixtures.py`), then exercised through the public methods.

1. `test_resolve_uri_exact` — node at `docs/notes/foo.md`; resolve it; assert its id.
2. `test_resolve_uri_case_insensitive` — node at `docs/notes/foo.md`; resolve `DOCS/NOTES/FOO.MD`; assert the same id (collation, not casefold-on-store).
3. `test_resolve_uri_strips_anchor_and_alias` — resolve `docs/notes/foo.md#sec|label`; assert same id.
4. `test_resolve_uri_alias` — node with `(key='aliases', value='old/path.md')`; resolve `old/path.md`; assert its id.
5. `test_resolve_uri_md_retry` — node at `docs/notes/foo.md`; resolve `docs/notes/foo`; assert its id.
6. `test_resolve_uri_miss_returns_none` — empty corpus; resolve anything; assert `None`.
7. `test_search_bm25_ranked` — three docs with the query term at different frequencies; assert descending score order.
8. `test_search_applies_tag_predicate` — five FTS-matching docs, three tagged `hoplite`; predicate `hoplite`; assert the three.
9. `test_search_no_over_fetch_truncates_at_limit` — `limit=2`, predicate rejecting most candidates; assert the full FTS set was considered and the result is ≤2.
10. `test_search_tags_sorted_ascending` — doc with tags `[c, a, b]`; assert `hit.tags == ['a','b','c']`.
11. `test_search_tag_only_surfaces_ghosts` — tag-only query for `ghost`; assert a ghost node (no FTS row) is returned.
12. `test_traverse_breadth_first` — star `a → b,c,d`; depth 1; assert three hits at distance 1, ordered `(distance, path)`.
13. `test_traverse_respects_depth` — chain `a→b→c→d`; depth 2 from a; assert b, c present, d absent.
14. `test_traverse_cycle_safe` — `a→b→a`; depth 10; assert b once, a not re-emitted.
15. `test_traverse_top_k_related_tie_break` — node with five `related` edges, two equal-confidence; `top_k_related=4`; assert the two equal-confidence neighbors come out ordered by ascending target path.
16. `test_traverse_always_follows_authored` — `top_k_related=0` with mentions+related edges; assert mentions/cites still followed, related dropped.
17. `test_traverse_via_edges_full_path` — `a→b→c`; depth 2; assert c's `via_edges` carries both hops, in order.
18. `test_traverse_unresolved_origin_raises` — `traverse("no-such.md", ...)`; assert `ValueError("unknown starting document: 'no-such.md'")`.
19. `test_export_byte_identical_counts` — populate, export, open the destination; assert per-table row counts match the source.

## Risks for the implementer

### Hard rules — don't violate these

- **Don't cache connections on the instance.** A fresh connection per `open_ro`/`open_rw` call is by design (see [[docs/notes/db-py-design.md]]). Caching defeats the per-call concurrency model and the future `PooledDatabase` swap-in.
- **Don't reintroduce in-memory adjacency.** No dicts of `out_edges`/`in_edges` on `Graph`. If `traverse` feels slow, the answer is a better CTE or an index, not a Python cache.
- **Don't push the tag predicate into SQL without profiling.** The Python evaluator runs in microseconds per candidate; boolean-tree-to-SQL is a real query-plan cost.
- **Don't casefold URIs anywhere.** `COLLATE NOCASE` on `node.uri` is the entire case-insensitivity mechanism. Storing or matching against a casefolded copy is the deleted contract, and reintroducing it is a bug.

### Known gaps — accepted, documented, not yet fixed

- **`refresh()` depends on `walker.walk` (step 5).** Until the walker lands, `refresh()` is a stub, and its tests ship with the walker.
- **Schema/model vocabulary drift.** `schema.sql` says `node`/`uri`; `models.py`/`row_factories.py` say `Document`/`path`. The queries bridge it with `n.uri AS path`. A future pass should rename the models or accept the alias permanently, tracked in [[docs/todos/db-refactor.md]].
- **`node_property` is `WITHOUT ROWID`.** There is no `rowid`, so tag aggregation can't `ORDER BY rowid`. Tags are sorted at projection (`row_to_hit`/`row_to_traversal_hit`) regardless, so column order is moot for them. Any future order-sensitive property must order by `(key, value)` or carry an explicit ordinal.

### Future considerations — forward-pointers

- **Python BFS fallback** if the recursive CTE underperforms at realistic depths. Swap it behind `traverse` without touching the public surface.
- **Pure-SQL tag-predicate compilation** if the Python evaluator becomes the bottleneck on heavy-tag queries.
- **Connection pooling** lands behind the `Database` interface, with no change to `graph.py` (see [[docs/todos/db-refactor.md]] "Connection pooling vs locking").

### Editorial

- The class is just `Graph`, in `graph.py`. No Protocol, no `SqliteGraph`/`InMemoryGraph` prefix, because there is one implementation. Callers `from hoplite.graph import Graph` and construct `Graph(db, corpus_root)`.
- Public methods take their argument set keyword-friendly, and `tools.py` call sites pass keywords for readability.
