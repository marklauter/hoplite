---
title: graph.py — Graph Protocol + InMemoryGraph
summary: Step 4's in-memory side. `graph.py` defines the `Graph` Protocol (the single interface `tools.py` depends on) and renames today's `Graph` class to `InMemoryGraph`. Search/traverse logic that lives in `tools.py` today moves onto `InMemoryGraph` so it satisfies the Protocol without help. The peer `SqliteGraph` lives in `graph_sqlite.py`; both stay in tree permanently.
tags: [note, sqlite, design, hoplite, interface]
created: 2026-05-28
document.status: design
---

# graph.py — Graph Protocol + InMemoryGraph

Step 4's in-memory side. `graph.py` defines the `Graph` Protocol (the single interface `tools.py` depends on) and renames today's `Graph` class to `InMemoryGraph`. Search/traverse logic that lives in `tools.py` today moves onto `InMemoryGraph` so it satisfies the Protocol without help. The peer `SqliteGraph` lives in `graph_sqlite.py`; both stay in tree permanently.

Sibling design notes: [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale; [[docs/notes/db-refactor.md]] for the broader plan; [[docs/notes/graph-sqlite-py-design.md]] for the SQL-backed peer and the [Protocol contracts](#protocol-contracts-checklist) spec; [[docs/notes/tools-py-design.md]] for the handlers that depend on the Protocol. This note covers `graph.py` alone.

## What changes in `graph.py`

Three deliverables in one module:

1. **Define the `Graph` Protocol** — the interface every concrete impl satisfies.
2. **Rename the existing `Graph` class to `InMemoryGraph`** — pure rename plus the new methods below; field shape (`documents`, `document_properties`, `out_edges`, `in_edges`, `aliases`, `casefold_index`, `fts`, `warnings`) is unchanged.
3. **Add `search` and `traverse` methods on `InMemoryGraph`** — the BFS loop, `_neighbors`, and FTS-candidate path move here from `tools.py`. `refresh` and `export` reshape the existing `walk` free function and `dump_index` method into instance methods that match the Protocol surface.

What stays in `graph.py` unchanged:
- The dataclass fields and their `default_factory` initializers.
- `add_edge` (still used by the walker).
- `resolve_wikilink` (referenced by the new `traverse` method).
- The walker (`walk(corpus_root) -> InMemoryGraph`) stays as a free function; `InMemoryGraph.refresh` calls it.
- The `_write_*` family of private writers and `dump_index`. `export` reuses the existing dump path verbatim — no change to how the in-memory side serializes to a file.

## The `Graph` Protocol

```python
from typing import Literal, Protocol

from hoplite.filtering import TagExpression
from hoplite.models import Hit, TraversalHit, WriteResult


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
```

Split scalars, not Pydantic models. The wire-schema types `MatchPredicate` / `TraversePredicate` live in `tools.py` for FastMCP validation; they do not cross the Protocol seam. `tools.py` parses the tag expression at the handler boundary and dispatches scalars. This keeps `graph.py` free of any upward dependency on `tools.py` — no import cycle.

`TagExpression` is the parsed tag-predicate AST (from `hoplite.filtering`) — a callable on a tag set returning `bool`. Both impls call it the same way: `tag_ast(frozenset(node_tags))`.

## `InMemoryGraph` — what changes

The class body keeps every existing field and existing method. Three new methods land; `dump_index` is renamed/wrapped.

### `search(text, tag_ast, limit) -> list[Hit]`

Moved from `tools.match_nodes`. Same algorithm: FTS5 query against the in-memory `fts` connection, then post-filter by tag expression, then truncate to `limit`. The `_escape_fts5_query` helper moves into `graph.py` (or stays a free function imported into `InMemoryGraph`); today's call site in `tools.py` is the only consumer.

When `text` is `None`, search the full corpus (the existing "no FTS query" branch). When `text` is set, run FTS and rank by BM25. Tag filter applies in either case.

Result construction uses `Hit(path=..., summary=_summary_for(self, path), tags=sorted(_tags_for(self, path)), score=...)`. The `sorted()` call is the in-memory side of the contract pinned in [[docs/notes/row-factories-py-design.md]] — the SQL side sorts inside `row_to_hit`; the in-memory side sorts here. Same observable behavior.

### `traverse(from_, *, edge_types, direction, top_k_related, tag_ast, depth) -> list[TraversalHit]`

Moved from `tools.traverse_nodes`. The `deque`-based BFS, the `_neighbors` helper (with its `(confidence desc, target_path asc)` tie-break for `related` edges), the visited-set bookkeeping, and the path accumulation all move onto `InMemoryGraph`. The algorithm is unchanged — only the home address.

`resolve_wikilink` is already on the class; the new `traverse` calls `self.resolve_wikilink(from_)` and raises `ValueError(f"unknown starting document: {from_!r}")` on miss. Matches today's behavior and the Protocol contract.

`TraversalHit.via_edges` carries the full path of edges from origin to each node, not just the last hop. `TraversalHit.tags` is `sorted(_tags_for(self, path))` — same sort-at-projection rule as `search`. Output is sorted by `(distance, path)` ascending before return.

### `refresh() -> WriteResult`

New method. Calls the existing `walk(self._corpus_root)` free function, replaces every field on `self` with the corresponding field on the freshly-walked graph, and returns a `WriteResult` with the row counts.

```python
def refresh(self) -> WriteResult:
    fresh = walk(self._corpus_root)
    self.documents = fresh.documents
    self.document_properties = fresh.document_properties
    self.edge_properties = fresh.edge_properties
    self.out_edges = fresh.out_edges
    self.in_edges = fresh.in_edges
    self.aliases = fresh.aliases
    self.casefold_index = fresh.casefold_index
    if self.fts is not None:
        self.fts.close()
    self.fts = fresh.fts
    self.warnings = fresh.warnings
    return WriteResult(path="<in-memory>", counts=self._counts())
```

Field-by-field swap rather than `self.__dict__.update(fresh.__dict__)` because `slots=True` is not on this dataclass today and replacing `__dict__` wholesale doesn't compose with possible future inheritance. Explicit is fine — eight fields.

The `_counts()` helper computes documents / ghosts / urls / edges by the same logic `dump_index` already uses (lines 136–151 of today's `graph.py`); factor that into a small helper so both `refresh` and `export` share it.

`InMemoryGraph.refresh` needs a `_corpus_root` field on the class. Today's class doesn't carry one — `walk(corpus_root)` is called from outside. Add `_corpus_root: Path` to the dataclass (or pass it through `__init__`); the constructor signature `InMemoryGraph(corpus_root: Path)` mirrors `SqliteGraph(db, corpus_root)`.

### `export(path) -> WriteResult`

Today's `dump_index(path)` renamed to `export(path)`. The method body doesn't change — it's the existing `_write_documents` / `_write_document_properties` / `_write_edges` / `_write_edge_properties` / `_write_fts` chain. The rename matches the Protocol method name; the implementation is unchanged.

Keep `dump_index` as a thin alias for one release if any external caller still uses the old name — or just rename and update callers (there's one in `tools.dump_index`, which becomes `graph.export(path)` by the rename).

## Logic that moves from `tools.py`

Listed for the implementation agent, in order of how much each touches:

| Symbol | Today | New home |
|---|---|---|
| `match_nodes` body (FTS + tag filter) | `tools.py` | `InMemoryGraph.search` |
| `_escape_fts5_query` | `tools.py` | top of `graph.py` (or imported into it) |
| `traverse_nodes` body (BFS loop, visited set, path accumulation) | `tools.py` | `InMemoryGraph.traverse` |
| `_neighbors` (with `related` tie-break) | `tools.py` | private helper on `InMemoryGraph` |
| `_summary_for(graph, path)` | `tools.py` | private helper on `InMemoryGraph` (or inlined; both call sites collapse) |
| `_tags_for(graph, path)` | `tools.py` | private helper on `InMemoryGraph` |
| `_ALWAYS_FOLLOW` constant | `tools.py` | module-level constant in `graph.py` |

After the move, `tools.py` contains predicate parsing, validation, and one-line dispatches to `graph.search` / `graph.traverse`. See [[docs/notes/tools-py-design.md]] for the post-move handler shape.

## Protocol contracts checklist

The authoritative spec is the contracts table in [[docs/notes/graph-sqlite-py-design.md#protocol-contracts]]. Mirroring it here as a checklist for the in-memory side:

| Contract | Where it lives in `InMemoryGraph` |
|---|---|
| Tag list sorted ascending on `Hit` / `TraversalHit` | `Hit(..., tags=sorted(_tags_for(self, path)))` in `search`; same shape in `traverse`. Today's `tools.py` already sorts traversal hits — match `search` to the same rule. |
| `traverse` output ordered `(distance, path)` ascending | Already true in today's `tools.py:traverse_nodes` (`hits.sort(key=lambda h: (h.distance, h.path))`). Preserve in the move. |
| `related`-edge tie-break `(confidence desc, target_path asc)` | Already in `tools.py:_neighbors`. Preserve in the move. |
| `search` considers full FTS-matched set before tag filter, truncates at `limit` | Today's `tools.py:match_nodes` already does this. Don't introduce over-fetch shortcuts. |
| Unresolved origin in `traverse` → `ValueError` | Already in today's `tools.py:traverse_nodes`. Preserve. |
| Origin excluded from `traverse` output | Already true; preserve. |
| Wikilink resolution chain | `InMemoryGraph.resolve_wikilink` already implements the chain (path → alias → casefold → `.md`-retry-wraps-chain). No changes needed. |

A contract divergence between `InMemoryGraph` and `SqliteGraph` is a Protocol bug. Fix in whichever side drifted; the table is authoritative.

## Tests

The 178 existing tests are the parity oracle. Parameterize the relevant test files (`test_smoke.py`, `test_filtering.py`, `test_traverse.py`) over both `InMemoryGraph` and `SqliteGraph` so every Protocol-level assertion runs twice. Helper:

```python
@pytest.fixture(params=["in_memory", "sqlite"])
def graph_factory(request, tmp_path):
    if request.param == "in_memory":
        return lambda corpus_root: InMemoryGraph(corpus_root)
    else:
        db = FileDatabase(tmp_path / ".hoplite" / "test.sqlite")
        return lambda corpus_root: SqliteGraph(db, corpus_root)
```

New `graph.py`-specific tests cover the in-memory class shape:

1. `test_in_memory_graph_search_returns_sorted_tags` — populate one doc with tags `[c, a, b]`; `search`; assert `hit.tags == ['a', 'b', 'c']`.
2. `test_in_memory_graph_traverse_unresolved_origin_raises_value_error` — call with unknown `from_`; assert `ValueError("unknown starting document: ...")`.
3. `test_in_memory_graph_refresh_replaces_state` — populate corpus, mutate one file on disk, call `refresh`; assert the change is visible. Verifies the field-by-field swap.
4. `test_in_memory_graph_satisfies_protocol` — `isinstance(InMemoryGraph(tmp_path), Graph)` via `runtime_checkable` (if we mark the Protocol so) or a structural check via `hasattr`. Documents that the surface is intentional, not accidental.

Most other existing tests change zero lines — they were already calling `tools.match_nodes` / `tools.traverse_nodes`, which now dispatch through the Protocol. The few that reach into `graph.documents`/`graph.out_edges` directly (if any) stay valid because those fields are still public on `InMemoryGraph`.

## Risks for the implementer

### Hard rules — don't violate these

- **Don't break the public field shape on `InMemoryGraph`.** Tests, the walker, and downstream code (if any) read `documents`, `out_edges`, `in_edges`, `aliases`, `casefold_index`, `document_properties`, `edge_properties`, `fts`, `warnings` directly. The rename is just a rename; the fields stay.
- **Don't try to satisfy the Protocol with classmethods or static methods.** Both impls are instance-based; that's what `Graph(Protocol)` declares.
- **Don't import from `tools.py` in `graph.py`.** That reintroduces the cycle. Predicate parsing belongs at the handler boundary; the Protocol takes scalars.
- **Don't drop the `tags=sorted(...)` call on `Hit` and `TraversalHit`.** It's the in-memory mirror of the `row_factories` sort. Pinned by test #1 above and by the cross-impl parity tests.

### Known gaps — accepted, documented, not yet fixed

- **`refresh` swaps state field-by-field.** Eight assignments. If `InMemoryGraph` ever grows a new field, refresh has to learn about it. Acceptable at current size; revisit if the field count climbs.
- **`InMemoryGraph` carries the FTS5 connection (`self.fts`) across refreshes.** The old connection is closed and replaced inside `refresh`. A concurrent `search` call holding a reference to the old connection would crash. Day-one we assume serial use of one `InMemoryGraph` instance; if MCP handler concurrency becomes real for the in-memory impl, this is the bug to revisit.
- **No `_corpus_root` on today's `Graph` class.** Adding it is mechanical (one field, one constructor arg). Existing callers of `walk(corpus_root)` continue to work; the new field is for `refresh`'s use.

### Future considerations — forward-pointers

- **Move the walker into `InMemoryGraph` as a method.** Today's `walk(corpus_root) -> InMemoryGraph` is a free function and `refresh` is the only caller. Could be `self._populate_from(corpus_root)` instead. Not changing it day-one because the walker is large and refactoring it out is a separate decision.
- **`runtime_checkable` on the Protocol.** If we want `isinstance(x, Graph)` to work at runtime (e.g., for the construction site to validate its return type), decorate the Protocol with `@runtime_checkable`. Costs a small amount of structural checking; gains a runtime assertion. Not needed day-one.

### Editorial

- **`InMemoryGraph` over `MemoryGraph` or `DictGraph`.** "In-memory" is the term used in `reify-in-memory-graph-as-file-based-sqlite.md` and across the design corpus; matching it.
- **`Graph` (the Protocol) keeps the simple name.** Concrete impls carry the distinguishing prefix. Callers that read `from hoplite.graph import Graph` continue to compile; the type they're importing just changed from a class to a Protocol.
