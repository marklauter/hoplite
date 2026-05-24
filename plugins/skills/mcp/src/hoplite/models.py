"""Domain models for Hoplite — frozen dataclasses mirroring docs/mcp/data-model.md.

All record types are immutable. Construction is where invariants land. Real
validation is deferred to the day-one implementation; these shapes exist so
the stub tool surface in `hoplite.tools` can return realistic returns.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "Edge",
    "Envelope",
    "FetchedNode",
    "Label",
    "Landing",
    "Node",
    "Prime",
    "TraversalHit",
    "WriteResult",
]


@dataclass(frozen=True, slots=True)
class Edge:
    type: str
    to: str | None = None
    # Trailing underscore avoids the Python keyword `from`; the JSON wire name matches.
    from_: str | None = None
    confidence: float | None = None
    source: str | None = None
    rationale: str | None = None


@dataclass(frozen=True, slots=True)
class Node:
    id: str
    labels: list[str]
    out_edges: list[Edge]
    summary: str
    body: str
    in_edges: list[Edge] | None = None
    embedding: str | None = None


@dataclass(frozen=True, slots=True)
class Label:
    id: str
    members: list[str]
    out_edges: list[Edge]
    summary: str | None = None
    envelope_body: str | None = None


@dataclass(frozen=True, slots=True)
class Prime:
    label: str
    body: str


@dataclass(frozen=True, slots=True)
class Envelope:
    framing: str
    primes: list[Prime]


@dataclass(frozen=True, slots=True)
class FetchedNode:
    id: str
    labels: list[str]
    out_edges: list[Edge]
    summary: str
    body: str
    envelope: Envelope
    in_edges: list[Edge] | None = None
    embedding: str | None = None


@dataclass(frozen=True, slots=True)
class Landing:
    id: str
    summary: str
    labels: list[str]
    score: float


@dataclass(frozen=True, slots=True)
class TraversalHit:
    id: str
    summary: str
    labels: list[str]
    distance: int
    via_edges: list[Edge]


@dataclass(frozen=True, slots=True)
class WriteResult:
    id: str
    warnings: list[str] | None = None
