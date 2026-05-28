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
            yield conn
        finally:
            conn.close()

    @contextmanager
    def open_ro(self) -> Generator[sqlite3.Connection, None, None]:
        if not self._path.exists():
            raise IndexNotFoundError(f"no Hoplite index at {self._path}; call refresh to build it")
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
def write_transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Connection, None, None]:
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
