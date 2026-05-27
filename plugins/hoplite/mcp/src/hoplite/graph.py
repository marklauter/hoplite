"""In-memory graph and corpus walker.

The ``Graph`` class is the mutable container holding documents, properties,
edges, and the in-memory FTS5 connection. The ``walk`` function builds a
populated ``Graph`` by scanning ``.md`` files under a corpus root through two
passes — identity collection, then body load with edge materialization —
followed by an aggregate pairwise MinHash pass for ``related`` edges.

See docs/hoplite/architecture.md for the full architectural shape.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, cast

import yaml

from hoplite import minhash, urls, wikilinks
from hoplite.models import Document, Edge, WriteResult

__all__ = [
    "DUMP_SCHEMA",
    "Graph",
    "walk",
]


def _empty_documents() -> dict[str, Document]:
    return {}


def _empty_edges() -> dict[str, list[Edge]]:
    return {}


def _empty_str_dict() -> dict[str, str]:
    return {}


def _empty_str_list() -> list[str]:
    return []


def _empty_node_props() -> dict[str, dict[str, list[str]]]:
    return {}


def _empty_edge_props() -> dict[tuple[str, str, str], dict[str, list[str]]]:
    return {}


# Frontmatter regex — matches `---\n...\n---\n` at the start of the file.
# `\r?\n` covers both LF and CRLF line endings (Obsidian on Windows writes CRLF).
_FRONTMATTER_RE: Final = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)

_REQUIRED_FIELDS: Final = ("title", "summary", "tags", "created")


DUMP_SCHEMA: Final = """
CREATE TABLE nodes (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL  -- 'document' (the only kind day one)
);

CREATE TABLE documents (
  id INTEGER PRIMARY KEY REFERENCES nodes(id),
  path TEXT NOT NULL UNIQUE,
  resolved INTEGER NOT NULL,
  content_hash TEXT,
  minhash BLOB
);

CREATE TABLE node_properties (
  node_id INTEGER NOT NULL REFERENCES nodes(id),
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (node_id, key, value)
);
CREATE INDEX idx_node_props_key_value ON node_properties(key, value);

CREATE TABLE edges (
  id INTEGER PRIMARY KEY,
  src INTEGER NOT NULL REFERENCES nodes(id),
  dst INTEGER NOT NULL REFERENCES nodes(id),
  kind TEXT NOT NULL,
  UNIQUE (src, dst, kind)
);
CREATE INDEX idx_edges_src ON edges(src);
CREATE INDEX idx_edges_dst ON edges(dst);

CREATE TABLE edge_properties (
  edge_id INTEGER NOT NULL REFERENCES edges(id),
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (edge_id, key, value)
);
CREATE INDEX idx_edge_props_key_value ON edge_properties(key, value);

