"""In-memory graph and corpus walker.

The ``Graph`` class is the mutable container holding documents, properties,
edges, and the in-memory FTS5 connection. The ``walk`` function builds a
populated ``Graph`` by scanning ``.md`` files under a corpus root through two
passes — identity collection, then body load with edge materialization —
followed by an aggregate pairwise MinHash pass for ``related`` edges.

See docs/hoplite/hoplite-architecture.md for the full architectural shape.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, cast

from hoplite import frontmatter, minhash, urls, wikilinks
from hoplite.models import Document, Edge, WriteResult

__all__ = [
    "SCHEMA",
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


def _empty_doc_props() -> dict[str, dict[str, list[str]]]:
    return {}


def _empty_edge_props() -> dict[tuple[str, str, str], dict[str, list[str]]]:
    return {}


# Frontmatter parsing moved to hoplite.frontmatter (split, normalize, validate).


# Single source of DDL for both the dump and the in-memory `:memory:` connection.
# The in-memory side only populates `fts`; the other tables sit empty there but
# loading them is the cost of keeping one canonical schema instead of two strings
# that can silently drift.
SCHEMA: Final = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")


@dataclass
class Graph:
    """Mutable container for the in-memory graph state."""

    documents: dict[str, Document] = field(default_factory=_empty_documents)
    document_properties: dict[str, dict[str, list[str]]] = field(default_factory=_empty_doc_props)
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
        (per docs/hoplite/hoplite-architecture.md#wikilinks-and-ghost-documents).

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

        conn = sqlite3.connect(str(abs_path))
        try:
            conn.executescript(SCHEMA)
            path_to_id = self._write_documents(conn)
            self._write_document_properties(conn, path_to_id)
            edge_pair_to_id = self._write_edges(conn, path_to_id)
            self._write_edge_properties(conn, edge_pair_to_id)
            self._write_fts(conn)
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

    def _write_documents(self, conn: sqlite3.Connection) -> dict[str, int]:
        """Insert documents with explicit integer ids and return the path → id map.

        Edges reference documents by id (rowid alias), so the writer assigns
        ids in iteration order here and hands the map back for the edge writers
        to translate paths.
        """
        path_to_id: dict[str, int] = {}
        rows: list[tuple[int, str, int, str | None, bytes | None]] = []
        for doc_id, (path, doc) in enumerate(self.documents.items(), start=1):
            path_to_id[path] = doc_id
            rows.append(
                (
                    doc_id,
                    doc.path,
                    1 if doc.resolved else 0,
                    doc.content_hash,
                    doc.minhash,
                ),
            )
        conn.executemany(
            "INSERT INTO document VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        return path_to_id

    def _write_document_properties(
        self,
        conn: sqlite3.Connection,
        path_to_id: dict[str, int],
    ) -> None:
        rows: list[tuple[int, str, str]] = []
        for path_key, props in self.document_properties.items():
            doc_id = path_to_id[path_key]
            for key, values in props.items():
                for value in values:
                    rows.append((doc_id, key, value))
        if rows:
            conn.executemany("INSERT INTO document_property VALUES (?, ?, ?)", rows)

    def _write_edges(
        self,
        conn: sqlite3.Connection,
        path_to_id: dict[str, int],
    ) -> dict[tuple[str, str], int]:
        """Insert edges with explicit integer ids and return a `(src_path, dst_path) → id` map.

        Edge properties FK to `edge.id`, so the writer assigns ids in iteration
        order here and hands the map back for the property writer to translate
        from the in-memory `(src, dst, kind)` triple — `(src, dst)` is the
        unique key on edge, so the kind is redundant for lookup.
        """
        seen: set[tuple[str, str]] = set()
        rows: list[tuple[int, int, int, str, float]] = []
        edge_pair_to_id: dict[tuple[str, str], int] = {}
        next_id = 1
        for edges in self.out_edges.values():
            for edge in edges:
                pair = (edge.src, edge.dst)
                if pair in seen:
                    continue
                seen.add(pair)
                edge_pair_to_id[pair] = next_id
                rows.append(
                    (
                        next_id,
                        path_to_id[edge.src],
                        path_to_id[edge.dst],
                        edge.kind,
                        edge.confidence,
                    ),
                )
                next_id += 1
        if rows:
            conn.executemany("INSERT INTO edge VALUES (?, ?, ?, ?, ?)", rows)
        return edge_pair_to_id

    def _write_edge_properties(
        self,
        conn: sqlite3.Connection,
        edge_pair_to_id: dict[tuple[str, str], int],
    ) -> None:
        rows: list[tuple[int, str, str]] = []
        for (src, dst, _kind), props in self.edge_properties.items():
            edge_id = edge_pair_to_id[(src, dst)]
            for key, values in props.items():
                for value in values:
                    rows.append((edge_id, key, value))
        if rows:
            conn.executemany("INSERT INTO edge_property VALUES (?, ?, ?)", rows)

    def _write_fts(self, conn: sqlite3.Connection) -> None:
        """Mirror the in-memory FTS5 index into the dump.

        The dump must be byte-for-byte equivalent to live state — it exists as
        a troubleshooting artifact, so any divergence between "what the server
        sees" and "what the snapshot shows" defeats the purpose. Bodies are
        replayed from ``self.fts`` (not re-read from disk) so the dump captures
        exactly the tokens the running server is matching against. The ``path``
        column is UNINDEXED so ``SELECT path FROM fts WHERE fts MATCH ...``
        joins back to ``document.path`` without an extra hop.
        """
        assert self.fts is not None
        rows = list(
            self.fts.execute("SELECT path, title, summary, body FROM fts"),
        )
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
        meta, body = frontmatter.parse(canonical, text, graph.warnings)
        if meta is None:
            continue

        # frontmatter.parse already validated document.tags / document.aliases as lists.
        aliases_value = meta.get("document.aliases", [])

        # Node properties: document.* keys with the prefix stripped, tags casefolded;
        # title/summary (FTS-only) and edge.* (stereotypes) are excluded.
        graph.document_properties[canonical] = frontmatter.to_properties(meta)

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
    for canonical, meta, body in parsed:
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
                graph.document_properties[bare] = {"tags": ["ghost"]}
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
                graph.document_properties[url] = {"tags": ["url"]}
            graph.add_edge(Edge(src=canonical, dst=url, kind="cites"))
        # MinHash signature.
        sig = minhash.signature(body)
        sig_bytes = minhash.to_bytes(sig)
        graph.documents[canonical] = _with_minhash(doc, sig_bytes)
        # FTS5 row — title/summary are bare first-class fields (not properties),
        # read straight from the frontmatter; body raw for tokenization.
        title, summary = frontmatter.fts_fields(meta)
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
    conn.executescript(SCHEMA)
    graph.fts = conn


def _with_minhash(doc: Document, sig_bytes: bytes) -> Document:
    """Return a copy of ``doc`` with ``minhash`` populated."""
    return Document(
        path=doc.path,
        resolved=doc.resolved,
        content_hash=doc.content_hash,
        minhash=sig_bytes,
    )


def _emit_related_edges(graph: Graph) -> None:
    """Pairwise MinHash comparison; emit symmetric `related` edges above threshold.

    Pairs already connected by an authored ``mentions`` edge (in either
    direction) are skipped — the author already declared the link, so
    reifying inferred similarity on top is redundant noise.
    """
    resolved = [d for d in graph.documents.values() if d.resolved and d.minhash is not None]
    threshold = minhash.DEFAULT_THRESHOLD
    mentioned: set[frozenset[str]] = {
        frozenset((edge.src, edge.dst))
        for edges in graph.out_edges.values()
        for edge in edges
        if edge.kind == "mentions"
    }
    for i, doc_a in enumerate(resolved):
        assert doc_a.minhash is not None
        sig_a = minhash.from_bytes(doc_a.minhash)
        for doc_b in resolved[i + 1 :]:
            if frozenset((doc_a.path, doc_b.path)) in mentioned:
                continue
            assert doc_b.minhash is not None
            sig_b = minhash.from_bytes(doc_b.minhash)
            score = minhash.jaccard(sig_a, sig_b)
            if score < threshold:
                continue
            graph.add_edge(Edge(src=doc_a.path, dst=doc_b.path, kind="related", confidence=score))
            graph.add_edge(Edge(src=doc_b.path, dst=doc_a.path, kind="related", confidence=score))
