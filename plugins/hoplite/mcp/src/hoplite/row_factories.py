import json
import sqlite3

from hoplite.models import Document, Edge, Hit, TraversalHit


def row_to_document(row: sqlite3.Row) -> Document:
    return Document(
        path=row["path"],
        resolved=bool(row["resolved"]),
        content_hash=row["content_hash"],
        minhash=row["minhash"],
    )


def row_to_document_with_id(row: sqlite3.Row) -> tuple[int, Document]:
    return row["id"], row_to_document(row)


def row_to_edge(row: sqlite3.Row) -> Edge:
    return Edge(
        src=row["src_path"],
        dst=row["dst_path"],
        kind=row["kind"],
        confidence=row["confidence"],
    )


def row_to_hit(row: sqlite3.Row) -> Hit:
    return Hit(
        path=row["path"],
        summary=row["summary"] or "",
        tags=parse_tags(row["tags"]),
        score=row["score"],
    )


def row_to_traversal_hit(row: sqlite3.Row, via_edges: list[Edge]) -> TraversalHit:
    return TraversalHit(
        path=row["path"],
        summary=row["summary"] or "",
        tags=parse_tags(row["tags"]),
        distance=row["distance"],
        via_edges=list(via_edges),
    )


def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [str(item) for item in json.loads(raw)]