CREATE VIRTUAL TABLE fts USING fts5(
  path UNINDEXED,
  title,
  summary,
  body,
  tokenize = 'porter unicode61',
  content = ''
);
"""


@dataclass
class Graph:
    """Mutable container for the in-memory graph state."""

    documents: dict[str, Document] = field(default_factory=_empty_documents)
    node_properties: dict[str, dict[str, list[str]]] = field(default_factory=_empty_node_props)
    edge_properties: dict[tuple[str, str, str], dict[str, list[str]]] = field(
        default_factory=_empty_edge_props,
    )
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
        (``str.casefold()``) and tolerant of an omitted ``.md`` extension
        (per docs/hoplite/architecture.md#wikilinks-and-ghost-documents).

        Display syntax — ``#anchor`` and ``|alias`` — is stripped before
        lookup. ``[[target#section|label]]`` resolves the same as ``[[target]]``.
        """
        target = target.split("|", 1)[0].split("#", 1)[0].strip()
        if not target:
            return None
        if target in self.documents:
            return target
        if target in self.aliases:
            return self.aliases[target]
        folded = self.casefold_index.get(target.casefold())
        if folded is not None:
            return folded
        if not target.endswith(".md"):
            return self.resolve_wikilink(target + ".md")
        return None

    def dump_index(self, path: str | Path) -> WriteResult:
        """Snapshot the in-memory state to a SQLite file. Overwrites the destination."""
        abs_path = Path(path).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        if abs_path.exists():
            abs_path.unlink()

        # Assign deterministic integer IDs to documents in path order.
        node_ids: dict[str, int] = {
            path_key: idx + 1 for idx, path_key in enumerate(sorted(self.documents))
        }

        conn = sqlite3.connect(str(abs_path))
        try:
            conn.executescript(DUMP_SCHEMA)
            self._write_nodes(conn, node_ids)
            self._write_documents(conn, node_ids)
            self._write_node_properties(conn, node_ids)
            edge_ids = self._write_edges(conn, node_ids)
            self._write_edge_properties(conn, edge_ids)
            self._write_fts(conn, node_ids)
            conn.commit()
        finally:
            conn.close()

        url_count = sum(
            1
            for d in self.documents.values()
            if not d.resolved and (d.path.startswith("http://") or d.path.startswith("https://"))
        )
        ghost_count = sum(1 for d in self.documents.values() if not d.resolved) - url_count
        edge_count = sum(len(es) for es in self.out_edges.values())
        return WriteResult(
            path=str(abs_path),
            counts={
                "documents": len(self.documents) - ghost_count - url_count,
                "ghosts": ghost_count,
                "urls": url_count,
                "edges": edge_count,
            },
        )

    def _write_nodes(self, conn: sqlite3.Connection, node_ids: dict[str, int]) -> None:
        rows = [(node_ids[path_key], "document") for path_key in self.documents]
        conn.executemany("INSERT INTO nodes VALUES (?, ?)", rows)

    def _write_documents(self, conn: sqlite3.Connection, node_ids: dict[str, int]) -> None:
        rows = [
            (
                node_ids[doc.path],
                doc.path,
                1 if doc.resolved else 0,
                doc.content_hash,
                doc.minhash,
            )
            for doc in self.documents.values()
        ]
        conn.executemany(
            "INSERT INTO documents VALUES (?, ?, ?, ?, ?)",
            rows,
        )

    def _write_node_properties(self, conn: sqlite3.Connection, node_ids: dict[str, int]) -> None:
        rows: list[tuple[int, str, str]] = []
        for path_key, props in self.node_properties.items():
            node_id = node_ids[path_key]
            for key, values in props.items():
                for value in values:
                    rows.append((node_id, key, value))
        if rows:
            conn.executemany("INSERT INTO node_properties VALUES (?, ?, ?)", rows)

    def _write_edges(
        self,
        conn: sqlite3.Connection,
        node_ids: dict[str, int],
    ) -> dict[tuple[str, str, str], int]:
        """Insert edge rows; return a map from (src, dst, kind) → assigned edge_id."""
        edge_ids: dict[tuple[str, str, str], int] = {}
        rows: list[tuple[int, int, int, str]] = []
        for edges in self.out_edges.values():
            for edge in edges:
                triple = (edge.src, edge.dst, edge.kind)
                if triple in edge_ids:
                    continue
                edge_id = len(edge_ids) + 1
                edge_ids[triple] = edge_id
                rows.append((edge_id, node_ids[edge.src], node_ids[edge.dst], edge.kind))
        if rows:
            conn.executemany("INSERT INTO edges VALUES (?, ?, ?, ?)", rows)
        return edge_ids

    def _write_edge_properties(
        self,
        conn: sqlite3.Connection,
        edge_ids: dict[tuple[str, str, str], int],
    ) -> None:
        rows: list[tuple[int, str, str]] = []
        for triple, props in self.edge_properties.items():
            edge_id = edge_ids.get(triple)
            if edge_id is None:
                continue
            for key, values in props.items():
                for value in values:
                    rows.append((edge_id, key, value))
        if rows:
            conn.executemany("INSERT INTO edge_properties VALUES (?, ?, ?)", rows)

    def _write_fts(self, conn: sqlite3.Connection, node_ids: dict[str, int]) -> None:
        """Replay title/summary/body into the contentless FTS5 index.

        FTS5 contentless mode keeps only the inverted index; raw column values
        are discarded after insert. The rowid is set to ``documents.id`` so
        consumers can join FTS back to ``documents`` via ``fts.rowid = id``.
        Body lives only in the markdown file on disk — the dump's FTS index
        carries title and summary tokens for debug-grade match queries.
        """
        rows: list[tuple[int, str, str, str, str]] = []
        for doc in self.documents.values():
            if not doc.resolved:
                continue
            props = self.node_properties.get(doc.path, {})
            title = (props.get("title") or [""])[0]
            summary = (props.get("summary") or [""])[0]
            rows.append((node_ids[doc.path], doc.path, title, summary, ""))
        if rows:
            conn.executemany(
                "INSERT INTO fts (rowid, path, title, summary, body) VALUES (?, ?, ?, ?, ?)",
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
            relative = md_path.relative_to(corpus_root.parent)
        except ValueError:
            continue
        canonical = relative.as_posix()
        if "/.hoplite/" in canonical or canonical.startswith(".hoplite/"):
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
        aliases_value = meta.get("aliases", [])
        if not isinstance(tags_value, list) or not isinstance(aliases_value, list):
            graph.warnings.append(f"{canonical}: tags and aliases must be lists")
            continue

        # Populate node_properties from the full frontmatter dict — every key,
        # scalar or list, becomes one or more (key, value) entries.
        graph.node_properties[canonical] = _frontmatter_to_props(meta)

        alias_strs = tuple(str(a) for a in cast(list[object], aliases_value))

        doc = Document(
            path=canonical,
            resolved=True,
            content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
            minhash=None,  # filled in pass 2
        )
        graph.documents[canonical] = doc
        graph.casefold_index[canonical.casefold()] = canonical
        # Aliases populate the lookup map AND the property store (already done above).
        for alias in alias_strs:
            graph.aliases[alias] = canonical
            graph.casefold_index[alias.casefold()] = canonical

        parsed.append((canonical, meta, body))

    # Pass 2: body load (already loaded above), edges, FTS, MinHash.
    for canonical, _meta, body in parsed:
        doc = graph.documents[canonical]
        # Wikilink mentions edges — dedupe per resolved target.
        seen_targets: set[str] = set()
        for target, _line, _column in wikilinks.extract(body):
            # Convention check: real wikilinks live under docs/, intentional
            # ghosts under ghost/. Anything else is malformed — warn and skip
            # rather than silently materializing a ghost at a garbage path.
            bare = target.split("|", 1)[0].split("#", 1)[0].strip()
            if not (bare.startswith("docs/") or bare.startswith("ghost/")):
                graph.warnings.append(
                    f"{canonical}: wikilink target '{target}' must start with 'docs/' or 'ghost/'",
                )
                continue
            resolved_target = graph.resolve_wikilink(target)
            if resolved_target is None:
                # Materialize a ghost at the bare (alias/anchor-stripped) target.
                ghost = Document(path=bare, resolved=False)
                graph.documents[bare] = ghost
                graph.casefold_index[bare.casefold()] = bare
                graph.node_properties[bare] = {"tags": ["ghost"]}
                resolved_target = bare
            if resolved_target in seen_targets:
                continue
            seen_targets.add(resolved_target)
            edge = Edge(src=canonical, dst=resolved_target, kind="mentions")
            graph.add_edge(edge)
        # External URL cites edges — markdown `[text](https://...)` links.
        seen_urls: set[str] = set()
        for url, _line, _column in urls.extract(body):
            if url in seen_urls:
                continue
            seen_urls.add(url)
            if url not in graph.documents:
                graph.documents[url] = Document(path=url, resolved=False)
                graph.casefold_index[url.casefold()] = url
                graph.node_properties[url] = {"tags": ["url"]}
            graph.add_edge(Edge(src=canonical, dst=url, kind="cites"))
        # MinHash signature.
        sig = minhash.signature(body)
        sig_bytes = minhash.to_bytes(sig)
        graph.documents[canonical] = _with_minhash(doc, sig_bytes)
        # FTS5 row — title and summary from properties, body raw for tokenization.
        props = graph.node_properties.get(canonical, {})
        title = (props.get("title") or [""])[0]
        summary = (props.get("summary") or [""])[0]
        assert graph.fts is not None
        graph.fts.execute(
            "INSERT INTO fts (path, title, summary, body) VALUES (?, ?, ?, ?)",
            (canonical, title, summary, body),
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


def _frontmatter_to_props(meta: dict[str, Any]) -> dict[str, list[str]]:
    """Project a parsed frontmatter dict into the EAV property shape.

    Scalars become single-element lists. Lists become multi-element lists with
    each element stringified. Empty lists produce no entry. Tag values get
    casefolded so predicate lookups match case-insensitively.
    """
    props: dict[str, list[str]] = {}
    for key, value in meta.items():
        if isinstance(value, list):
            items = cast(list[object], value)
            if not items:
                continue
            if key == "tags":
                props[key] = [str(item).casefold() for item in items]
            else:
                props[key] = [str(item) for item in items]
        elif value is None:
            continue
        else:
            props[key] = [str(value)]
    return props


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
        content_hash=doc.content_hash,
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
            graph.add_edge(Edge(src=doc_a.path, dst=doc_b.path, kind="related"))
            graph.add_edge(Edge(src=doc_b.path, dst=doc_a.path, kind="related"))
            score_str = f"{score:.6f}"
            graph.edge_properties[(doc_a.path, doc_b.path, "related")] = {
                "confidence": [score_str],
            }
            graph.edge_properties[(doc_b.path, doc_a.path, "related")] = {
                "confidence": [score_str],
            }
