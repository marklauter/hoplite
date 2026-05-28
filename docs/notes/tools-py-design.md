---
title: tools.py — MCP handlers over the Graph Protocol
summary: `tools.py` keeps its existing four-handler surface (`where`, `relatives`, `refresh`, `export`) but the bodies shrink to predicate parsing plus a single call into a `Graph` Protocol instance. The module-level `_graph` singleton is replaced by a `FileDatabase` singleton; each handler constructs a per-call `SqliteGraph(db, corpus_root)` (the day-one default impl) and lets `with db.open_*()` blocks own connection lifetime. Wire-format and tool semantics are unchanged.
tags: [note, sqlite, design, hoplite, mcp]
created: 2026-05-28
document.status: design
---

# tools.py — MCP handlers over the Graph Protocol

`tools.py` keeps its existing four-handler surface (`where`, `relatives`, `refresh`, `export`) but the bodies shrink to predicate parsing plus a single call into a `Graph` Protocol instance. Handlers depend on the `Graph` Protocol (defined in `graph.py` per [[docs/notes/graph-sqlite-py-design.md]] "Position in the Graph protocol"); the construction line wires `SqliteGraph` as the day-one default. Swapping in `InMemoryGraph` is a one-line change at the construction site.

Sibling design notes: [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale; [[docs/notes/db-refactor.md]] for the broader plan; [[docs/notes/db-py-design.md]] (the `Database` interface), [[docs/notes/graph-sqlite-py-design.md]] (the SQL impl and the Protocol surface), and [[docs/notes/walker-py-design.md]] (the writer behind `SqliteGraph.refresh()`) for collaborating modules. This note covers `tools.py` alone.

## Surface preserved

The MCP wire schema in `docs/hoplite/hoplite-tool-api.md` is the contract; this refactor preserves it.

- `where(predicate: MatchPredicate, k: int) -> list[Hit]`
- `relatives(from_: str, predicate: TraversePredicate | None, depth: int) -> list[TraversalHit]`
- `refresh() -> WriteResult`
- `export(path: str | None) -> WriteResult`

The Pydantic `MatchPredicate` and `TraversePredicate` models stay where they are. The `__all__` export list stays as-is. The MCP tool annotations in `server.py` don't need to change.

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

`_graph` is gone. `_database` holds a `FileDatabase` instance constructed once at `set_root()`. Construction is cheap — no connection opens, no schema applies, just stashes the path. This matches the "server bootstrap does nothing" decision in [[docs/notes/db-refactor.md]] step 7.

`set_root()` is still called at module import from `server.py`. The signature is unchanged.

## Handler bodies — the new shape

Each handler resolves the singleton, constructs a per-call `Graph`, and delegates. The bodies become ~5–10 lines each. The handler type annotations use the `Graph` Protocol, not the concrete `SqliteGraph` class — so the construction line is the only place the concrete impl is named.

```python
from hoplite.graph import Graph              # the Protocol
from hoplite.graph_sqlite import SqliteGraph  # the day-one default impl


def _build_graph(db: Database) -> Graph:
    """The single construction site. Swap `SqliteGraph` for `InMemoryGraph` here."""
    return SqliteGraph(db, _corpus())


def match_nodes(predicate: MatchPredicate, k: int = 5) -> list[Hit]:
    _validate_match_predicate(predicate, k)
    db = _require_database()
    graph = _build_graph(db)
    try:
        return graph.search(predicate=predicate, limit=k)
    except IndexNotFoundError as e:
        raise ValueError(str(e)) from e


def traverse_nodes(
    from_: str,
    predicate: TraversePredicate | None = None,
    depth: int = 1,
) -> list[TraversalHit]:
    if depth < 1:
        raise ValueError(f"depth must be >= 1; got {depth}")
    db = _require_database()
    graph = _build_graph(db)
    pred = predicate or TraversePredicate()
    try:
        return graph.traverse(from_=from_, predicate=pred, depth=depth)
    except IndexNotFoundError as e:
        raise ValueError(str(e)) from e


def reindex() -> WriteResult:
    db = _require_database()
    graph = _build_graph(db)
    try:
        return graph.refresh()
    except GraphRefreshInProgressError as e:
        raise ValueError(str(e)) from e


def dump_index(path: str | None = None) -> WriteResult:
    db = _require_database()
    graph = _build_graph(db)
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

Note the predicate-parsing move: `MatchPredicate` is passed to `graph.search` whole, not split into `text` + parsed tag AST. The Protocol's `search(predicate: MatchPredicate, limit: int)` shape keeps the parser at the *graph impl* boundary — each impl parses the tag expression itself if it needs to. Either `InMemoryGraph` and `SqliteGraph` share a `_parse_tag_expr` helper in `hoplite.filtering`, or each parses inline; the Protocol contract is "accepts the `MatchPredicate`," not "accepts a parsed AST." (This is a small reversal from an earlier draft of this note that had `tools.py` parse the AST.)

What moves out of `tools.py`:
- `_escape_fts5_query` → into `graph_sqlite.py` (or a small `fts.py` helper). Today's `tools.py` is the only caller; the escape logic belongs next to the query that uses it. `InMemoryGraph` has its own FTS-escape path (the existing `:memory:` FTS connection) and doesn't share this helper.
- `_neighbors` → into the concrete `traverse` impls. Each `Graph` impl owns its own neighbor-expansion strategy: `SqliteGraph` queries the edge table; `InMemoryGraph` walks its dict.
- `_summary_for` / `_tags_for` → dead. Both `Graph` impls return `Hit` and `TraversalHit` with summary and tags already projected.
- The `deque`-based BFS loop → into `InMemoryGraph.traverse`. `SqliteGraph.traverse` has its own Python BFS over SQL queries; the algorithm is the same, but the data source differs.

What stays:
- Pydantic model definitions (`MatchPredicate`, `TraversePredicate`).
- `set_root`, `_corpus`, `_hoplite_state` (used by `_default_export_path`).
- Validation that raises `ValueError` for bad input (`k < 1`, `depth < 1`, empty predicates).
- The `_build_graph(db) -> Graph` construction site — the single point that names the concrete impl. Future runtime-selection logic (env var, settings flag, per-condition default) lands here.

## Error translation

Domain exceptions from `db.py` and `graph_sqlite.py` get translated to `ValueError` at handler boundaries. FastMCP surfaces `ValueError` cleanly to the MCP client as a tool error with the message intact.

| Source exception | Where raised | Translated to | Message preserved |
|---|---|---|---|
| `IndexNotFoundError` | `FileDatabase.open_ro` | `ValueError` | `"no Hoplite index at <path>; call refresh to build it"` |
| `GraphRefreshInProgressError` | `write_transaction` | `ValueError` | `"knowledge graph is being refreshed; retry shortly"` |
| `ValueError` (input validation) | `tools.py` itself | passes through unchanged | `"k must be >= 1; got 0"` etc. |

The translation pattern is `except <Domain> as e: raise ValueError(str(e)) from e`. The `from e` preserves the original exception in `__cause__` for debugging; the surfaced message is just the domain error's actionable text.

Why translate instead of letting domain exceptions propagate: FastMCP doesn't have a notion of "domain errors" vs "runtime errors." Everything that crosses the handler boundary is either a successful return or an exception that becomes a tool error. `ValueError` is the convention for "user input or state was bad in a way the user can fix"; that's what these are.

## What shrinks

Today's `tools.py` is 324 lines. After the rewrite:

- Pydantic models: ~35 lines (unchanged)
- Module state + `set_root`: ~25 lines
- Four handlers: ~50 lines (down from ~200)
- Small helpers (`_require_database`, `_default_export_path`, `_corpus`, `_hoplite_state`): ~20 lines

Estimated: ~130 lines, down from 324. The BFS loop, `_neighbors`, `_escape_fts5_query`, and the FTS-vs-tag-only candidate path all move into the concrete `Graph` impls (`SqliteGraph` for the SQL side, `InMemoryGraph` for the in-memory side).

## Tests

The existing test files (`test_smoke.py`, `test_filtering.py`, `test_traverse.py`, etc.) are the parity oracle — they should continue passing once `tools.py` delegates through the `Graph` Protocol. Most tests don't change; the underlying impl wired by `_build_graph` does. Parameterize the relevant test files over both `SqliteGraph` and `InMemoryGraph` so every Protocol-level assertion runs twice — that's how step 9's parity check stays a regression guard, not a one-time gate.

New `tools.py`-specific tests cover the boundary behavior the existing suite doesn't exercise:

1. `test_match_nodes_without_set_root_raises` — handler called before `set_root`; assert `RuntimeError("set_root() must be called before any handler")`.
2. `test_match_nodes_translates_index_not_found` — `set_root` to a path that doesn't exist; call `match_nodes`; assert `ValueError("no Hoplite index at ...; call refresh to build it")`.
3. `test_reindex_translates_refresh_in_progress` — mock `Graph.refresh` to raise `GraphRefreshInProgressError`; assert `ValueError("knowledge graph is being refreshed; retry shortly")` from the handler.
4. `test_traverse_validates_depth` — call with `depth=0`; assert `ValueError("depth must be >= 1; got 0")` (handler-level validation, before any DB call).
5. `test_match_validates_k` — same shape for `k`.
6. `test_match_requires_text_or_tagged` — both empty; assert `ValueError("predicate must include at least one of `text` or `tagged`")`.
7. `test_dump_index_default_path_uses_timestamp` — call with `path=None`; assert the destination matches the `.hoplite/<ISO>.index.sqlite` pattern.

Tests #2 and #3 are the load-bearing ones — they verify the domain-error-to-ValueError translation contract. Tests #4–#6 verify handler-level input validation runs before the DB is touched (a failed validation should never open a connection).

## Risks for the implementer

### Hard rules — don't violate these

- **Don't cache a `Graph` instance.** Construct a fresh `_build_graph(db)` per handler call. Caching `_graph` reintroduces the per-process state pattern this refactor exists to remove. Construction is cheap (a couple of field assignments); the connection lifecycle that matters lives inside the impl's `with db.open_*()` blocks per [[docs/notes/db-py-design.md]].
- **Don't import `SqliteGraph` (or `InMemoryGraph`) anywhere except `_build_graph`.** The handler bodies and type annotations depend only on the `Graph` Protocol. Importing the concrete class elsewhere couples `tools.py` to one impl and breaks the swap point.
- **Don't catch domain exceptions inside the `Graph` call.** Let the impl raise; the handler's `try/except` translates at the boundary. Catching inside the impl would force every method on `Graph` to take an error-translation responsibility it doesn't need.
- **Don't leak `sqlite3.Connection` objects across handler calls.** Connections are opened inside `SqliteGraph` methods and closed by the `with` block before the method returns. Holding one across `await` boundaries (if handlers ever become async) would defeat WAL's per-call snapshot model. (Moot for `InMemoryGraph`, which doesn't open connections — but the rule reads the same regardless of impl.)

### Known gaps — accepted, documented, not yet fixed

- **`set_root()` must be called before any handler.** Server bootstrap (see [[docs/notes/server-py-design.md]]) calls it at import time, so day-to-day this never fires. Tests that import `tools` directly need to call `set_root(tmp_path)` in a fixture.
- **`_build_graph` is the only runtime-selection mechanism today.** No env var, no settings flag, no per-condition logic. If a future need arrives (e.g., `HOPLITE_BACKEND=memory` for tests, or auto-select based on corpus size), the logic lands inside `_build_graph` and nothing else changes.

### Future considerations — forward-pointers

- **Async handlers.** FastMCP supports async handler bodies. If a future version of Hoplite goes async (e.g., for streaming responses), the `Graph` methods stay sync — async handlers just `await asyncio.to_thread(graph.search, ...)`. The `Database` per-call model means each thread gets its own connection cleanly.
- **`_escape_fts5_query` move.** Today's logic is correct and well-tested. The mechanical move into `graph_sqlite.py` (or `fts.py`) should preserve the function shape exactly.

### Editorial

- Tools module name stays `tools.py`. Don't rename to `handlers.py` or split. The MCP wire schema and existing tests reference the current names.
- Handler call sites in `server.py` continue to wrap each function with `mcp.tool(...)`. No changes there beyond what step 7 needs.
