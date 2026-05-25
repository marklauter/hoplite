"""In-memory graph and corpus walker.

The ``Graph`` class is the mutable container holding documents, tags, edges,
and the in-memory FTS5 connection. The ``walk`` function builds a populated
``Graph`` by scanning ``.md`` files under a corpus root through two passes —
identity collection, then body load with edge materialization — followed by
an aggregate pairwise MinHash pass for ``related`` edges.

See docs/mcp/implementation.md for the full architectural shape.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, cast

import yaml

from hoplite import minhash, wikilinks
from hoplite.models import Document, Edge, Tag, WriteResult

__all__ = [
    "DUMP_SCHEMA",
    "Graph",
    "walk",
]


def _empty_documents() -> dict[str, Document]:
    return {}


def _empty_tags() -> dict[str, Tag]:
    return {}


def _empty_edges() -> dict[str, list[Edge]]:
    return {}


def _empty_str_dict() -> dict[str, str]:
    return {}


def _empty_str_list() -> list[str]:
    return []


# Frontmatter regex — matches `---\n...\n---\n` at the start of the file.
# `\r?\n` covers both LF and CRLF line endings (Obsidian on Windows writes CRLF).
_FRONTMATTER_RE: Final = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)

_REQUIRED_FIELDS: Final = ("title", "summary", "tags", "created", "aliases")


DUMP_SCHEMA: Final = """
CREATE TABLE nodes (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL  -- 'document' | 'tag'
);

CREATE TABLE documents (
  id INTEGER PRIMARY KEY REFERENCES nodes(id),
  path TEXT NOT NULL UNIQUE,
  resolved INTEGER NOT NULL,
  title TEXT,
  summary TEXT,
  body TEXT,
  content_hash TEXT,
  created_at REAL,
  updated_at REAL,
  minhash BLOB
);

CREATE TABLE tags (
  id INTEGER PRIMARY KEY REFERENCES nodes(id),
  slug TEXT NOT NULL UNIQUE,
  text TEXT NOT NULL,
  summary TEXT
);

CREATE TABLE document_aliases (
  document_id INTEGER NOT NULL REFERENCES documents(id),
  alias TEXT NOT NULL,
  PRIMARY KEY (document_id, alias)
);

CREATE TABLE edges (
  src INTEGER NOT NULL REFERENCES nodes(id),
  dst INTEGER NOT NULL REFERENCES nodes(id),
  kind TEXT NOT NULL,
  confidence REAL,
  PRIMARY KEY (src, dst, kind)
);
CREATE INDEX idx_edges_src ON edges(src);
CREATE INDEX idx_edges_dst ON edges(dst);

CREATE VIRTUAL TABLE fts USING fts5(path, title, summary, body);
"""


@dataclass
class Graph:
    """Mutable container for the in-memory graph state."""

    documents: dict[str, Document] = field(default_factory=_empty_documents)
    tags: dict[str, Tag] = field(default_factory=_empty_tags)
    out_edges: dict[str, list[Edge]] = field(default_factory=_empty_edges)
    in_edges: dict[str, list[Edge]] = field(default_factory=_empty_edges)
    aliases: dict[str, str] = field(default_factory=_empty_str_dict)
    casefold_index: dict[str, str] = field(default_factory=_empty_str_dict)
    fts: sqlite3.Connection | None = None
    warnings: list[str] = field(default_factory=_empty_str_list)

    def add_edge(self, edge: Edge) -> None:
        """Register an edge in both adjacency dicts."""
        self.out_edges.setdefault(edge.src, []).append(edge)
        self.in_edges.setdefault(edge.dst, []).append(edge)

    def resolve_wikilink(self, target: str) -> str | None:
        """Resolve a wikilink target to a canonical document path.

        Returns the canonical path for a resolved target, or ``None`` if
        no document or alias matches. Lookup is case-insensitive ordinal
        (``str.casefold()``).
        """
        if target in self.documents:
            return target
        if target in self.aliases:
            return self.aliases[target]
        return self.casefold_index.get(target.casefold())

    def members_of(self, tag_slug: str) -> list[str]:
        """Return document paths that carry the given tag."""
        edges = self.out_edges.get(tag_slug, [])
        return [e.dst for e in edges if e.kind == "member"]

    def dump_index(self, path: str | Path) -> WriteResult:
        """Snapshot the in-memory state to a SQLite file. Overwrites the destination."""
        abs_path = Path(path).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        if abs_path.exists():
            abs_path.unlink()

        # Assign integer IDs to every node (document + tag), deterministic by sort.
        # The combined map lets edge writes resolve src/dst regardless of node kind.
        node_ids: dict[str, int] = {}
        for path_key in sorted(self.documents):
            node_ids[path_key] = len(node_ids) + 1
        for slug in sorted(self.tags):
            if slug in node_ids:
                raise ValueError(f"node identifier collision: {slug!r} is both a document path and a tag slug")
            node_ids[slug] = len(node_ids) + 1

        conn = sqlite3.connect(str(abs_path))
        try:
            conn.executescript(DUMP_SCHEMA)
            self._write_nodes(conn, node_ids)
            self._write_documents(conn, node_ids)
            self._write_tags(conn, node_ids)
            self._write_edges(conn, node_ids)
            self._write_fts(conn)
            conn.commit()
        finally:
            conn.close()

        ghost_count = sum(1 for d in self.documents.values() if not d.resolved)
        edge_count = sum(len(es) for es in self.out_edges.values())
        return WriteResult(
            path=str(abs_path),
            counts={
                "documents": len(self.documents) - ghost_count,
                "ghosts": ghost_count,
                "tags": len(self.tags),
                "edges": edge_count,
            },
        )

    def _write_nodes(self, conn: sqlite3.Connection, node_ids: dict[str, int]) -> None:
        rows: list[tuple[int, str]] = []
        for path_key in self.documents:
            rows.append((node_ids[path_key], "document"))
        for slug in self.tags:
            rows.append((node_ids[slug], "tag"))
        conn.executemany("INSERT INTO nodes VALUES (?, ?)", rows)

    def _write_documents(self, conn: sqlite3.Connection, node_ids: dict[str, int]) -> None:
        rows = [
            (
                node_ids[doc.path],
                doc.path,
                1 if doc.resolved else 0,
                doc.title,
                doc.summary,
                doc.body,
                doc.content_hash,
                _date_to_epoch(doc.created),
                None,  # updated_at from git not wired up yet
                doc.minhash,
            )
            for doc in self.documents.values()
        ]
        conn.executemany(
            "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        alias_rows = [
            (node_ids[doc.path], alias)
            for doc in self.documents.values()
            for alias in doc.aliases
        ]
        if alias_rows:
            conn.executemany("INSERT INTO document_aliases VALUES (?, ?)", alias_rows)

    def _write_tags(self, conn: sqlite3.Connection, node_ids: dict[str, int]) -> None:
        rows = [(node_ids[tag.slug], tag.slug, tag.text, tag.summary) for tag in self.tags.values()]
        if rows:
            conn.executemany("INSERT INTO tags VALUES (?, ?, ?, ?)", rows)

    def _write_edges(self, conn: sqlite3.Connection, node_ids: dict[str, int]) -> None:
        rows: list[tuple[Any, ...]] = [
            (
                node_ids[edge.src],
                node_ids[edge.dst],
                edge.kind,
                edge.confidence,
            )
            for edges in self.out_edges.values()
            for edge in edges
        ]
        if rows:
            conn.executemany(
                "INSERT INTO edges VALUES (?, ?, ?, ?)",
                rows,
            )

    def _write_fts(self, conn: sqlite3.Connection) -> None:
        rows = [
            (doc.path, doc.title or "", doc.summary or "", doc.body or "")
            for doc in self.documents.values()
            if doc.resolved
        ]
        if rows:
            conn.executemany(
                "INSERT INTO fts (path, title, summary, body) VALUES (?, ?, ?, ?)",
                rows,
            )


def walk(corpus_root: Path) -> Graph:
    """Build a populated ``Graph`` by walking ``.md`` files under ``corpus_root``."""
    graph = Graph()
    _setup_fts(graph)

    md_paths = sorted(corpus_root.rglob("*.md"))
    parsed: list[tuple[str, dict[str, Any], str]] = []

    # Pass 1: identity collection.
    for md_path in md_paths:
        try:
            relative = md_path.relative_to(corpus_root)
        except ValueError:
            continue
        canonical = relative.as_posix()
        if canonical.startswith(".hoplite/"):
            continue
        try:
            text = md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            graph.warnings.append(f"{canonical}: read failed: {exc}")
            continue
        meta, body = _parse_frontmatter(canonical, text, graph.warnings)
        if meta is None:
            continue

        tags_value = meta["tags"]
        aliases_value = meta["aliases"]
        if not isinstance(tags_value, list) or not isinstance(aliases_value, list):
            graph.warnings.append(f"{canonical}: tags and aliases must be lists")
            continue

        tags_list = cast(list[object], tags_value)
        aliases_list = cast(list[object], aliases_value)
        tag_originals = tuple(str(t) for t in tags_list)
        # Casefold tags at ingest so the predicate parser (which accepts only
        # `[a-z0-9-]`) and the `name in tags` membership test reach the same
        # canonical form. Tag.text preserves the original casing for display.
        tag_slugs = tuple(t.casefold() for t in tag_originals)
        alias_strs = tuple(str(a) for a in aliases_list)

        doc = Document(
            path=canonical,
            resolved=True,
            tags=frozenset(tag_slugs),
            aliases=alias_strs,
            title=str(meta["title"]),
            summary=str(meta["summary"]),
            body=body,
            content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
            created=str(meta["created"]),
            minhash=None,  # filled in pass 2
        )
        graph.documents[canonical] = doc
        graph.casefold_index[canonical.casefold()] = canonical
        for alias in alias_strs:
            graph.aliases[alias] = canonical
            graph.casefold_index[alias.casefold()] = canonical

        # Register tag nodes — slug is the canonical casefolded form;
        # text preserves the original casing from the first frontmatter mention.
        for slug, original in zip(tag_slugs, tag_originals, strict=True):
            if slug not in graph.tags:
                graph.tags[slug] = Tag(slug=slug, text=original)
                graph.casefold_index[slug] = slug

        parsed.append((canonical, meta, body))

    # Pass 2: body load (already loaded above), edges, FTS, MinHash.
    for canonical, _meta, body in parsed:
        doc = graph.documents[canonical]
        # Wikilink mentions edges (deduped per (src, dst) — multiple wikilinks to
        # the same target collapse to one edge; the graph carries relationships,
        # not source positions).
        seen_targets: set[str] = set()
        for target, _line, _column in wikilinks.extract(body):
            resolved_target = graph.resolve_wikilink(target)
            if resolved_target is None:
                # Materialize a ghost.
                ghost = Document(path=target, resolved=False)
                graph.documents[target] = ghost
                graph.casefold_index[target.casefold()] = target
                resolved_target = target
            if resolved_target in seen_targets:
                continue
            seen_targets.add(resolved_target)
            edge = Edge(src=canonical, dst=resolved_target, kind="mentions")
            graph.add_edge(edge)
        # Tag member edges.
        for tag_slug in doc.tags:
            edge = Edge(src=tag_slug, dst=canonical, kind="member")
            graph.add_edge(edge)
        # MinHash signature.
        sig = minhash.signature(body)
        sig_bytes = minhash.to_bytes(sig)
        graph.documents[canonical] = _with_minhash(doc, sig_bytes)
        # FTS5 row.
        assert graph.fts is not None
        graph.fts.execute(
            "INSERT INTO fts (path, title, summary, body) VALUES (?, ?, ?, ?)",
            (canonical, doc.title, doc.summary, body),
        )

    assert graph.fts is not None
    graph.fts.commit()

    # Aggregate pass: pairwise MinHash similarity for `related` edges.
    _emit_related_edges(graph)

    return graph


def _setup_fts(graph: Graph) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE VIRTUAL TABLE fts USING fts5(
            path UNINDEXED,
            title,
            summary,
            body,
            tokenize = 'porter unicode61'
        )
        """,
    )
    graph.fts = conn


def _parse_frontmatter(
    canonical: str,
    text: str,
    warnings: list[str],
) -> tuple[dict[str, Any] | None, str]:
    """Split frontmatter from body and parse it; return (meta, body) or (None, "")."""
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        warnings.append(f"{canonical}: missing or unterminated frontmatter")
        return None, ""
    yaml_block = match.group(1)
    body = text[match.end() :]
    try:
        raw_meta = yaml.safe_load(yaml_block)
    except yaml.YAMLError as exc:
        warnings.append(f"{canonical}: yaml parse error: {exc}")
        return None, ""
    if raw_meta is None:
        raw_meta = {}
    if not isinstance(raw_meta, dict):
        warnings.append(f"{canonical}: frontmatter is not a mapping")
        return None, ""
    meta: dict[str, Any] = {str(k): v for k, v in cast(dict[object, object], raw_meta).items()}
    missing = [f for f in _REQUIRED_FIELDS if f not in meta]
    if missing:
        warnings.append(f"{canonical}: missing mandatory fields: {missing}")
        return None, ""
    return meta, body


def _with_minhash(doc: Document, sig_bytes: bytes) -> Document:
    """Return a copy of ``doc`` with ``minhash`` populated."""
    return Document(
        path=doc.path,
        resolved=doc.resolved,
        tags=doc.tags,
        aliases=doc.aliases,
        title=doc.title,
        summary=doc.summary,
        body=doc.body,
        content_hash=doc.content_hash,
        created=doc.created,
        minhash=sig_bytes,
    )


def _emit_related_edges(graph: Graph) -> None:
    """Pairwise MinHash comparison; emit symmetric `related` edges above threshold."""
    resolved = [d for d in graph.documents.values() if d.resolved and d.minhash is not None]
    threshold = minhash.DEFAULT_THRESHOLD
    for i, doc_a in enumerate(resolved):
        assert doc_a.minhash is not None
        sig_a = minhash.from_bytes(doc_a.minhash)
        for doc_b in resolved[i + 1 :]:
            assert doc_b.minhash is not None
            sig_b = minhash.from_bytes(doc_b.minhash)
            score = minhash.jaccard(sig_a, sig_b)
            if score < threshold:
                continue
            graph.add_edge(
                Edge(
                    src=doc_a.path,
                    dst=doc_b.path,
                    kind="related",
                    confidence=score,
                ),
            )
            graph.add_edge(
                Edge(
                    src=doc_b.path,
                    dst=doc_a.path,
                    kind="related",
                    confidence=score,
                ),
            )


def _date_to_epoch(date_str: str | None) -> float | None:
    """Convert a YYYY-MM-DD string to a UTC epoch float; return None if unparseable."""
    if date_str is None:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None
