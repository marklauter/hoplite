---
title: graph_sqlite.py — SqliteGraph, the SQL-backed Graph implementation
summary: `graph_sqlite.py` defines `SqliteGraph`, one of two implementations of the `Graph` Protocol. The Protocol surface (`search`, `traverse`, `refresh`, `export`) lives in `graph.py` alongside the peer `InMemoryGraph`; both implementations are permanent. `SqliteGraph` opens a `sqlite3.Connection` per method through the injected `Database`, runs SQL queries that feed `row_factories.py`, and returns the same dataclasses the in-memory peer returns.
tags: [note, sqlite, design, hoplite, interface]
created: 2026-05-28
document.status: design
---

# graph_sqlite.py — SqliteGraph, the SQL-backed Graph implementation

`graph_sqlite.py` defines `SqliteGraph`, one of two implementations of the `Graph` Protocol. The Protocol surface (`search`, `traverse`, `refresh`, `export`) lives in `graph.py` alongside the peer `InMemoryGraph` (today's class, renamed); both implementations are permanent. `SqliteGraph` opens a `sqlite3.Connection` per method through the injected `Database`, runs SQL queries that feed `row_factories.py`, and returns the same dataclasses the in-memory peer returns.

Sibling design notes: [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale; [[docs/notes/db-refactor.md]] for the broader plan; [[docs/notes/db-py-design.md]] (the `Database` interface this depends on), [[docs/notes/migrations-py-design.md]] (the schema this queries), and [[docs/notes/row-factories-py-design.md]] (the projection layer this composes with) for the modules this collaborates with. This note covers `graph_sqlite.py` alone — the Protocol contract is shared with `InMemoryGraph` and pinned below in [Protocol contracts](#protocol-contracts).

## Position in the Graph protocol

`Graph` is a `typing.Protocol`, defined in `graph.py` alongside the in-memory implementation. Two classes satisfy it:

```python
# hoplite/graph.py
class Graph(Protocol):
    def search(
        self,
        text: str | None,
        tag_ast: TagExpression | None,
        limit: int,
    ) -> list[Hit]: ...
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


class InMemoryGraph:
    # today's class, renamed. Holds documents/out_edges/in_edges/aliases dicts.
    # search/traverse logic moves here from tools.py so it satisfies the Protocol.
    ...
```

The Protocol takes split scalars, not the Pydantic `MatchPredicate` / `TraversePredicate` from `tools.py`. The Pydantic models are tool-boundary input types — they exist for FastMCP wire-schema validation and don't belong on internal interfaces. Predicate parsing (`parser.parse_predicate`) runs at the `tools.py` boundary; the parsed `TagExpression` AST (a callable on a tag set, from `hoplite.filtering`) crosses the seam as a primitive. This avoids the `graph_sqlite.py → tools.py → graph_sqlite.py` import cycle that would otherwise form.

```python
# hoplite/graph_sqlite.py
class SqliteGraph:
    # SQL-backed, opens fresh connections per call through Database.
    ...
```

Both implementations are permanent peers. `InMemoryGraph` does not have a declared runtime role yet (TBD); the Protocol exists so the two impls sit side-by-side without `tools.py` knowing which one it has. Bootstrapping today wires `SqliteGraph` (see [[docs/notes/tools-py-design.md]]); swapping in `InMemoryGraph` is a one-line change at the construction site.

The Protocol surface is the contract every method must honor in the same way across both impls. The conventions that affect parity — tag-list ordering, traversal sort order, `related`-edge tie-break, over-fetch policy — are pinned below in [Protocol contracts](#protocol-contracts), not deferred to "step 9 will catch it." A divergence between impls is a Protocol bug, fixed in whichever side drifted.

## Class shape

```python
class SqliteGraph:
    def __init__(self, db: Database, corpus_root: Path) -> None:
        self._db = db
        self._corpus_root = corpus_root
```

Two fields: the injected `Database` and the corpus root (load-bearing only for `refresh()`, which dispatches to the walker). No connection caching, no in-memory adjacency dicts, no aliases map — every lookup runs a SQL query.

Each public method follows the same shape: open a connection (ro for read-only operations, rw for refresh/export), run one or more queries, project rows through `row_factories`, return. The `with self._db.open_ro() as conn:` block bounds connection lifetime to the single method call.

## Public methods

These are the Protocol contract. `InMemoryGraph` and `SqliteGraph` must agree on inputs, outputs, ordering, and edge-case semantics. Where the SQL-backed implementation does something specific (per-call connection open, FTS-then-filter), it's a SqliteGraph-internal detail — the Protocol caller sees only the contracted return shape.

### `search(text, tag_ast, limit) -> list[Hit]`

The `where` tool's implementation. `text` is the BM25 text query (or `None` for tag-only search); `tag_ast` is the parsed tag predicate AST (callable on a tag set) or `None`. Returns up to `limit` documents ranked by BM25, filtered by the optional tag predicate.

Path: open ro connection; run the FTS query from row_to_hit's SQL contract; iterate results through `row_to_hit`; apply the tag predicate as a Python post-filter against each candidate's tags; return the survivors up to `limit`.

The tag predicate is applied in Python, not pushed into SQL. Reasons:
- The predicate grammar (`!`, `&`, `|`, parenthesized groups) is small enough to evaluate in Python in microseconds per candidate.
- Compiling the predicate into SQL `WHERE EXISTS (SELECT 1 FROM document_property ...)` clauses is straightforward for atoms but messy for arbitrary boolean composition.
- BM25 ranking happens first; the tag filter narrows.

**No over-fetch.** When a tag predicate is present, the SQL fetches the *full* FTS-matched set (no `LIMIT` push-down), the Python evaluator filters it, and the result is truncated to `limit`. Over-fetching with `limit * N` would be a real behavior change relative to `InMemoryGraph`, which today considers every FTS match before filtering — Protocol parity wins over "fewer rows materialized." If profiling shows the full-fetch dominates on large corpora, the optimization is to push the predicate into SQL, not to over-fetch.

### `traverse(from_, *, edge_types, direction, top_k_related, tag_ast, depth) -> list[TraversalHit]`

The `relatives` tool's implementation. `edge_types` is the set of edge kinds to follow (empty set = follow all); `direction` selects `out`/`in`/`both`; `top_k_related` caps the number of `related` edges followed per node by descending confidence (or `None` for no cap); `tag_ast` is a parsed tag predicate (or `None`) used to post-filter reached nodes. Breadth-first walk from `from_`, returning one `TraversalHit` per node reached at distance 1..depth (excluding the origin).

Path: open ro connection; resolve `from_` to a `document.id` via the wikilink resolver helper; run a BFS loop in Python, issuing one SELECT against the edge table per depth level; track visited node ids to avoid cycles; remember the full path of via-edges from origin to each reached node (not just the last hop); then for each visited node, run a per-node projection SELECT and feed it through `row_to_traversal_hit` together with the accumulated edge path.

The projection SELECT shape, fed to the landed `row_to_traversal_hit(row, via_edges)` factory:

```sql
SELECT d.path,
       fts.summary,
       (SELECT json_group_array(value) FROM (
          SELECT value FROM document_property
          WHERE id = d.id AND key = 'tags' ORDER BY rowid
        )) AS tags,
       ? AS distance
FROM document d
LEFT JOIN fts ON fts.rowid = d.id
WHERE d.id = ?
```

The first `?` is the BFS-computed distance, bound as a literal column value so the row carries it where `row_to_traversal_hit` expects (`row["distance"]`). The second `?` is the visited node id. `LEFT JOIN fts` because traverse can reach nodes that don't have FTS rows (the contract about ghost/URL inclusion is up to the walker, but the join doesn't fail when fts is absent — the `summary` comes back NULL and `row_to_traversal_hit` falls back to `""`).

This per-node projection is the *only* way distance enters a row. There is no schema column for it, no helper that materializes tags separately from this SELECT, and no Python-side bypass of `row_to_traversal_hit`. The factory is the single projection point; everything else feeds into it.

Recursive CTE was considered and rejected for day-one:
- The Python loop is easier to read and debug, and the depth values we ship (1–3 typical) don't justify the CTE complexity.
- The CTE form requires materializing the full reachable set before any limit applies; the Python loop matches `InMemoryGraph`'s shape, which simplifies the parity oracle.
- If profiling at corpus sizes past 10k documents shows the Python loop dominates, swap to a CTE in one place without changing the public API.

`top_k_related` is enforced at each visited node — when traversing `related` edges, rank by `(confidence desc, target_path asc)` and follow only the top K. The lexicographic tie-break on target path is required for Protocol parity with `InMemoryGraph` (see `tools.py:_neighbors` today). The ranking happens in Python after the edge SELECT, not in SQL, because the "target" column depends on direction: for outbound edges `target = dst`; for inbound edges `target = src`. The SQL fetches candidate edges via `_out_edges_for` / `_in_edges_for` projected through `row_to_edge`; Python then computes the per-edge target, sorts by `(-edge.confidence, target_path)`, and truncates to `top_k_related`. The `idx_edge_kind_src` / `idx_edge_kind_dst` indexes cover the retrieval; the sort is a small in-memory cost over a per-node candidate set.

### `refresh() -> WriteResult`

Rebuilds the database from the corpus root. Open rw connection through `db.open_rw()`, call `migrations.apply(conn)` (idempotent — applies schema on first call, no-op thereafter), then call into the walker (step 5) inside a `write_transaction`. Returns a `WriteResult` with row counts.

This module owns the *coordination* (open rw, apply migrations, wrap walker call in write_transaction, return result). The walker itself is step 5 territory — the `walk(conn, corpus_root) -> WriteResult` function lives in a separate module. `refresh()` is one or two lines once the walker exists:

```python
def refresh(self) -> WriteResult:
    with self._db.open_rw() as conn:
        migrations.apply(conn)
        with write_transaction(conn):
            return walker.walk(conn, self._corpus_root)
```

The walker landing later means `refresh()` can be implemented as a TODO until step 5. Tests for `refresh()` ship with the walker; nothing useful tests in isolation here.

**Transaction nesting note.** `migrations.apply(conn)` runs its own `BEGIN IMMEDIATE` / `COMMIT` (per [[docs/notes/migrations-py-design.md]]) and returns with no open transaction. The outer `write_transaction(conn)` block then opens a *second*, independent transaction for the walker. The two do not nest — they run sequentially against the same connection. A reader of this code who assumes `write_transaction` wraps both would be wrong; the schema apply commits before the walker's truncate-and-rebuild begins. This is fine on day one (the walker re-runs migrations as a no-op if it ever needs to), but if a future change wants both phases atomic, it has to bypass `migrations.apply`'s internal transaction.

### `export(path) -> WriteResult`

Backs the live database up to `path` (default `.hoplite/<ISO>.index.sqlite`). Open ro connection, open a destination `sqlite3.Connection` against `path` with create-if-missing, call `conn.backup(dest)`, close both, return a `WriteResult` with the absolute output path and the row counts queried from the source connection.

`conn.backup()` is stdlib SQLite's online-backup API — byte-for-byte copy that runs in pages, holding read locks briefly. Replaces the `_write_documents` / `_write_edges` / etc. handlers `InMemoryGraph` carries from the old dump path. `SqliteGraph`'s dump schema is identical to its live schema by construction; the source-of-truth promise the old `DUMP_SCHEMA` constant tried to maintain is now structural. (`InMemoryGraph.export` still composes its dump from per-table writes — that's its impl detail and unrelated to the Protocol surface.)

## Internal helpers

These are private (underscore-prefixed) and used by the public methods. Each takes an open connection rather than opening its own, so a single public method's connection lifetime covers all its sub-queries.

### `_resolve_wikilink(conn, target) -> int | None`

Mirrors `InMemoryGraph.resolve_wikilink` (today's `graph.py:Graph.resolve_wikilink`). Returns the `document.id` for a resolved target or `None` if no match.

Resolution chain (matches today's behavior in `InMemoryGraph.resolve_wikilink`):
1. Strip `#anchor` and `|alias` suffixes — display syntax, not part of the lookup key.
2. Run steps 3–5 against the stripped target.
3. Exact path match: `SELECT id FROM document WHERE path = ?`.
4. Alias match: `SELECT id FROM document WHERE id IN (SELECT id FROM document_property WHERE key = 'aliases' AND value = ?)`.
5. Casefold path match: `SELECT id FROM document WHERE path = ?` where the input is `target.casefold()`. The walker stores paths in casefold form, so the same `path` column serves both exact and casefold lookups.
6. If steps 3–5 all miss and the target doesn't end in `.md`, append `.md` and rerun steps 3–5 against the new target.

The `.md` retry wraps the whole chain, not just the casefold step — appending `.md` and trying only casefold would skip the exact-path and alias matches against the `.md`-suffixed form. `InMemoryGraph` does the wrapping retry; the SQL impl must match.

No schema change needed: the walker casefolds paths before insert, so the existing `path` column is the casefold lookup column. `idx_document_path` covers it.

### `_out_edges_for(conn, doc_id, kinds) -> list[Edge]`

`SELECT e.kind, e.confidence, src_doc.path AS src_path, dst_doc.path AS dst_path FROM edge e JOIN document src_doc ON src_doc.id = e.src JOIN document dst_doc ON dst_doc.id = e.dst WHERE e.src = ? AND e.kind IN (?, ?, ...)`. The kinds-in clause is parameterized over the predicate's `edge_types` set. Covered by `idx_edge_kind_src`.

`_in_edges_for` is symmetric: filters by `e.dst = ?`, covered by `idx_edge_kind_dst`.

Both project through `row_to_edge`.

### `_properties_for(conn, doc_id) -> dict[str, list[str]]`

Groups rows from `document_property` into the same `dict[str, list[str]]` shape `InMemoryGraph.document_properties[path]` exposes — so the two impls' internal projection of properties matches when an integration test wants to compare. SQL:

```sql
SELECT key, value FROM document_property WHERE id = ? ORDER BY rowid
```

Python-side group: `result[key].append(value)`. Insertion order preserved by the `ORDER BY rowid` clause (same convention as the EAV materialization rule in [docs/hoplite/hoplite-architecture.md#eav-decomposition](../hoplite/hoplite-architecture.md#eav-decomposition)).

Not used by `search()` or `traverse()` in the projection path — both go through `row_to_hit` / `row_to_traversal_hit`, which read tags via inline `json_group_array(...)` in their projection SELECTs. `_properties_for` exists as a parity helper for integration tests that want to assert SqliteGraph's stored property shape matches InMemoryGraph's in-memory dict, and as a building block for any future operation that needs a full per-doc property dict. If no consumer ever materializes, drop it. `search()`'s tag-filter post-pass uses the batched `_tags_for_paths` instead — one query covers every candidate keyed by path.

## Protocol contracts

These are the conventions both `InMemoryGraph` and `SqliteGraph` must follow identically. They are pinned here (not in `graph.py`) only because this design note already gathers the SQL-side specifics; the in-memory side has to match.

| Contract | Behavior | Why |
|---|---|---|
| **Tag list ordering on `Hit` and `TraversalHit`** | Sorted ascending. | Owned by `row_factories.row_to_hit` / `row_to_traversal_hit` — they wrap `parse_tags(...)` in `sorted(...)` before constructing the dataclass. `SqliteGraph` inherits the sort for free; `InMemoryGraph` mirrors the same `sorted(...)` at its `Hit` / `TraversalHit` construction sites (see [[docs/notes/graph-py-design.md#protocol-contracts-checklist]]). Pinned by `test_row_to_hit_returns_tags_sorted_ascending` in [[docs/notes/row-factories-py-design.md]]. |
| **`traverse` output order** | Ascending `(distance, path)`. | Matches `tools.py:traverse_nodes` today (`hits.sort(key=lambda h: (h.distance, h.path))`). BFS visitation order would diverge. |
| **`related`-edge tie-break in `_neighbors`** | Sort by `(confidence desc, target_path asc)`; truncate to `top_k_related`. | Matches `tools.py:_neighbors` today. Without the lexicographic tie-break, equal-confidence neighbors come out in arbitrary order, surfacing as parity diffs. |
| **`search` over-fetch policy** | Full FTS-matched set considered before tag filter; truncate to `limit` at the end. | Matches `InMemoryGraph`. No over-fetch shortcut. |
| **Origin unresolved on `traverse`** | Raise `ValueError(f"unknown starting document: {from_!r}")`. | Matches `tools.py:traverse_nodes` today. |
| **Origin excluded from `traverse` output** | The origin node is not in the returned `list[TraversalHit]`. | Matches `tools.py:traverse_nodes` today. |
| **Wikilink resolution chain** | strip suffixes → exact-path → alias → casefold-path; if all miss and target lacks `.md`, append and retry the full chain. | See [_resolve_wikilink](#_resolve_wikilink-conn-target---int--none). The retry wraps; it does not just retry casefold. |

A divergence between impls on any of these rows is a Protocol bug. The parity check at step 9 (see below) walks the contract row by row.

## Tag predicate compilation

The grammar (`note`, `note & hoplite`, `(note | journal) & !draft`) is documented in `docs/hoplite/hoplite-architecture.md` and parsed today by `hoplite.filtering`. The parser doesn't change in this refactor — only the evaluator.

`search()` builds a candidate set via FTS, then for each candidate fetches its tags (one batched query joining `document_property` against the candidate paths) and calls the parsed predicate AST — which is itself a callable on a tag set, per `hoplite.filtering` — against each candidate's tag set in Python. The AST callable shape matches what `tools.py` already uses (`tag_pred(frozenset(node_tags))`), so the predicate is constructed once at the handler boundary and threaded through unchanged.

The batched fetch is the optimization that matters: instead of one query per candidate (N round-trips), one query for all candidates (1 round-trip plus a hash-group in Python). At a 50-hit `where` query with average 5 tags per document, this is ~50 cheap dict lookups instead of 50 SQLite round-trips.

Alternative pure-SQL compilation (`WHERE EXISTS (SELECT 1 FROM document_property ...)` clauses) considered and rejected for day-one — the predicate expression types are small, the Python evaluator already exists in `filtering.py`, and the batched-fetch + Python-evaluate path is fast enough.

## Module skeleton

```python
import sqlite3
from pathlib import Path
from typing import Literal

from hoplite import migrations, row_factories, walker
from hoplite.db import Database, write_transaction
from hoplite.filtering import TagExpression  # parsed predicate AST; callable on a tag set
from hoplite.models import Hit, TraversalHit, WriteResult


class SqliteGraph:
    def __init__(self, db: Database, corpus_root: Path) -> None:
        self._db = db
        self._corpus_root = corpus_root

    def search(
        self,
        text: str | None,
        tag_ast: TagExpression | None,
        limit: int,
    ) -> list[Hit]:
        with self._db.open_ro() as conn:
            candidates = self._fts_candidates(conn, text)  # full FTS-matched set; see "No over-fetch"
            if tag_ast is None:
                return candidates[:limit]
            tags_by_path = self._tags_for_paths(conn, [hit.path for hit in candidates])
            survivors = [
                hit for hit in candidates
                if tag_ast(frozenset(tags_by_path.get(hit.path, ())))
            ]
            return survivors[:limit]

    def traverse(
        self,
        from_: str,
        *,
        edge_types: set[str],
        direction: Literal["out", "in", "both"],
        top_k_related: int | None,
        tag_ast: TagExpression | None,
        depth: int,
    ) -> list[TraversalHit]:
        with self._db.open_ro() as conn:
            origin_id = self._resolve_wikilink(conn, from_)
            if origin_id is None:
                raise ValueError(f"unknown starting document: {from_!r}")
            return self._bfs(
                conn,
                origin_id,
                edge_types=edge_types,
                direction=direction,
                top_k_related=top_k_related,
                tag_ast=tag_ast,
                depth=depth,
            )

    def refresh(self) -> WriteResult:
        with self._db.open_rw() as conn:
            migrations.apply(conn)
            with write_transaction(conn):
                return walker.walk(conn, self._corpus_root)  # step 5

    def export(self, path: Path) -> WriteResult:
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._db.open_ro() as src:
            dest = sqlite3.connect(path)
            try:
                src.backup(dest)
                counts = self._count_rows(src)
            finally:
                dest.close()
        return WriteResult(path=str(path.resolve()), counts=counts)

    # ... private helpers: _resolve_wikilink, _out_edges_for, _in_edges_for,
    # _properties_for, _fts_candidates, _tags_for_paths, _bfs, _count_rows
```

No `hoplite.tools` import. The Protocol takes primitive types only — `str`, `int`, `set[str]`, `Literal`, `TagExpression` (from `hoplite.filtering`, which has no upward dependency on `tools.py`). Implementation modules stay clean of the FastMCP/Pydantic layer.

The class is small. Public methods are 5–10 lines each; private helpers are the SQL contracts compiled to Python.

Two details to note in this skeleton, both load-bearing for parity:

- `traverse` raises `ValueError` on an unresolved origin, matching `tools.py:traverse_nodes` today. `InMemoryGraph.traverse` must raise the same way. Returning `[]` would silently disagree with the in-memory peer.
- `_count_rows` runs *inside* the `with src:` block, so the counts come from the same snapshot that was backed up — not a fresh `open_ro()` afterward. A second snapshot could differ under a concurrent writer.

`_tags_for_paths` replaces the earlier `_tags_for_ids` / `_properties_for` proposal: one batched fetch keyed by `document.path` for the tag-filter post-pass in `search()`. `_properties_for(conn, doc_id)` is reserved for `traverse()`, where each `TraversalHit` materializes its own per-node tag list (no batched cross-node query because the BFS already touches each node individually).

## Tests

`:memory:` connections constructed directly, populated via the `_populate_*` helpers from `test_row_factories.py` (factored into a shared `tests/_db_fixtures.py` module to keep the helpers in one place).

Layered test strategy:
1. **Helper-level tests** — each private helper gets unit tests against a fixture corpus. Verify the SQL queries, the row factory composition, and the BFS termination.
2. **Public-method tests** — each public method gets integration tests that exercise the helper composition. Search returns BM25-ranked hits filtered by predicate; traverse returns ordered TraversalHit lists.
3. **Parity tests** — see "Parity verification" below.

Specific test bullets:

1. `test_resolve_wikilink_exact_path` — populate one document at `docs/notes/foo.md`; resolve `docs/notes/foo.md`; assert returns its id.
2. `test_resolve_wikilink_strips_anchor_and_alias` — same document; resolve `docs/notes/foo.md#section|label`; assert returns same id.
3. `test_resolve_wikilink_alias` — document with `(id=1, key='aliases', value='old/path.md')`; resolve `old/path.md`; assert returns 1.
4. `test_resolve_wikilink_casefold` — document at `docs/notes/foo.md` (stored canonical, already in casefold form); resolve `DOCS/NOTES/FOO.MD`; assert the resolver casefolds the input and matches against `path`, returning the id.
5. `test_resolve_wikilink_md_retry` — document at `docs/notes/foo.md`; resolve `docs/notes/foo` (no extension); assert resolver retries with `.md` and returns the id.
6. `test_resolve_wikilink_returns_none_on_miss` — empty corpus; resolve any target; assert None.
7. `test_out_edges_filters_by_kind` — populate three edges of different kinds from one src; query with `kinds={'mentions'}`; assert only mentions returned.
8. `test_out_edges_uses_path_columns` — assert returned Edge instances carry path strings (not integer ids) in src/dst. Smoke check that the join is wired correctly.
9. `test_properties_for_groups_by_key` — populate tags=[a,b,c] and aliases=[x,y]; assert returned dict has the right shape and insertion order.
10. `test_search_returns_bm25_ranked` — populate three documents with bodies containing the query term at different frequencies; assert returned Hits are in descending score order.
11. `test_search_applies_tag_predicate` — populate five docs all matching FTS, three tagged `hoplite`; query with `predicate=hoplite`; assert only the three are returned.
12. `test_search_no_over_fetch_truncates_at_limit` — limit=2, predicate that rejects 80% of candidates; assert the full FTS set was considered (no `limit * N` shortcut) and the returned list is correctly truncated to ≤2.
13. `test_search_returns_tags_sorted_ascending` — populate one doc with tags `[c, a, b]` (insertion order); call `search`; assert `hit.tags == ['a', 'b', 'c']`. Pins the Protocol contract for tag ordering.
14. `test_traverse_bfs_breadth_first` — populate a star (a → b, a → c, a → d); traverse from `a` depth=1; assert exactly three TraversalHits at distance=1, ordered `(distance, path)` ascending.
15. `test_traverse_respects_depth` — populate a chain (a → b → c → d); traverse depth=2 from a; assert b and c present, d absent.
16. `test_traverse_cycle_safe` — populate a → b → a (mutual); traverse depth=10 from a; assert b returned once, a not re-visited.
17. `test_traverse_top_k_related_ties_break_by_path` — populate a node with five `related` edges where two share the same confidence value; query `top_k_related=4`; assert the two equal-confidence neighbors come out ordered by ascending target path. Pins the tie-break contract.
18. `test_traverse_unresolved_origin_raises_value_error` — call traverse from `"no-such-doc.md"`; assert `ValueError("unknown starting document: 'no-such-doc.md'")`. Pins the unresolved-origin contract.
19. `test_export_creates_byte_identical_copy` — populate corpus, call export; open the destination file; assert the row counts of every table match the source.

## Parity verification

The `Graph` Protocol is the contract; step 9's parity check is the load-bearing test that both impls satisfy it identically. Both `InMemoryGraph` and `SqliteGraph` stay in tree permanently, so this isn't a "cutover gate" — it's an ongoing invariant that regression tests guard.

Step 9 will:
1. Populate the real corpus through both `InMemoryGraph` (in-memory, via today's walker) and `SqliteGraph` (file-backed, via `walker.walk`).
2. Run a fixed set of `search(predicate, limit)` calls against both; assert the `list[Hit]` outputs are equal.
3. Run a fixed set of `traverse(from_, predicate, depth)` calls against both; assert the `list[TraversalHit]` outputs are equal.
4. Compare `refresh()` `WriteResult.counts`.
5. Compare `_resolve_wikilink` resolution on targets that exercise each branch of the chain (exact, alias, casefold, with and without `.md` retry).

Each row of the [Protocol contracts](#protocol-contracts) table is a parity assertion. Discrepancies to anticipate, based on today's code:

- **Tag sort order on `Hit`/`TraversalHit`** — `row_factories.row_to_hit` / `row_to_traversal_hit` sort ascending; `InMemoryGraph` mirrors at its construction sites. Divergence here means one impl skipped the sort.
- **`traverse` output order** — `(distance, path)` ascending, not BFS visitation order.
- **`_neighbors` tie-break on `related`** — `(confidence desc, target_path asc)`, not just confidence.
- **Origin unresolved** — `ValueError`, not empty list.
- **Float precision on confidence** — SQLite REAL ↔ Python float round-trips cleanly, but worth asserting.
- **Resolution chain order** — alias-before-casefold, retry-wraps-chain.

If `InMemoryGraph` drifts (e.g., a future change to `tools.py:_neighbors` tie-break), the Protocol contracts table is the authoritative spec; update the drifting impl, not the contract.

## Risks for the implementer

### Hard rules — don't violate these

- **Don't cache connections on the `SqliteGraph` instance.** The Database interface gives a fresh connection per `open_ro()` / `open_rw()` call by design (see [[docs/notes/db-py-design.md]]). Caching a connection on `self` defeats both the per-call concurrency model and the future `PooledDatabase` swap-in.
- **Don't reintroduce in-memory adjacency dicts inside `SqliteGraph`.** That's `InMemoryGraph`'s job, in a different module. If you find yourself caching `out_edges` to make `SqliteGraph.traverse` faster, the answer is a better SQL query (or an index), not a Python dict.
- **Don't push the tag predicate into SQL for "performance" without profiling.** The Python evaluator runs in microseconds per candidate; SQLite query-plan complexity for boolean expression trees is a real cost. Measure before changing.
- **Don't break Protocol parity for a local optimization.** Any change that makes `SqliteGraph.search` or `SqliteGraph.traverse` return results that diverge from `InMemoryGraph` is a regression even if it's faster. The [Protocol contracts](#protocol-contracts) table is the authoritative spec.

### Known gaps — accepted, documented, not yet fixed

- **Casefold resolution depends on the walker storing casefolded paths.** Walker owns the contract; this design assumes it.
- **`refresh()` is a stub until step 5** — the walker function lives elsewhere. Tests for `refresh()` ship with the walker, not here.
- **`search`/`traverse` logic must move from `tools.py` onto `InMemoryGraph` for the Protocol to hold.** Today the BFS loop, `_neighbors`, FTS query, and `_escape_fts5_query` all live in `tools.py` and reach into `InMemoryGraph`'s public dicts. Step 4's deliverable is *both* `SqliteGraph` *and* an `InMemoryGraph` that satisfies the Protocol on its own. See [[docs/notes/tools-py-design.md]] for the corresponding `tools.py` shrink.

### Future considerations — forward-pointers

- **Recursive CTE for traverse** if Python BFS becomes the bottleneck past ~10k docs.
- **Pure-SQL tag predicate compilation** if the Python evaluator becomes a bottleneck on heavy-tag queries.
- **Connection pooling** lands behind the existing `Database` interface (see lock-vs-pool tradeoff in [[docs/notes/db-refactor.md]]).

### Editorial

- The class is `SqliteGraph`, not `Graph`. `Graph` is the Protocol; the concrete classes carry distinguishing names (`InMemoryGraph`, `SqliteGraph`). Both stay in tree permanently — there is no "deletion of one in favor of the other" follow-up.
- All public methods take their full argument set as keyword-friendly (no positional-only). Tools.py call sites pass keywords for readability.
