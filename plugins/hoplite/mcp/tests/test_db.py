import sqlite3
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
        assert _pragma(conn, "foreign_keys") == 1
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
