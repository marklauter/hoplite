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
    "set_root",
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
_vault_root: Path | None = None
_hoplite_root: Path | None = None


def set_root(cwd: Path) -> None:
    """Configure the vault and Hoplite state directories from ``cwd``.

    The vault lives at ``cwd/docs`` — the walker indexes every ``.md`` under it.
    Hoplite-derived state lives at ``cwd/.hoplite`` — alongside the vault, not
    inside it. Resets the cached graph so the next tool call rebuilds.
    """
    global _graph, _vault_root, _hoplite_root
    _vault_root = cwd / "docs"
    _hoplite_root = cwd / ".hoplite"
    _graph = None


def _vault() -> Path:
    return _vault_root if _vault_root is not None else Path.cwd() / "docs"


def _hoplite_state() -> Path:
    return _hoplite_root if _hoplite_root is not None else Path.cwd() / ".hoplite"


def _get_graph() -> Graph:
    global _graph
    if _graph is None:
        _graph = graph_module.walk(_vault())
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
        escaped = _escape_fts5_query(text)
        if escaped:
            cursor = graph.fts.execute(
                "SELECT path, bm25(fts) AS score FROM fts WHERE fts MATCH ? ORDER BY score LIMIT ?",
                (escaped, over_fetch),
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
    origin = graph.resolve_wikilink(from_)
    if origin is None:
        raise ValueError(f"unknown starting document: {from_!r}")

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


def _escape_fts5_query(text: str) -> str:
    """Make user text safe for FTS5 MATCH; preserves AND semantics across whitespace tokens.

    FTS5 raises on bare special chars (``"``, ``:``, ``(``, ``*``, etc.) and on operator
    keywords (``AND``, ``OR``, ``NEAR``). Wrapping each whitespace-split token in double
    quotes (with internal quotes doubled) escapes everything; FTS5's implicit AND across
    space-separated terms preserves the multi-word search semantics callers expect.
    Returns ``""`` for whitespace-only input (the caller skips the FTS5 query when empty).
    """
    terms = text.split()
    return " ".join('"' + t.replace('"', '""') + '"' for t in terms)


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
    vault = _vault()
    _graph = graph_module.walk(vault)
    return WriteResult(
        path=str(vault.resolve()),
        warnings=list(_graph.warnings) if _graph.warnings else None,
    )


def dump_index(path: str | None = None) -> WriteResult:
    """Snapshot the in-memory graph to a SQLite file for debugging."""
    graph = _get_graph()
    destination = Path(path) if path else _hoplite_state() / "index.db"
    return graph.dump_index(destination)
