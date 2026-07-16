---
title: tools.py — MCP handlers over the Graph
summary: "`tools.py` keeps its four-handler surface (`where`, `relatives`, `refresh`, `export`) but the bodies shrink to predicate parsing plus a single call into a `Graph`. The module-level `_graph` singleton is replaced by a `FileDatabase` singleton; each handler constructs a per-call `Graph(db, corpus_root)` and lets `with db.open_*()` blocks own connection lifetime. Wire-format and tool semantics are unchanged."
tags: [note, sqlite, design, hoplite, mcp]
created: 2026-05-28
status: design
---

# tools.py — MCP handlers over the Graph

`tools.py` keeps its existing four-handler surface (`where`, `relatives`, `refresh`, `export`), but the bodies shrink to predicate parsing plus a single call into a `Graph`. The module-level `_graph` singleton is replaced by a `FileDatabase` singleton; each handler constructs a per-call `Graph(db, corpus_root)` (see [[docs/notes/graph-py-design.md]]) and lets `with db.open_*()` blocks own connection lifetime. There is one `Graph` implementation, SQLite-backed, so the handler depends on the concrete class directly: no Protocol, no impl selection.

Sibling design notes: [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale; [[docs/notes/db-refactor.md]] for the broader plan; [[docs/notes/db-py-design.md]] (the `Database` interface), [[docs/notes/graph-py-design.md]] (the `Graph` this delegates to), and [[docs/notes/walker-py-design.md]] (the writer behind `Graph.refresh()`) for collaborating modules. This note covers `tools.py` alone.

## Surface preserved

The MCP wire schema in `docs/hoplite/hoplite-tool-api.md` is the contract; this refactor preserves it.

- `where(predicate: MatchPredicate, k: int) -> list[Hit]`
- `relatives(from_: str, predicate: TraversePredicate | None, depth: int) -> list[TraversalHit]`
- `refresh() -> WriteResult`
- `export(path: str | None) -> WriteResult`

The Pydantic `MatchPredicate` and `TraversePredicate` models stay where they are. The `__all__` export list stays as-is. The MCP tool annotations in `server.py` don't change.

## Module state

Today's module-level state is three globals: `_graph`, `_corpus_root`, `_hoplite_root`. The new shape:

```python
_database: Database | None = None
_corpus_root: Path | None = None
_hoplite_root: Path | None = None


def set_root(cwd: Path) -> None:
    global _database, _corpus_root, _hoplite_root
    _corpus_root = cwd / "docs"
    _hoplite_root = cwd / ".hoplite"
    db_path = _hoplite_root / "hoplite.schema.001.sqlite"
    _database = FileDatabase(db_path)
```

`_graph` is gone. `_database` holds a `FileDatabase` constructed once at `set_root()`. Construction is cheap: no connection opens, no schema applies, it just stashes the path. This matches the "server bootstrap does nothing" decision in [[docs/notes/db-refactor.md]].

`set_root()` is still called at module import from `server.py`. The signature is unchanged.

## Handler bodies — the new shape

Each handler resolves the singleton database, constructs a per-call `Graph`, and delegates. The bodies become about 5 to 10 lines each.

```python
from hoplite import parser
from hoplite.graph import Graph


def _build_graph(db: Database) -> Graph:
    return Graph(db, _corpus())


def match_nodes(predicate: MatchPredicate, k: int = 5) -> list[Hit]:
    _validate_match_predicate(predicate, k)
    graph = _build_graph(_require_database())
    text = (predicate.text or "").strip() or None
    tag_expr = (predicate.tagged or "").strip()
    tag_ast = parser.parse_predicate(tag_expr) if tag_expr else None
    try:
        return graph.search(text=text, tag_ast=tag_ast, limit=k)
    except IndexNotFoundError as e:
        raise ValueError(str(e)) from e


def traverse_nodes(
    from_: str,
    predicate: TraversePredicate | None = None,
    depth: int = 1,
) -> list[TraversalHit]:
    if depth < 1:
        raise ValueError(f"depth must be >= 1; got {depth}")
    graph = _build_graph(_require_database())
    pred = predicate or TraversePredicate()
    tag_expr = (pred.tagged or "").strip()
    tag_ast = parser.parse_predicate(tag_expr) if tag_expr else None
    try:
        return graph.traverse(
            from_=from_,
            edge_types=set(pred.edge_types or []),
            direction=pred.direction,
            top_k_related=pred.top_k_related,
            tag_ast=tag_ast,
            depth=depth,
        )
    except IndexNotFoundError as e:
        raise ValueError(str(e)) from e


def reindex() -> WriteResult:
    graph = _build_graph(_require_database())
    try:
        return graph.refresh()
    except GraphRefreshInProgressError as e:
        raise ValueError(str(e)) from e


def dump_index(path: str | None = None) -> WriteResult:
    graph = _build_graph(_require_database())
    destination = Path(path) if path else _default_export_path()
    try:
        return graph.export(destination)
    except IndexNotFoundError as e:
        raise ValueError(str(e)) from e


def _require_database() -> Database:
    if _database is None:
        raise RuntimeError("set_root() must be called before any handler")
    return _database


def _default_export_path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    return _hoplite_state() / f"{stamp}.index.sqlite"
```

The Pydantic models never cross into `Graph`. `tools.py` is the parsing boundary: it strips `text`/`tagged`, calls `parser.parse_predicate` to produce a `TagExpression` AST (a callable on a tag set), and dispatches scalars. `Graph` stays Pydantic-free, which keeps `graph.py` free of any upward dependency on `tools.py`, so there is no import cycle.

What moves out of `tools.py` (into `Graph`, see [[docs/notes/graph-py-design.md]]):
- `_escape_fts5_query` → into `graph.py`. Today's `tools.py` is the only caller; the escape logic belongs next to the FTS query that uses it.
- `_neighbors` and the `deque`-based BFS → gone. `Graph.traverse` is a recursive CTE over the `edge` table; there is no Python neighbor-expansion loop to move.
- `_summary_for` / `_tags_for` → dead. `Graph` returns `Hit`/`TraversalHit` with summary and tags already projected.

What stays:
- Pydantic model definitions (`MatchPredicate`, `TraversePredicate`).
- `set_root`, `_corpus`, `_hoplite_state`.
- Validation that raises `ValueError` for bad input (`k < 1`, `depth < 1`, empty predicates).
- `parser.parse_predicate(tag_expr)` calls — the tag-expression-to-AST parse runs here, at the handler boundary.
- `_build_graph(db) -> Graph` — the per-call construction site.

## Error translation

Domain exceptions from `db.py` and `graph.py` are translated to `ValueError` at handler boundaries. FastMCP surfaces `ValueError` cleanly to the client as a tool error with the message intact.

| Source exception | Where raised | Translated to | Message preserved |
|---|---|---|---|
| `IndexNotFoundError` | `FileDatabase.open_ro` | `ValueError` | `"no Hoplite index at <path>; call refresh to build it"` |
| `GraphRefreshInProgressError` | `write_transaction` | `ValueError` | `"knowledge graph is being refreshed; retry shortly"` |
| `ValueError` (input validation) | `tools.py` itself | passes through unchanged | `"k must be >= 1; got 0"` etc. |

The pattern is `except <Domain> as e: raise ValueError(str(e)) from e`. The `from e` preserves the original in `__cause__`; the surfaced message is the domain error's actionable text. FastMCP has no notion of "domain errors": everything crossing the handler boundary is a successful return or a tool error, and `ValueError` is the convention for "user input or state was bad in a fixable way."

## What shrinks

Today's `tools.py` is 324 lines. After the rewrite:

- Pydantic models: ~35 lines (unchanged)
- Module state + `set_root`: ~25 lines
- Four handlers: ~50 lines (down from ~200)
- Small helpers (`_require_database`, `_default_export_path`, `_corpus`, `_hoplite_state`): ~20 lines

Estimated ~130 lines, down from 324. The BFS, `_neighbors`, `_escape_fts5_query`, and the FTS-vs-tag-only candidate path all move into `Graph`; the BFS becomes a recursive CTE.

## Tests

The existing test files (`test_smoke.py`, `test_filtering.py`, `test_traverse.py`, etc.) are the behavioral oracle — they should keep passing once `tools.py` delegates to `Graph`. Most tests don't change; the underlying implementation does.

New `tools.py`-specific tests cover the boundary behavior the existing suite doesn't exercise:

1. `test_match_nodes_without_set_root_raises` — handler called before `set_root`; assert `RuntimeError("set_root() must be called before any handler")`.
2. `test_match_nodes_translates_index_not_found` — `set_root` to a path that doesn't exist; call `match_nodes`; assert `ValueError("no Hoplite index at ...; call refresh to build it")`.
3. `test_reindex_translates_refresh_in_progress` — make `Graph.refresh` raise `GraphRefreshInProgressError`; assert `ValueError("knowledge graph is being refreshed; retry shortly")`.
4. `test_traverse_validates_depth` — `depth=0`; assert `ValueError("depth must be >= 1; got 0")` (handler-level, before any DB call).
5. `test_match_validates_k` — same shape for `k`.
6. `test_match_requires_text_or_tagged` — both empty; assert `ValueError("predicate must include at least one of `text` or `tagged`")`.
7. `test_dump_index_default_path_uses_timestamp` — `path=None`; assert the destination matches `.hoplite/<ISO>.index.sqlite`.

Tests #2 and #3 are the load-bearing ones: the domain-error-to-`ValueError` translation. Tests #4 through #6 verify handler-level validation runs before the DB is touched. A failed validation should never open a connection.

## Risks for the implementer

### Hard rules — don't violate these

- Don't cache a `Graph` instance. Construct a fresh `_build_graph(db)` per handler call. Caching reintroduces the per-process state pattern this refactor removes. Construction is cheap (two field assignments); the connection lifecycle that matters lives inside the `with db.open_*()` blocks per [[docs/notes/db-py-design.md]].
- Don't catch domain exceptions inside the `Graph` call. Let `Graph` raise; the handler's `try/except` translates at the boundary.
- Don't leak `sqlite3.Connection` objects across handler calls. Connections open inside `Graph` methods and close on `with`-exit before the method returns. Holding one across an `await` (if handlers ever go async) would defeat WAL's per-call snapshot model.
- Don't move predicate parsing into `Graph`. It belongs at the handler boundary so `Graph` stays Pydantic-free and import-cycle-free.

### Known gaps — accepted, documented, not yet fixed

- `set_root()` must be called before any handler. Server bootstrap (see [[docs/notes/server-py-design.md]]) calls it at import, so day-to-day this never fires. Tests importing `tools` directly call `set_root(tmp_path)` in a fixture.

### Future considerations — forward-pointers

- Async handlers. FastMCP supports async bodies. `Graph` methods stay sync; async handlers `await asyncio.to_thread(graph.search, ...)`. The per-call `Database` model means each thread gets its own connection cleanly.
- `_escape_fts5_query` move. Today's logic is correct and well-tested. The mechanical move into `graph.py` should preserve the function shape exactly.

### Editorial

- Tools module name stays `tools.py`. Don't rename or split. The MCP wire schema and existing tests reference the current names.
- Handler call sites in `server.py` continue to wrap each function with `mcp.tool(...)`. No changes beyond what step 7 needs.
