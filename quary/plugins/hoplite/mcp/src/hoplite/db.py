"""SQLite connection and transaction plumbing.

Threading contract (read before using these connections off the event loop):
Python's stdlib ``sqlite3`` is synchronous and blocking — there is no async API,
only blocking calls. Connections are also *thread-affine*: ``sqlite3.connect``
defaults to ``check_same_thread=True``, so a connection may only be touched on
the thread that created it.

``open_rw``/``open_ro`` are context managers that open, use, and close a
connection within one ``with`` block, so honor that boundary: the entire ``with``
must run on a single thread. In an async server (FastMCP), that means running the
whole block inside one ``asyncio.to_thread`` / ``anyio.to_thread.run_sync`` call —
never open a connection, ``await`` something that may resume on another thread,
then keep using it. Crossing threads mid-block raises ``sqlite3.ProgrammingError``.

We keep the safe default (``check_same_thread=True``) rather than disabling it:
it's a guardrail, not a limitation. If a connection ever genuinely needs to
outlive a single offloaded call and move between threads, route that path
through a per-connection-thread wrapper (e.g. ``aiosqlite``) instead of turning
the check off — SQLite has no real async to gain, only thread affinity to respect.
"""

import sqlite3
from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import Protocol

_RW_PRAGMAS = (
    "PRAGMA journal_mode = WAL",
    "PRAGMA foreign_keys = ON",
    "PRAGMA synchronous = NORMAL",
    "PRAGMA temp_store = MEMORY",
    "PRAGMA mmap_size = 268435456",
)

# Read-only connections can't write, so foreign_keys enforcement (a write-time
# check) is meaningless here and is deliberately omitted.
_RO_PRAGMAS = (
    "PRAGMA temp_store = MEMORY",
    "PRAGMA mmap_size = 268435456",
)


class IndexNotFoundError(RuntimeError):
    """The index file is missing. Caller should run refresh before retrying."""


class GraphRefreshInProgressError(RuntimeError):
    """A writer holds the lock. Caller should retry shortly."""


class Database(Protocol):
    def open_rw(self) -> AbstractContextManager[sqlite3.Connection]: ...
    def open_ro(self) -> AbstractContextManager[sqlite3.Connection]: ...


class FileDatabase:
    def __init__(self, path: Path) -> None:
        self._path = path

    @contextmanager
    def open_rw(self) -> Generator[sqlite3.Connection, None, None]:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._path, isolation_level=None, timeout=5.0)
        try:
            conn.row_factory = sqlite3.Row
            for pragma in _RW_PRAGMAS:
                conn.execute(pragma)
            # PRAGMA journal_mode does NOT raise when WAL can't be enabled — it
            # leaves the mode unchanged and returns the actual mode. The
            # reader-during-refresh model depends on WAL, so verify it took
            # rather than silently degrade (e.g. on a network filesystem with no
            # shared-memory support).
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            if mode.lower() != "wal":
                raise RuntimeError(
                    f"WAL journal mode required but database is in {mode!r}; "
                    f"the index filesystem may not support WAL shared memory",
                )
            # Writers fail fast. The only contender for the write lock is a long
            # drop+recreate refresh that won't free it in milliseconds, so don't
            # block: BEGIN IMMEDIATE raises at once and write_transaction turns
            # it into GraphRefreshInProgressError for the caller to retry. (The
            # connect timeout above still covers the setup phase.)
            conn.execute("PRAGMA busy_timeout = 0")
            yield conn
        finally:
            conn.close()

    @contextmanager
    def open_ro(self) -> Generator[sqlite3.Connection, None, None]:
        # TODO(pooling): reads connect-read-close, so every request discards the
        # SQLite page cache and tears down the mmap mapping; the 256MB mmap_size
        # and page cache only pay off across a connection's lifetime. A warm,
        # long-lived RO connection (a pool of one is enough — WAL allows many
        # concurrent readers) would keep both hot across requests. Gated on the
        # refresh strategy: safe if refresh is in-place (WAL hands the next read
        # the new snapshot), but a file-swap refresh would strand a pooled
        # connection on the old inode, so revisit when that decision lands.
        #
        # mode=ro only, and deliberately NO immutable flag. immutable=1 would
        # tell SQLite the file never changes and skip WAL recovery — but a
        # refresh mutates this file, and we rely on recovery of an orphaned WAL
        # (verified to work here even with -shm deleted). immutable defaults to
        # 0, so omitting it is the correct state; spelling out immutable=0 is a
        # no-op that only reads as if it did something.
        # Consequence of plain mode=ro on a WAL database: the process must still
        # be able to open the -shm wal-index, so a genuinely read-only
        # filesystem would fail to open here.
        uri = f"{self._path.as_uri()}?mode=ro"
        try:
            conn = sqlite3.connect(uri, isolation_level=None, timeout=5.0, uri=True)
        except sqlite3.OperationalError as e:
            # Classify the failure after the fact rather than checking existence
            # first — that check-then-open had a TOCTOU window against refresh.
            if not self._path.exists():
                raise IndexNotFoundError(
                    f"no Hoplite index at {self._path}; call refresh to build it",
                ) from e
            raise
        try:
            conn.row_factory = sqlite3.Row
            for pragma in _RO_PRAGMAS:
                conn.execute(pragma)
            yield conn
        finally:
            conn.close()


@contextmanager
def write_transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Connection, None, None]:
    try:
        conn.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as e:
        # Mask to the primary result code so extended codes still register as
        # busy: SQLITE_BUSY_SNAPSHOT (517), SQLITE_BUSY_RECOVERY (261), etc.
        if (e.sqlite_errorcode & 0xFF) == sqlite3.SQLITE_BUSY:
            raise GraphRefreshInProgressError(
                "knowledge graph is being refreshed; retry shortly",
            ) from e
        raise
    try:
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        # A failing ROLLBACK (e.g. "no transaction is active") must not bury the
        # original exception — swallow it so the real cause is what propagates.
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise
