"""Domain models for Hoplite — frozen dataclasses mirroring docs/hoplite/architecture.md.

All record types are immutable. The Graph container (see hoplite.graph) is the
mutable shell; entities are values projected from it.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "Document",
    "Edge",
    "Hit",
    "TraversalHit",
    "WriteResult",
]


@dataclass(frozen=True, slots=True)
class Document:
    """A markdown file in the corpus, identified by its relative path.

    File-level facts only: identity (``path``), ghost-or-real flag (``resolved``),
    and the two derived non-searchable artifacts (``content_hash``, ``minhash``).
    Everything authored in YAML frontmatter — title, summary, tags, aliases,
    created, and user-defined keys — lives in ``Graph.node_properties`` instead.

    Ghost documents (referenced by a wikilink but not yet on disk) have
    ``resolved=False`` and the derived fields ``None``.
    """

    path: str
    resolved: bool
    content_hash: str | None = None
    minhash: bytes | None = None


@dataclass(frozen=True, slots=True)
class Edge:
    """A typed connection between two documents.

    Day-one ``kind`` is one of ``mentions`` or ``related``. Each pair of nodes
    carries at most one edge per kind. Edge properties (e.g., ``confidence`` for
    ``related`` edges) live in ``Graph.edge_properties`` keyed on the
    ``(src, dst, kind)`` triple.
    """

    src: str
    dst: str
    kind: str


@dataclass(frozen=True, slots=True)
class Hit:
    """A search result from ``hoplite_match_nodes``."""

    path: str
    summary: str
    tags: list[str]
    score: float


@dataclass(frozen=True, slots=True)
class TraversalHit:
    """A result from ``hoplite_traverse_nodes``. One per node reached."""

    path: str
    summary: str
    tags: list[str]
    distance: int
    via_edges: list[Edge]


# slots=True omitted: FastMCP's Pydantic schema generator reads the slot
# member descriptor as a non-serializable default and warns at startup.
@dataclass(frozen=True)
class WriteResult:
    """Returned by ``hoplite_reindex`` and ``hoplite_dump_index``."""

    path: str
    counts: dict[str, int] | None = None
    warnings: list[str] | None = None
