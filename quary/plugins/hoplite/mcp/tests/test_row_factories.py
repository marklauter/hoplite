import json
import sqlite3

import pytest

from hoplite import migrations
from hoplite.models import Document, Edge
from hoplite.row_factories import (
    parse_tags,
    row_to_document,
    row_to_document_with_id,
    row_to_edge,
    row_to_hit,
    row_to_traversal_hit,
)


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(migrations.SCHEMA)
    return c


def _populate_document(
    conn: sqlite3.Connection,
    *,
    id: int,
    path: str,
    resolved: bool = True,
    content_hash: str | None = None,
    minhash: bytes | None = None,
) -> None:
    conn.execute(
        "INSERT INTO document (id, path, resolved, content_hash, minhash) VALUES (?, ?, ?, ?, ?)",
        (id, path, int(resolved), content_hash, minhash),
    )


def _populate_property(conn: sqlite3.Connection, *, id: int, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO document_property (id, key, value) VALUES (?, ?, ?)",
        (id, key, value),
    )


def _populate_edge(
    conn: sqlite3.Connection,
    *,
    id: int,
    src: int,
    dst: int,
    kind: str = "mentions",
    confidence: float = 1.0,
) -> None:
    conn.execute(
        "INSERT INTO edge (id, src, dst, kind, confidence) VALUES (?, ?, ?, ?, ?)",
        (id, src, dst, kind, confidence),
    )


def _populate_fts(
    conn: sqlite3.Connection,
    *,
    rowid: int,
    path: str,
    title: str = "",
    summary: str = "",
    body: str = "",
) -> None:
    conn.execute(
        "INSERT INTO fts (rowid, path, title, summary, body) VALUES (?, ?, ?, ?, ?)",
        (rowid, path, title, summary, body),
    )


_HIT_QUERY = """
    SELECT d.path,
           fts.summary,
           (SELECT json_group_array(value) FROM (
              SELECT value FROM document_property
              WHERE id = d.id AND key = 'tags' ORDER BY rowid
            )) AS tags,
           bm25(fts) AS score
    FROM fts
    JOIN document d ON d.id = fts.rowid
    WHERE fts MATCH 'body'
"""


def test_row_to_document_projects_all_fields(conn: sqlite3.Connection) -> None:
    _populate_document(
        conn,
        id=1,
        path="docs/notes/foo.md",
        resolved=True,
        content_hash="abc123",
        minhash=b"\x01\x02\x03",
    )
    row = conn.execute("SELECT * FROM document WHERE id = 1").fetchone()
    doc = row_to_document(row)
    assert doc == Document(
        path="docs/notes/foo.md",
        resolved=True,
        content_hash="abc123",
        minhash=b"\x01\x02\x03",
    )


def test_row_to_document_handles_null_optional_fields(conn: sqlite3.Connection) -> None:
    _populate_document(conn, id=1, path="ghost/bar", resolved=False)
    row = conn.execute("SELECT * FROM document WHERE id = 1").fetchone()
    doc = row_to_document(row)
    assert doc.content_hash is None
    assert doc.minhash is None


def test_row_to_document_widens_resolved_to_bool(conn: sqlite3.Connection) -> None:
    _populate_document(conn, id=1, path="a.md", resolved=True)
    _populate_document(conn, id=2, path="b.md", resolved=False)
    rows = conn.execute("SELECT * FROM document ORDER BY id").fetchall()
    docs = [row_to_document(r) for r in rows]
    assert docs[0].resolved is True
    assert docs[1].resolved is False


def test_row_to_document_with_id_composes_on_base(conn: sqlite3.Connection) -> None:
    _populate_document(
        conn, id=5, path="x.md", resolved=True, content_hash="h", minhash=b"m"
    )
    row = conn.execute("SELECT * FROM document WHERE id = 5").fetchone()
    assert row_to_document_with_id(row) == (5, row_to_document(row))


def test_row_to_edge_projects_path_columns_not_id(conn: sqlite3.Connection) -> None:
    _populate_document(conn, id=1, path="src.md")
    _populate_document(conn, id=2, path="dst.md")
    _populate_edge(conn, id=1, src=1, dst=2, kind="mentions", confidence=0.9)
    row = conn.execute(
        """
        SELECT e.kind, e.confidence,
               src_doc.path AS src_path,
               dst_doc.path AS dst_path
        FROM edge e
        JOIN document src_doc ON src_doc.id = e.src
        JOIN document dst_doc ON dst_doc.id = e.dst
        """
    ).fetchone()
    edge = row_to_edge(row)
    assert edge == Edge(src="src.md", dst="dst.md", kind="mentions", confidence=0.9)


