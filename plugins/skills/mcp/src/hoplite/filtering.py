"""Candidate filtering against a compiled label predicate.

Consumers parse and compile a label expression once via
:func:`hoplite.parser.parse_predicate`, then apply the resulting predicate
to one or many candidate batches with :func:`filter_candidates`. The
returned ids preserve input order so ranked candidate lists (e.g., BM25
results from match, breadth-ordered nodes from traverse) stay ranked
after filtering.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

__all__ = ["filter_candidates"]


def filter_candidates(
    predicate: Callable[[frozenset[str]], bool],
    candidates: Iterable[tuple[str, frozenset[str]]],
) -> list[str]:
    """Return ids of candidates whose labels satisfy the predicate.

    Order matches the iteration order of ``candidates``.
    """
    return [node_id for node_id, labels in candidates if predicate(labels)]
