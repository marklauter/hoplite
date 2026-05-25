"""Tool handlers for the four-tool Hoplite MCP surface.

Bodies delegate to a module-level ``Graph`` singleton initialized lazily on
first call (or eagerly via the server lifespan). ``hoplite_reindex`` resets
the singleton so the next call rebuilds from the corpus.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Literal, TypedDict

from hoplite import filtering, parser
from hoplite import graph as graph_module
from hoplite.graph import Graph
from hoplite.models import Edge, Hit, TraversalHit, WriteResult

__all__ = [
    "MatchPredicate",
    "TraversePredicate",
    "dump_index",
    "match_nodes",
    "reindex",
    "set_corpus_root",
    "traverse_nodes",
]


class MatchPredicate(TypedDict, total=False):
    text: str
    tagged: str


class TraversePredicate(TypedDict, total=False):
    edge_types: list[str]
    min_confidence: float
    direction: Literal["out", "in", "both"]
    tagged: str


_graph: Graph | None = None
_corpus_root: Path | None = None


def set_corpus_root(root: Path) -> None:
    """Set the corpus root and reset the cached graph. Called by the server lifespan."""
    global _graph, _corpus_root
    _corpus_root = root
    _graph = None


def _get_graph() -> Graph:
    global _graph
    if _graph is None:
        root = _corpus_root if _corpus_root is not None else Path.cwd()
        _graph = graph_module.walk(root)
    return _graph


def match_nodes(predicate: MatchPredicate, k: int = 5) -> list[Hit]:
    """Search the corpus. BM25 over body and summary, optional tag predicate post-filter."""
    if k < 1:
        raise ValueError(f"k must be >= 1; got {k}")
    text = predicate.get("text", "").strip()
    tagged = predicate.get("tagged", "").strip()
    if not text and not tagged:
        raise ValueError("predicate must include at least one of `text` or `tagged`")

    graph = _get_graph()

    # Stage 1: get scored candidates from FTS5 (or the full corpus when no text query).
    candidates: list[tuple[str, float]] = []
    if text:
        assert graph.fts is not None
        # Over-fetch so the tag post-filter still has results.
        over_fetch = k * 4 if tagged else k
        cursor = graph.fts.execute(
            "SELECT path, bm25(fts) AS score FROM fts WHERE fts MATCH ? ORDER BY score LIMIT ?",
            (text, over_fetch),
        )
        # FTS5 bm25() returns negative values where smaller (more negative) is more relevant.
        # Negate so the Hit.score reads as higher = better.
        candidates = [(path, -score) for path, score in cursor.fetchall()]
    else:
        # No text query — every resolved document is a candidate at score 0.
        candidates = [(doc.path, 0.0) for doc in graph.documents.values() if doc.resolved]

    # Stage 2: optional tag predicate post-filter.
    if tagged:
        pred = parser.parse_predicate(tagged)
        filtered_paths = set(
            filtering.filter_candidates(
                pred,
                (
                    (path, graph.documents[path].tags)
                    for path, _ in candidates
                    if path in graph.documents
                ),
            ),
        )
        candidates = [c for c in candidates if c[0] in filtered_paths]

    # Stage 3: cap at k and build Hits.
    hits: list[Hit] = []
    for path, score in candidates[:k]:
        doc = graph.documents.get(path)
        if doc is None or not doc.resolved:
            continue
        hits.append(
            Hit(
                path=path,
                summary=doc.summary or "",
                tags=sorted(doc.tags),
                score=score,
            ),
        )
    return hits


def traverse_nodes(
    from_: str,
    predicate: TraversePredicate | None = None,
    depth: int = 1,
) -> list[TraversalHit]:
    """BFS walk from a starting document. Returns hits at distances 1..depth."""
    if depth < 1:
        raise ValueError(f"depth must be >= 1; got {depth}")
    predicate = predicate or {}
    edge_types = set(predicate.get("edge_types", []))
    min_confidence = predicate.get("min_confidence", 0.0)
    direction = predicate.get("direction", "out")
    tagged = predicate.get("tagged", "").strip()
    tag_pred = parser.parse_predicate(tagged) if tagged else None

    graph = _get_graph()
    if from_ not in graph.documents and from_ not in graph.aliases:
        raise ValueError(f"unknown starting document: {from_!r}")
    origin = graph.resolve_wikilink(from_) or from_

    # BFS.
    visited: dict[str, int] = {origin: 0}
    paths: dict[str, list[Edge]] = {origin: []}
    queue: deque[str] = deque([origin])
    while queue:
        current = queue.popleft()
        current_distance = visited[current]
        if current_distance >= depth:
            continue
        neighbors = _neighbors(graph, current, direction, edge_types, min_confidence)
        for next_node, via in neighbors:
            if next_node in visited:
                continue
            visited[next_node] = current_distance + 1
            paths[next_node] = [*paths[current], via]
            queue.append(next_node)

    # Build TraversalHits (excluding origin), optionally tag-filtered.
    hits: list[TraversalHit] = []
    for node, distance in visited.items():
        if node == origin:
            continue
        doc = graph.documents.get(node)
        if doc is None:
            continue
        if tag_pred is not None and not tag_pred(doc.tags):
            continue
        hits.append(
            TraversalHit(
                path=node,
                summary=doc.summary or "",
                tags=sorted(doc.tags),
                distance=distance,
                via_edges=paths[node],
            ),
        )
    hits.sort(key=lambda h: (h.distance, h.path))
    return hits


def _neighbors(
    graph: Graph,
    node: str,
    direction: Literal["out", "in", "both"],
    edge_types: set[str],
    min_confidence: float,
) -> list[tuple[str, Edge]]:
    """Return (target, edge) pairs adjacent to ``node`` per the predicate filters."""
    candidates: list[Edge] = []
    if direction in ("out", "both"):
        candidates.extend(graph.out_edges.get(node, []))
    if direction in ("in", "both"):
        candidates.extend(graph.in_edges.get(node, []))
    result: list[tuple[str, Edge]] = []
    for edge in candidates:
        if edge_types and edge.kind not in edge_types:
            continue
        if edge.confidence is not None and edge.confidence < min_confidence:
            continue
        target = edge.dst if edge.src == node else edge.src
        result.append((target, edge))
    return result


def reindex() -> WriteResult:
    """Rebuild the in-memory graph from the corpus."""
    global _graph
    root = _corpus_root if _corpus_root is not None else Path.cwd()
    _graph = graph_module.walk(root)
    return WriteResult(
        path=str(root.resolve()),
        warnings=list(_graph.warnings) if _graph.warnings else None,
    )


def dump_index(path: str | None = None) -> WriteResult:
    """Snapshot the in-memory graph to a SQLite file for debugging."""
    graph = _get_graph()
    root = _corpus_root if _corpus_root is not None else Path.cwd()
    destination = Path(path) if path else root / ".hoplite" / "index.db"
    return graph.dump_index(destination)
