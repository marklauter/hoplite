"""Tests for hoplite.filtering."""

from __future__ import annotations

import pytest

from hoplite.filtering import filter_candidates
from hoplite.parser import parse_predicate

# --- empty input --------------------------------------------------------------


def test_empty_candidates_returns_empty() -> None:
    predicate = parse_predicate("note")
    assert filter_candidates(predicate, []) == []


def test_empty_candidates_accepts_generator() -> None:
    predicate = parse_predicate("note")
    empty: list[tuple[str, frozenset[str]]] = []
    assert filter_candidates(predicate, (c for c in empty)) == []


# --- single candidate ---------------------------------------------------------


def test_single_candidate_matches() -> None:
    predicate = parse_predicate("note")
    assert filter_candidates(predicate, [("a.md", frozenset({"note"}))]) == ["a.md"]


def test_single_candidate_does_not_match() -> None:
    predicate = parse_predicate("note")
    assert filter_candidates(predicate, [("a.md", frozenset({"journal"}))]) == []


def test_single_candidate_empty_labels() -> None:
    predicate = parse_predicate("note")
    assert filter_candidates(predicate, [("a.md", frozenset[str]())]) == []


# --- mixed outcomes -----------------------------------------------------------


def test_mixed_candidates_partial_survival() -> None:
    predicate = parse_predicate("note")
    candidates: list[tuple[str, frozenset[str]]] = [
        ("a.md", frozenset({"note"})),
        ("b.md", frozenset({"journal"})),
        ("c.md", frozenset({"note", "mcp"})),
        ("d.md", frozenset[str]()),
    ]
    assert filter_candidates(predicate, candidates) == ["a.md", "c.md"]


# --- order preservation -------------------------------------------------------


def test_order_preserved_for_survivors() -> None:
    predicate = parse_predicate("note")
    # Survivors are interleaved so any reordering would surface.
    candidates: list[tuple[str, frozenset[str]]] = [
        ("e.md", frozenset({"note"})),
        ("d.md", frozenset({"draft"})),
        ("c.md", frozenset({"note"})),
        ("b.md", frozenset({"journal"})),
        ("a.md", frozenset({"note"})),
    ]
    assert filter_candidates(predicate, candidates) == ["e.md", "c.md", "a.md"]


def test_order_preserved_when_all_match() -> None:
    predicate = parse_predicate("note | journal")
    candidates: list[tuple[str, frozenset[str]]] = [
        ("z.md", frozenset({"note"})),
        ("m.md", frozenset({"journal"})),
        ("a.md", frozenset({"note", "journal"})),
    ]
    assert filter_candidates(predicate, candidates) == ["z.md", "m.md", "a.md"]


# --- realistic predicates from docs/hoplite/hoplite-architecture.md -------------------


def test_doc_example_intersection() -> None:
    # note & mcp — nodes labeled both note and mcp.
    predicate = parse_predicate("note & mcp")
    candidates: list[tuple[str, frozenset[str]]] = [
        ("data-model.md", frozenset({"note", "mcp"})),
        ("journal-entry.md", frozenset({"note"})),
        ("server.md", frozenset({"mcp"})),
        ("untagged.md", frozenset[str]()),
    ]
    assert filter_candidates(predicate, candidates) == ["data-model.md"]


def test_doc_example_union_with_exclusion() -> None:
    # (note | journal) & !draft
    predicate = parse_predicate("(note | journal) & !draft")
    candidates: list[tuple[str, frozenset[str]]] = [
        ("a.md", frozenset({"note"})),
        ("b.md", frozenset({"journal"})),
        ("c.md", frozenset({"note", "draft"})),
        ("d.md", frozenset({"draft"})),
        ("e.md", frozenset({"mcp"})),
        ("f.md", frozenset({"journal", "mcp"})),
    ]
    assert filter_candidates(predicate, candidates) == ["a.md", "b.md", "f.md"]


def test_doc_example_date_exclusion() -> None:
    # mcp & !2026-05-24 — mcp-labeled nodes excluding today's.
    predicate = parse_predicate("mcp & !2026-05-24")
    candidates: list[tuple[str, frozenset[str]]] = [
        ("yesterday.md", frozenset({"mcp", "2026-05-23"})),
        ("today.md", frozenset({"mcp", "2026-05-24"})),
        ("undated.md", frozenset({"mcp"})),
        ("note.md", frozenset({"note", "2026-05-23"})),
    ]
    assert filter_candidates(predicate, candidates) == ["yesterday.md", "undated.md"]


# --- consumer reuses one predicate across batches -----------------------------


def test_predicate_reusable_across_batches() -> None:
    predicate = parse_predicate("note")
    batch1: list[tuple[str, frozenset[str]]] = [
        ("a.md", frozenset({"note"})),
        ("b.md", frozenset({"draft"})),
    ]
    batch2: list[tuple[str, frozenset[str]]] = [
        ("c.md", frozenset({"note", "mcp"})),
    ]
    assert filter_candidates(predicate, batch1) == ["a.md"]
    assert filter_candidates(predicate, batch2) == ["c.md"]


# --- duplicate ids pass through unchanged -------------------------------------


def test_duplicate_ids_preserved() -> None:
    # The filter doesn't dedupe — that's a caller concern.
    predicate = parse_predicate("note")
    candidates: list[tuple[str, frozenset[str]]] = [
        ("a.md", frozenset({"note"})),
        ("a.md", frozenset({"note"})),
    ]
    assert filter_candidates(predicate, candidates) == ["a.md", "a.md"]


# --- tautology / contradiction ------------------------------------------------


@pytest.mark.parametrize(
    ("expression", "expected_ids"),
    [
        ("note | !note", ["a.md", "b.md", "c.md"]),  # tautology: every candidate survives
        ("note & !note", []),  # contradiction: no candidate survives
    ],
)
def test_tautology_and_contradiction(expression: str, expected_ids: list[str]) -> None:
    predicate = parse_predicate(expression)
    candidates: list[tuple[str, frozenset[str]]] = [
        ("a.md", frozenset({"note"})),
        ("b.md", frozenset({"draft"})),
        ("c.md", frozenset[str]()),
    ]
    assert filter_candidates(predicate, candidates) == expected_ids
