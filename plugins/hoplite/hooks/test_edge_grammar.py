"""Tests for the edge-target grammar — the executable form of expressing-edges.md.

Run: ``python -m pytest plugins/hoplite/hooks/test_edge_grammar.py``
"""

from __future__ import annotations

import pytest

from edge_grammar import (
    frontmatter_edge_targets,
    inline_wikilinks,
    validate_target,
)

# --- valid targets ------------------------------------------------------------

VALID = [
    "circle",                       # bare name
    "lib/shapes:circle",            # namespace:page
    "lib/shapes:circle/area",       # namespace:page/subpage
    "circle/area",                  # page/subpage, no namespace
    "refines::circle",              # stereotype
    "refines::lib/shapes:circle",   # stereotype + namespace (the :: / : combo)
    "circle#properties",            # section
    "circle#properties#radius",     # nested section
    "circle#^radius-def",           # block
    "refines::circle#properties",   # stereotype + section
    "ghost/draft-idea",             # ghost open loop
    "../parent",                    # relative parent
    "/child",                       # relative-to-root
    "kind",                         # extensionless name that happens to look termish
]


@pytest.mark.parametrize("target", VALID)
def test_valid_frontmatter(target: str) -> None:
    assert validate_target(target) is None, target


@pytest.mark.parametrize("target", VALID)
def test_valid_inline(target: str) -> None:
    assert validate_target(target, inline=True) is None, target


def test_inline_display_text_allowed() -> None:
    assert validate_target("circle|shown text", inline=True) is None


# --- invalid targets ----------------------------------------------------------

INVALID = [
    ("", "empty"),
    ("   ", "empty"),
    ("contrast::kind.md", ".md"),
    ("kind.md", ".md"),
    ("circle.md#properties", ".md"),
    ("a::b::c", "more than one"),
    ("::circle", "empty stereotype"),
    ("circle::", "empty target after"),
    ("foo!bar", "embed"),
]


@pytest.mark.parametrize(("target", "needle"), INVALID)
def test_invalid_reports_specific(target: str, needle: str) -> None:
    msg = validate_target(target)
    assert msg is not None, target
    assert needle in msg, f"{target!r} -> {msg!r}"


def test_display_text_rejected_in_frontmatter() -> None:
    msg = validate_target("circle|shown")
    assert msg is not None and "inline-only" in msg


def test_display_text_stripped_then_validated_inline() -> None:
    # display text is free-form, but the link before `|` still must be valid
    assert validate_target("kind.md|shown", inline=True) is not None


def test_structural_fallback_for_odd_shapes() -> None:
    assert validate_target("a:b:c:d") is not None  # too many namespace colons


# --- frontmatter extraction ---------------------------------------------------


def test_flow_list() -> None:
    lines = ["title: t", "edges: [refines::circle, contrast::square]"]
    assert frontmatter_edge_targets(lines) == ["refines::circle", "contrast::square"]


def test_block_list() -> None:
    lines = ["edges:", "  - refines::circle", "  - contrast::square"]
    assert frontmatter_edge_targets(lines) == ["refines::circle", "contrast::square"]


def test_quoted_flow_items_validated_with_quotes() -> None:
    lines = ['edges: ["refines::circle"]']
    # extraction is raw; validate_target strips surrounding quotes itself
    assert frontmatter_edge_targets(lines) == ['"refines::circle"']
    assert validate_target('"refines::circle"') is None


def test_quoted_invalid_still_caught() -> None:
    msg = validate_target('"kind.md"')
    assert msg is not None and ".md" in msg


def test_scalar_where_list_belongs_is_captured() -> None:
    assert frontmatter_edge_targets(["edges: kind.md"]) == ["kind.md"]


def test_indented_edges_key_is_not_top_level() -> None:
    # a nested `edges:` (indented) is not the bare list key
    assert frontmatter_edge_targets(["document:", "  edges: [x]"]) == []


def test_no_edges_key() -> None:
    assert frontmatter_edge_targets(["title: t", "summary: s"]) == []


# --- inline extraction --------------------------------------------------------


def test_inline_basic() -> None:
    assert inline_wikilinks("see [[circle]] here") == [("circle", 1)]


def test_inline_embed_marker_not_in_target() -> None:
    assert inline_wikilinks("![[circle]]") == [("circle", 1)]


def test_inline_skips_backticked_sample() -> None:
    assert inline_wikilinks("an example `[[circle]]` is skipped") == []


def test_inline_skips_fenced_block() -> None:
    body = "```\n[[circle]]\n```\nbut [[square]] counts"
    assert inline_wikilinks(body) == [("square", 4)]


def test_inline_dedupes_keeping_first_line() -> None:
    assert inline_wikilinks("[[circle]]\nand [[circle]]") == [("circle", 1)]


def test_inline_display_target_extracted_whole() -> None:
    # the `|display` rides along; validate_target(inline=True) handles it
    assert inline_wikilinks("[[circle|shown]]") == [("circle|shown", 1)]
    assert validate_target("circle|shown", inline=True) is None
