import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

from hoplite.db import (
    Database,
    FileDatabase,
    GraphRefreshInProgressError,
    IndexNotFoundError,
    write_transaction,
)


class _BeginFailingConn:
    """Proxy that raises a chosen error on BEGIN IMMEDIATE and forwards otherwise."""

    def __init__(self, real: sqlite3.Connection, fail_with: sqlite3.OperationalError) -> None:
        self._real = real
        self._fail_with = fail_with

    def execute(self, sql: str) -> sqlite3.Cursor:
        if sql == "BEGIN IMMEDIATE":
            raise self._fail_with
        return self._real.execute(sql)


_db_check: Database = FileDatabase(Path("x"))


def _pragma(conn: sqlite3.Connection, name: str) -> object:
    row = conn.execute(f"PRAGMA {name}").fetchone()
    return row[0]


def test_open_rw_creates_parent_directory(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "deeper" / "index.sqlite"
    db = FileDatabase(path)
    with db.open_rw():
        pass
    assert path.parent.is_dir()
    assert path.exists()


def test_open_rw_applies_pragmas(tmp_path: Path) -> None:
    db = FileDatabase(tmp_path / "idx.sqlite")
    with db.open_rw() as conn:
        assert _pragma(conn, "journal_mode") == "wal"
        assert _pragma(conn, "foreign_keys") == 1
        assert _pragma(conn, "synchronous") == 1
        assert _pragma(conn, "temp_store") == 2
        assert _pragma(conn, "mmap_size") == 268435456


def test_open_ro_applies_pragmas(tmp_path: Path) -> None:
    db = FileDatabase(tmp_path / "idx.sqlite")
    with db.open_rw() as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
    with db.open_ro() as conn:
        # foreign_keys is deliberately NOT set on read-only connections: it's a
        # write-time check, meaningless when the connection can't write. Default 0.
        assert _pragma(conn, "foreign_keys") == 0
        assert _pragma(conn, "temp_store") == 2
        assert _pragma(conn, "mmap_size") == 268435456


def test_open_ro_missing_file_raises(tmp_path: Path) -> None:
    db = FileDatabase(tmp_path / "missing.sqlite")
    with pytest.raises(IndexNotFoundError, match="no Hoplite index at") as exc_info, db.open_ro():
        pass
    msg = str(exc_info.value)
    assert str(tmp_path / "missing.sqlite") in msg
    assert "call refresh" in msg


def test_open_ro_uri_form_works(tmp_path: Path) -> None:
    db = FileDatabase(tmp_path / "idx.sqlite")
    with db.open_rw() as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
        conn.execute("INSERT INTO t VALUES (42)")
    with db.open_ro() as conn:
        row = conn.execute("SELECT x FROM t").fetchone()
        assert row[0] == 42


_CRASH_WRITER = """
import os, sys
from pathlib import Path
from hoplite.db import FileDatabase

db = FileDatabase(Path(sys.argv[1]))
cm = db.open_rw()            # hold the cm so GC can't run the generator's close
conn = cm.__enter__()
conn.execute("CREATE TABLE IF NOT EXISTS t (x INTEGER)")
conn.execute(f"INSERT INTO t VALUES ({int(sys.argv[2])})")
os._exit(0)                  # die without a clean close: leaves an orphaned WAL
"""


def _crash_write(dbpath: Path, value: int) -> None:
    """Write a committed row, then hard-exit before checkpoint.

    Autocommit lands the row in the -wal; ``os._exit`` skips the clean close
    (and its checkpoint), leaving an orphaned WAL the next opener must recover.
    """
    result = subprocess.run(
        [sys.executable, "-c", _CRASH_WRITER, str(dbpath), str(value)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("delete_shm", [False, True])
def test_open_ro_recovers_orphaned_wal(tmp_path: Path, delete_shm: bool) -> None:
    """A genuinely read-only connection recovers a crash-orphaned WAL.

    The query path opens ``mode=ro`` against a live WAL database. If a writer
    crashes mid-refresh, committed frames sit in the -wal that the main db file
    has never seen. ``mode=ro`` restricts writes to the *database*, not to the
    WAL-recovery sidecar files, so recovery still works as long as the directory
    is writable (it always is — the writer owns ``.hoplite/``). Verified both
    with the -shm present and deleted, the latter forcing shm recreation.
    """
    path = tmp_path / "idx.sqlite"
    _crash_write(path, 4242)

    # The row lives ONLY in the WAL: reading the main file alone can't see it.
    # immutable=1 tells SQLite to ignore the WAL and read the base file as-is.
    main_only = sqlite3.connect(f"{path.as_uri()}?immutable=1", uri=True)
    try:
        with pytest.raises(sqlite3.OperationalError, match="no such table"):
            main_only.execute("SELECT x FROM t").fetchall()
    finally:
        main_only.close()

    if delete_shm:
        (tmp_path / "idx.sqlite-shm").unlink()

    db = FileDatabase(path)
    with db.open_ro() as conn:
        # The connection is genuinely read-only...
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("INSERT INTO t VALUES (1)")
        # ...yet it replayed the orphaned WAL.
        assert conn.execute("SELECT x FROM t").fetchone()[0] == 4242


def test_open_rw_independent_connections_see_committed_data(tmp_path: Path) -> None:
    db = FileDatabase(tmp_path / "idx.sqlite")
    with db.open_rw() as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
        with write_transaction(conn):
            conn.execute("INSERT INTO t VALUES (7)")
    with db.open_rw() as conn:
        row = conn.execute("SELECT x FROM t").fetchone()
        assert row[0] == 7


def test_write_transaction_commit_on_clean_exit(tmp_path: Path) -> None:
    db = FileDatabase(tmp_path / "idx.sqlite")
    with db.open_rw() as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
        with write_transaction(conn):
            conn.execute("INSERT INTO t VALUES (1)")
    with db.open_rw() as conn:
        count = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
        assert count == 1


def test_write_transaction_rollback_on_exception(tmp_path: Path) -> None:
    db = FileDatabase(tmp_path / "idx.sqlite")
    with db.open_rw() as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
    with (
        db.open_rw() as conn,
        pytest.raises(RuntimeError, match="boom"),
        write_transaction(conn),
    ):
        conn.execute("INSERT INTO t VALUES (1)")
        raise RuntimeError("boom")
    with db.open_rw() as conn:
        count = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
        assert count == 0


class _BusyError(sqlite3.OperationalError):
    @property
    def sqlite_errorcode(self) -> int:  # type: ignore[override]
        return sqlite3.SQLITE_BUSY


class _GenericOperationalError(sqlite3.OperationalError):
    @property
    def sqlite_errorcode(self) -> int:  # type: ignore[override]
        return sqlite3.SQLITE_ERROR


def test_write_transaction_translates_sqlite_busy(tmp_path: Path) -> None:
    db = FileDatabase(tmp_path / "idx.sqlite")
    with db.open_rw() as conn:
        proxy = _BeginFailingConn(conn, _BusyError("database is locked"))
        with (
            pytest.raises(
                GraphRefreshInProgressError, match="being refreshed; retry shortly"
            ) as exc_info,
            write_transaction(cast(sqlite3.Connection, proxy)),
        ):
            pass
        assert isinstance(exc_info.value.__cause__, sqlite3.OperationalError)


def test_write_transaction_propagates_non_busy_operational_error(tmp_path: Path) -> None:
    db = FileDatabase(tmp_path / "idx.sqlite")
    with db.open_rw() as conn:
        proxy = _BeginFailingConn(conn, _GenericOperationalError("some other error"))
        with (
            pytest.raises(sqlite3.OperationalError, match="some other error"),
            write_transaction(cast(sqlite3.Connection, proxy)),
        ):
            pass


def test_open_rw_writer_fails_fast(tmp_path: Path) -> None:
    """Writers set busy_timeout=0 so BEGIN IMMEDIATE raises at once during a refresh."""
    db = FileDatabase(tmp_path / "idx.sqlite")
    with db.open_rw() as conn:
        assert _pragma(conn, "busy_timeout") == 0


class _BusySnapshotError(sqlite3.OperationalError):
    @property
    def sqlite_errorcode(self) -> int:  # type: ignore[override]
        return 517  # SQLITE_BUSY_SNAPSHOT = SQLITE_BUSY | (1 << 9)


def test_write_transaction_translates_extended_busy_code(tmp_path: Path) -> None:
    """The & 0xFF mask must catch extended busy codes, not just the primary one."""
    db = FileDatabase(tmp_path / "idx.sqlite")
    with db.open_rw() as conn:
        proxy = _BeginFailingConn(conn, _BusySnapshotError("snapshot is busy"))
        with (
            pytest.raises(GraphRefreshInProgressError, match="being refreshed"),
            write_transaction(cast(sqlite3.Connection, proxy)),
        ):
            pass


class _RollbackFailingConn:
    """Forwards everything except ROLLBACK, which raises (e.g. no active txn)."""

    def __init__(self, real: sqlite3.Connection) -> None:
        self._real = real

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Cursor:
        if sql == "ROLLBACK":
            raise sqlite3.OperationalError("cannot rollback - no transaction is active")
        return self._real.execute(sql, params)


def test_write_transaction_rollback_failure_does_not_mask_original(tmp_path: Path) -> None:
    """A failing ROLLBACK must not bury the exception that caused the rollback."""
    db = FileDatabase(tmp_path / "idx.sqlite")
    with db.open_rw() as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
        proxy = _RollbackFailingConn(conn)
        with (
            pytest.raises(RuntimeError, match="boom"),
            write_transaction(cast(sqlite3.Connection, proxy)),
        ):
            raise RuntimeError("boom")


class _FakeCursor:
    def __init__(self, row: tuple[object, ...]) -> None:
        self._row = row

    def fetchone(self) -> tuple[object, ...]:
        return self._row


class _NonWalConn:
    """Wraps a real connection but reports a non-WAL mode on journal_mode read-back."""

    def __init__(self, real: sqlite3.Connection) -> None:
        self._real = real

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> object:
        if sql == "PRAGMA journal_mode":
            return _FakeCursor(("delete",))
        return self._real.execute(sql, params)

    @property
    def row_factory(self) -> object:
        return self._real.row_factory

    @row_factory.setter
    def row_factory(self, value: object) -> None:
        self._real.row_factory = value  # type: ignore[assignment]

    def close(self) -> None:
        self._real.close()


def test_open_rw_raises_when_wal_not_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """WAL is verified, not assumed: a silent fallback to another journal mode raises."""
    db = FileDatabase(tmp_path / "idx.sqlite")
    real_connect = sqlite3.connect

    def fake_connect(*args: object, **kwargs: object) -> object:
        return _NonWalConn(real_connect(*args, **kwargs))  # type: ignore[arg-type]

    monkeypatch.setattr(sqlite3, "connect", fake_connect)
    with pytest.raises(RuntimeError, match="WAL journal mode required"), db.open_rw():
        pass
