"""Domain models for Hoplite — frozen dataclasses mirroring docs/mcp/data-model.md.

All record types are immutable. The Graph container (see hoplite.graph) is the
mutable shell; entities are values projected from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = [
    "Document",
    "Edge",
    "Hit",
    "Tag",
    "TraversalHit",
    "WriteResult",
]


# Typed empty default for frozen-dataclass field defaults — `frozenset()` alone
# produces frozenset[Unknown] under strict pyright.
_NO_TAGS: Final[frozenset[str]] = frozenset()


@dataclass(frozen=True, slots=True)
class Document:
    """A markdown file in the corpus, identified by its relative path.

    Ghost documents (referenced by a wikilink but not yet on disk) have
    ``resolved=False`` and all content fields ``None``.
    """

    path: str
    resolved: bool
    tags: frozenset[str] = _NO_TAGS
    aliases: tuple[str, ...] = ()
    title: str | None = None
    summary: str | None = None
    body: str | None = None
    content_hash: str | None = None
    created: str | None = None
    minhash: bytes | None = None


@dataclass(frozen=True, slots=True)
class Tag:
    """A free-form annotation. First-class graph node with members.

    Tag membership is derived from ``member`` edges in the Graph, not stored
    on the Tag value itself.
    """

    slug: str
    text: str
    summary: str | None = None


@dataclass(frozen=True, slots=True)
class Edge:
    """A typed connection between two nodes.

    Day-one ``kind`` is one of ``member``, ``mentions``, ``related``.
    Source-position fields (``source_path``, ``line``, ``column``) populate for
    ``mentions`` edges only; ``confidence`` and ``source`` populate for
    ``related`` edges only.
    """

    src: str
    dst: str
    kind: str
    confidence: float | None = None
    source: str | None = None
    rationale: str | None = None
    source_path: str | None = None
    line: int | None = None
    column: int | None = None


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
