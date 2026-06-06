---
title: db.py — Database interface and FileDatabase implementation
summary: `db.py` exposes a `Database` protocol with `open_rw` and `open_ro` methods that yield fresh `sqlite3.Connection` instances per call. `FileDatabase` is the day-one implementation; the interface is the seam for a future pool.
tags: [note, sqlite, design, hoplite, architecture]
created: 2026-05-27
document:
  status: design
---

# db.py — Database interface and FileDatabase implementation

`db.py` exposes a `Database` protocol with `open_rw` and `open_ro` methods that yield fresh `sqlite3.Connection` instances per call. `FileDatabase` is the day-one implementation; the interface is the seam for a future pool.

Sibling design notes: [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale and trigger; [[docs/notes/db-refactor.md]] for the broader refactor plan. This note covers `db.py` alone.

## Interface — `Database`

A `typing.Protocol` with two methods, both context managers that yield a fresh connection per call. Neither method knows anything about the schema; that responsibility lives in `migrations.py`.

```python
class Database(Protocol):
    def open_rw(self) -> ContextManager[sqlite3.Connection]: ...
    def open_ro(self) -> ContextManager[sqlite3.Connection]: ...
```

- `open_rw` — write path. Used only by `refresh`. Creates the file if missing.
- `open_ro` — read path. Used by every query tool. Errors cleanly if the file doesn't exist.

Callers depend on `Database`, not on a concrete class. Tool handlers receive an instance via the MCP server's closure; no global state, no module-level connection.

## Implementation — `FileDatabase`

`FileDatabase(path: Path)` is the day-one implementation. Each method opens a fresh `sqlite3.Connection`, applies the appropriate PRAGMAs, sets `row_factory = sqlite3.Row`, yields, and closes on `with` exit.

`open_rw` opens the file with create-if-missing semantics — the default of `sqlite3.connect(path)`. Before opening, it ensures the parent directory exists via `path.parent.mkdir(parents=True, exist_ok=True)`; the `.hoplite/` directory is created on first use, no manual setup needed.

`open_ro` opens with the URI form, built via `path.as_uri()` so Windows paths produce the correct `file:///D:/...` shape and POSIX paths produce `file:///home/...`. The query string `?mode=ro&immutable=0` appends to the URI. SQLite errors if the file doesn't exist; `FileDatabase.open_ro` catches that and re-raises as `IndexNotFoundError` (loud is right; see the "fail loud" decision in [[docs/notes/db-refactor.md]]).

Caller shape:

```python
with db.open_ro() as conn:
    rows = conn.execute("SELECT uri FROM node").fetchall()
```

Connection lifetime equals the `with` block. No caching, no sharing, no thread-safety concerns. Two overlapping tool calls get independent connections that don't block each other under WAL.

## PRAGMAs

PRAGMAs apply per connection, except `journal_mode = WAL` which is persistent per database.

Read-write path (`open_rw`), in order:

1. `PRAGMA journal_mode = WAL` — no-op if already WAL; idempotent and cheap, so no separate flag needed.
2. `PRAGMA foreign_keys = ON` — enables FK constraint enforcement. Off by default for backward compat.
3. `PRAGMA synchronous = NORMAL` — fewer fsync calls than `FULL`; durable under WAL, faster.
4. `PRAGMA temp_store = MEMORY` — sort buffers and temp tables in RAM, not tmpdir.
5. `PRAGMA mmap_size = 268435456` — 256 MiB of memory-mapped I/O. Reads bypass `read()` syscalls.

Read-only path (`open_ro`):

1. `PRAGMA foreign_keys = ON` — harmless on a read-only connection but keeps `EXPLAIN QUERY PLAN` honest.
2. `PRAGMA temp_store = MEMORY`.
3. `PRAGMA mmap_size = 268435456`.

`cache_size` left at the default 2000 pages (~8 MiB per connection). Tune later if profiling demands it.

## Transactions and isolation

Both `open_rw` and `open_ro` construct connections with `isolation_level=None` — autocommit mode. Callers manage transactions explicitly. Reference: [SQLite isolation model](https://sqlite.org/isolation.html).

Python's stdlib `sqlite3` defaults to an "implicit transaction on first DML" mode that interferes with explicit `BEGIN IMMEDIATE` — calling it on a connection where Python has already issued an implicit `BEGIN` raises "cannot start a transaction within a transaction." `isolation_level=None` turns that off.

Caller protocol under autocommit:

- `refresh` and `migrations.apply` issue `BEGIN IMMEDIATE` ... `COMMIT` (or `ROLLBACK` on exception) themselves. `BEGIN IMMEDIATE` grabs the write lock upfront so concurrent writers serialize cleanly instead of racing and failing partway through.
- Query tools issue plain `SELECT` statements with no transaction wrapping. Each statement autocommits (a no-op for reads).

Under WAL, this gives:

- Snapshot isolation across connections — a read transaction sees a frozen snapshot from start; concurrent writes are invisible to that reader.
- Serialized writers — `BEGIN IMMEDIATE` on connection B blocks until connection A's writer commits.
- No isolation within one connection — sequential statements see each other's uncommitted changes. Fine for our single-writer walker.

## Domain errors

Two domain exceptions live in `db.py` to translate raw `sqlite3.OperationalError` into actionable messages the agent can read.

### `IndexNotFoundError`

```python
class IndexNotFoundError(RuntimeError):
    """The index file is missing. Caller should run refresh before retrying."""
```

Raised by `FileDatabase.open_ro` when the file doesn't exist. Message names the path and the remediation: `"no Hoplite index at <path>; call refresh to build it"`. Catching it doesn't require a `sqlite3` import.

### `GraphRefreshInProgressError`

```python
class GraphRefreshInProgressError(RuntimeError):
    """A writer holds the lock. Caller should retry shortly."""
```

Raised when `BEGIN IMMEDIATE` returns `SQLITE_BUSY` after the busy_timeout expires — another `refresh` is in flight. Message: `"knowledge graph is being refreshed; retry shortly"`. Translation happens at the call sites that issue `BEGIN IMMEDIATE` (the walker and `migrations.apply`): catch `sqlite3.OperationalError` where the SQLite error code is `SQLITE_BUSY`, re-raise as the domain error.

busy_timeout stays at Python's default 5 seconds (`sqlite3.connect(timeout=5.0)`). Under WAL, readers never block on writers, so this only fires when two refreshes race — rare given agents start manually, and 5 seconds is enough cushion to absorb the typical refresh window's commit phase.

## Helper — `write_transaction`

Context-manager helper in `db.py`. Centralizes the `BEGIN IMMEDIATE` / `COMMIT` / `ROLLBACK` protocol and translates `SQLITE_BUSY` into `GraphRefreshInProgressError`. Callers (the walker, `migrations.apply`) wrap their work in it instead of issuing the transaction commands by hand.

```python
from contextlib import contextmanager
from collections.abc import Iterator
import sqlite3

@contextmanager
def write_transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        conn.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_BUSY:
            raise GraphRefreshInProgressError(
                "knowledge graph is being refreshed; retry shortly"
            ) from e
        raise
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
```

Caller shape:

```python
with db.open_rw() as conn:
    with write_transaction(conn):
        conn.execute("DELETE FROM node")
        # ... walker bulk inserts ...
```

Two nested `with` blocks compose cleanly. `open_rw` owns connection lifecycle (open/close). `write_transaction` owns transaction lifecycle (BEGIN/COMMIT/ROLLBACK + busy translation). Each helper has one job; the caller composes them.

Note: `OperationalError.sqlite_errorcode` requires Python 3.11+. The current `pyproject.toml` declares `requires-python = ">=3.10"`; bump to `>=3.11` as part of this refactor (the bootstrapped venv already runs 3.14, so no production impact). Alternative if 3.10 must stay: fall back to `"database is locked" in str(e)` message-sniffing — workable but locale-sensitive.

## Why per-call open

A shared connection would chokepoint concurrent requests: one transaction per connection, and stdlib `sqlite3` defaults to `check_same_thread=True`, which would crash outright under FastMCP's concurrent handler model. Per-call open under WAL is cheap: pragma application is microseconds, and `mmap_size = 256MB` keeps most reads in the OS page cache across connection close.

The `Database` interface is the seam for future optimization. A `PooledDatabase` that satisfies the same protocol slots in without changes to tool handlers or `refresh`. See the lock-vs-pool tradeoff in [[docs/notes/db-refactor.md]] for the future direction.

## Module skeleton

Full `db.py` shape, consolidating the prose decisions above. The implementation agent should mirror this structure; deviations are the agent's call but should be justified.

```python
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol
import sqlite3


_RW_PRAGMAS = (
    "PRAGMA journal_mode = WAL",
    "PRAGMA foreign_keys = ON",
    "PRAGMA synchronous = NORMAL",
    "PRAGMA temp_store = MEMORY",
    "PRAGMA mmap_size = 268435456",
)

_RO_PRAGMAS = (
    "PRAGMA foreign_keys = ON",
    "PRAGMA temp_store = MEMORY",
    "PRAGMA mmap_size = 268435456",
)


class IndexNotFoundError(RuntimeError):
    """The index file is missing. Caller should run refresh before retrying."""


class GraphRefreshInProgressError(RuntimeError):
    """A writer holds the lock. Caller should retry shortly."""


class Database(Protocol):
    def open_rw(self) -> "AbstractContextManager[sqlite3.Connection]": ...
    def open_ro(self) -> "AbstractContextManager[sqlite3.Connection]": ...


class FileDatabase:
    def __init__(self, path: Path) -> None:
        self._path = path

    @contextmanager
    def open_rw(self) -> Iterator[sqlite3.Connection]:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._path, isolation_level=None, timeout=5.0)
        try:
            conn.row_factory = sqlite3.Row
            for pragma in _RW_PRAGMAS:
                conn.execute(pragma)
            yield conn
        finally:
            conn.close()

    @contextmanager
    def open_ro(self) -> Iterator[sqlite3.Connection]:
        if not self._path.exists():
            raise IndexNotFoundError(
                f"no Hoplite index at {self._path}; call refresh to build it"
            )
        uri = f"{self._path.as_uri()}?mode=ro&immutable=0"
        conn = sqlite3.connect(uri, isolation_level=None, timeout=5.0, uri=True)
        try:
            conn.row_factory = sqlite3.Row
            for pragma in _RO_PRAGMAS:
                conn.execute(pragma)
            yield conn
        finally:
            conn.close()


@contextmanager
def write_transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        conn.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_BUSY:
            raise GraphRefreshInProgressError(
                "knowledge graph is being refreshed; retry shortly"
            ) from e
        raise
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
```

`AbstractContextManager` import: `from contextlib import AbstractContextManager` — included at the top of the real module. Omitted from the skeleton above for brevity since it's only referenced in the Protocol's return type annotation.

## Tests

Tests run against `:memory:`.

- `FileDatabase.open_rw` against a `:memory:`-backed instance: assert each PRAGMA is set, that two sequential `with` blocks produce independent connections, and that both see the same data after the first commits.
- `FileDatabase.open_ro` needs a real temp file — URI semantics like `file:...?mode=ro` aren't available on `:memory:`. This is the one acceptable exception to the "tests use `:memory:`" rule from the refactor plan.
- `FileDatabase.open_ro` against a missing-file path raises `IndexNotFoundError` with the expected message.
- `GraphRefreshInProgressError` test: two threads both reach `write_transaction(conn)` against the same file; the second thread raises the domain error after the busy timeout.
- `write_transaction` rollback test: an exception raised inside the `with` block triggers `ROLLBACK` (no rows persist) and the original exception re-propagates.
- The `Database` protocol is structural; no test exists for the protocol itself. Any class that satisfies the methods passes.