def test_row_to_edge_raises_indexerror_on_missing_join(conn: sqlite3.Connection) -> None:
    _populate_document(conn, id=1, path="src.md")
    _populate_document(conn, id=2, path="dst.md")
    _populate_edge(conn, id=1, src=1, dst=2)
    row = conn.execute("SELECT src, dst, kind, confidence FROM edge").fetchone()
    with pytest.raises(IndexError):
        row_to_edge(row)


def test_row_to_edge_does_not_guard_miswritten_alias(conn: sqlite3.Connection) -> None:
    _populate_document(conn, id=1, path="src.md")
    _populate_document(conn, id=2, path="dst.md")
    _populate_edge(conn, id=1, src=1, dst=2)
    row = conn.execute(
        "SELECT e.src AS src_path, e.dst AS dst_path, e.kind, e.confidence FROM edge e"
    ).fetchone()
    edge = row_to_edge(row)
    assert isinstance(edge.src, int)
    assert isinstance(edge.dst, int)


def test_row_to_hit_returns_tags_sorted_ascending(conn: sqlite3.Connection) -> None:
    _populate_document(conn, id=1, path="a.md")
    # Insert in reverse-alphabetical order so the assertion meaningfully
    # exercises the sort rather than coincidentally matching insertion order.
    _populate_property(conn, id=1, key="tags", value="note")
    _populate_property(conn, id=1, key="tags", value="hoplite")
    _populate_fts(conn, rowid=1, path="a.md", title="A", summary="sum", body="body")
    row = conn.execute(_HIT_QUERY).fetchone()
    hit = row_to_hit(row)
    assert hit.tags == ["hoplite", "note"]


def test_row_to_hit_handles_empty_tags(conn: sqlite3.Connection) -> None:
    _populate_document(conn, id=1, path="a.md")
    _populate_fts(conn, rowid=1, path="a.md", title="A", summary="s", body="body")
    row = conn.execute(_HIT_QUERY).fetchone()
    hit = row_to_hit(row)
    assert hit.tags == []


def test_row_to_hit_handles_null_summary(conn: sqlite3.Connection) -> None:
    _populate_document(conn, id=1, path="a.md")
    row = conn.execute(
        "SELECT path, NULL AS summary, '[]' AS tags, 0.0 AS score FROM document WHERE id = 1"
    ).fetchone()
    hit = row_to_hit(row)
    assert hit.summary == ""


def test_parse_tags_coerces_non_string_elements() -> None:
    assert parse_tags("[1, 2, 3]") == ["1", "2", "3"]


def test_parse_tags_propagates_malformed_json() -> None:
    with pytest.raises(json.JSONDecodeError):
        parse_tags("not-json")


def test_row_to_traversal_hit_copies_via_edges(conn: sqlite3.Connection) -> None:
    _populate_document(conn, id=1, path="a.md")
    row = conn.execute(
        "SELECT path, 'sum' AS summary, '[]' AS tags, 1 AS distance FROM document WHERE id = 1"
    ).fetchone()
    edges = [Edge(src="a.md", dst="b.md", kind="mentions", confidence=1.0)]
    hit = row_to_traversal_hit(row, edges)
    assert hit.via_edges is not edges
    edges.clear()
    assert len(hit.via_edges) == 1


def test_row_to_traversal_hit_preserves_edge_order(conn: sqlite3.Connection) -> None:
    _populate_document(conn, id=1, path="a.md")
    row = conn.execute(
        "SELECT path, 'sum' AS summary, '[]' AS tags, 1 AS distance FROM document WHERE id = 1"
    ).fetchone()
    e1 = Edge(src="a.md", dst="b.md", kind="mentions", confidence=1.0)
    e2 = Edge(src="a.md", dst="c.md", kind="cites", confidence=1.0)
    e3 = Edge(src="a.md", dst="d.md", kind="related", confidence=0.5)
    hit = row_to_traversal_hit(row, [e1, e2, e3])
    assert hit.via_edges == [e1, e2, e3]


def test_row_to_traversal_hit_returns_tags_sorted_ascending(conn: sqlite3.Connection) -> None:
    _populate_document(conn, id=1, path="a.md")
    row = conn.execute(
        "SELECT path, 'sum' AS summary, '[\"note\", \"hoplite\"]' AS tags, 1 AS distance FROM document WHERE id = 1"
    ).fetchone()
    hit = row_to_traversal_hit(row, [])
    assert hit.tags == ["hoplite", "note"]
