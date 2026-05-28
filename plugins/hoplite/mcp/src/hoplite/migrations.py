import sqlite3
from pathlib import Path
from typing import Final

SCHEMA: Final = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")

_EXPECTED_TABLES: Final = ("document", "document_property", "edge", "edge_property", "fts")


def apply(conn: sqlite3.Connection) -> None:
    """Apply the schema to `conn` if not already present. Idempotent.

    Must be called outside any explicit transaction — `executescript`
    unconditionally commits the current transaction before running the
    script, which would prematurely close any outer `write_transaction`.

    Race-tolerant: if another process applies the schema between our
    presence check and our executescript, the resulting OperationalError
    is swallowed only if the error text matches "already exists" AND the
    post-error state shows the full multi-table schema present.
    """
    if _schema_present(conn):
        return
    try:
        conn.executescript(SCHEMA)
    except sqlite3.OperationalError as e:
        if "already exists" in str(e) and _schema_present(conn):
            return
        raise


def _schema_present(conn: sqlite3.Connection) -> bool:
    placeholders = ",".join("?" * len(_EXPECTED_TABLES))
    sql = (
        f"SELECT COUNT(*) FROM sqlite_master "
        f"WHERE type='table' AND name IN ({placeholders})"
    )
    row = conn.execute(sql, _EXPECTED_TABLES).fetchone()
    return row[0] == len(_EXPECTED_TABLES)
