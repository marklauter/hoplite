import sqlite3
from pathlib import Path
from typing import cast

import pytest

from hoplite import migrations
from hoplite.migrations import (  # pyright: ignore[reportPrivateUsage]
    _EXPECTED_TABLES,
    SCHEMA,
    apply,
)

_EXPECTED_INDEXES = (
    "idx_node_property_key_value",
    "idx_edge_kind_src",
    "idx_edge_kind_dst",
    "idx_edge_property_key_value",
)


class _ExecScriptRaisingConn:
    """Proxy that raises a chosen error on executescript and forwards otherwise."""

    def __init__(self, real: sqlite3.Connection, raise_with: sqlite3.OperationalError) -> None:
        self._real = real
        self._raise_with = raise_with

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Cursor:
        return self._real.execute(sql, params)

    def executescript(self, _sql: str) -> sqlite3.Cursor:
        raise self._raise_with


def _names_of(conn: sqlite3.Connection, kind: str) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = ?", (kind,)
    ).fetchall()
    return {r[0] for r in rows}


def test_apply_creates_all_expected_tables() -> None:
    conn = sqlite3.connect(":memory:")
    apply(conn)
    tables = _names_of(conn, "table")
    indexes = _names_of(conn, "index")
    for name in _EXPECTED_TABLES:
        assert name in tables, f"missing table {name}"
    for name in _EXPECTED_INDEXES:
        assert name in indexes, f"missing index {name}"


def test_apply_is_idempotent() -> None:
    conn = sqlite3.connect(":memory:")
    apply(conn)
    tables_first = _names_of(conn, "table")
    apply(conn)
    tables_second = _names_of(conn, "table")
    assert tables_first == tables_second


def test_apply_raises_on_partial_schema() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE node (id INTEGER PRIMARY KEY)")
    with pytest.raises(sqlite3.OperationalError, match="already exists"):
        apply(conn)


def test_apply_race_recovery_succeeds_when_schema_present() -> None:
    conn = sqlite3.connect(":memory:")
    for name in _EXPECTED_TABLES:
        conn.execute(f"CREATE TABLE {name} (x INTEGER)")
    # Drop one so _schema_present returns False before executescript runs,
    # then re-create it so post-error _schema_present returns True.
    conn.execute("DROP TABLE node")
    proxy = _ExecScriptRaisingConn(
        conn, sqlite3.OperationalError("table node already exists")
    )

    def fake_executescript(_sql: str) -> sqlite3.Cursor:
        conn.execute("CREATE TABLE node (x INTEGER)")
        raise sqlite3.OperationalError("table node already exists")

    proxy.executescript = fake_executescript  # type: ignore[assignment]
    apply(cast(sqlite3.Connection, proxy))


def test_apply_race_recovery_reraises_when_schema_absent() -> None:
    conn = sqlite3.connect(":memory:")
    proxy = _ExecScriptRaisingConn(
        conn, sqlite3.OperationalError("table node already exists")
    )
    with pytest.raises(sqlite3.OperationalError, match="already exists"):
        apply(cast(sqlite3.Connection, proxy))


def test_apply_does_not_swallow_non_already_exists_errors() -> None:
    conn = sqlite3.connect(":memory:")
    for name in _EXPECTED_TABLES:
        conn.execute(f"CREATE TABLE {name} (x INTEGER)")
    conn.execute("DROP TABLE node")
    proxy = _ExecScriptRaisingConn(conn, sqlite3.OperationalError("disk I/O error"))

    def fake_executescript(_sql: str) -> sqlite3.Cursor:
        conn.execute("CREATE TABLE node (x INTEGER)")
        raise sqlite3.OperationalError("disk I/O error")

    proxy.executescript = fake_executescript  # type: ignore[assignment]
    with pytest.raises(sqlite3.OperationalError, match="disk I/O error"):
        apply(cast(sqlite3.Connection, proxy))


def test_schema_constant_matches_file() -> None:
    on_disk = (Path(migrations.__file__).parent / "schema.sql").read_text(encoding="utf-8")
    assert on_disk == SCHEMA


def test_node_uri_is_case_insensitive_unique() -> None:
    conn = sqlite3.connect(":memory:")
    apply(conn)
    conn.execute("INSERT INTO node (uri, resolved) VALUES ('Foo.md', 1)")
    # COLLATE NOCASE makes uri identity case-insensitive, so this collides.
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO node (uri, resolved) VALUES ('FOO.MD', 1)")


def test_property_tables_are_without_rowid() -> None:
    conn = sqlite3.connect(":memory:")
    apply(conn)
    # WITHOUT ROWID tables expose no implicit rowid column.
    for table in ("node_property", "edge_property"):
        with pytest.raises(sqlite3.OperationalError, match="no such column"):
            conn.execute(f"SELECT rowid FROM {table}")
