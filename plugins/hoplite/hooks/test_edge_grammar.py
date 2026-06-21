"""Tests for the edge-target grammar — the executable form of expressing-edges.md.

Run: ``python -m pytest plugins/hoplite/hooks/test_edge_grammar.py``
"""

from __future__ import annotations

import pytest

from edge_grammar import (
    TARGET_RE,
    frontmatter_edge_targets,
    inline_wikilinks,
    validate_target,
)

# --- valid targets ------------------------------------------------------------

VALID = [
    "circle",                       # bare page
    "lib/shapes:circle",            # namespace:page
    "docs/hoplite/glossary:term",   # the canonical corpus form (multi-segment namespace)
    "refines::circle",              # stereotype
    "refines::lib/shapes:circle",   # stereotype + namespace (the :: / : combo)
    "refines::docs/hoplite/glossary:term",  # stereotype + multi-segment namespace
    "circle#properties",            # section
    "circle#properties#radius",     # nested section
    "circle#^radius-def",           # block
    "refines::circle#properties",   # stereotype + page + section
    "ghost:draft-idea",             # ghost is a namespace
    "refines::ghost:draft-idea",    # stereotyped ghost
    "kind",                         # bare slug
    "circle.md",                    # dots are ordinary — .md is not special
    "contrast::kind.md",            # stereotype + dotted page
    "my.file.name.xyz",             # several dots, still one page name
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
    ("a::b::c", "more than one"),
    ("::circle", "empty stereotype"),
    ("circle::", "empty target after"),
    ("foo!bar", "embed"),
    ("docs/hoplite/hoplite.md", "does not match"),  # missing namespace colon
    ("circle/area", "does not match"),               # subpages are gone
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
    assert validate_target("a::b::c|shown", inline=True) is not None


def test_structural_fallback_for_odd_shapes() -> None:
    assert validate_target("a:b:c:d") is not None  # too many namespace colons


def test_md_extension_is_optional() -> None:
    # `.md` is an ordinary segment, not a constraint: both forms are valid
    assert validate_target("circle.md") is None
    assert validate_target("circle") is None
    assert validate_target("contrast::kind.md") is None


# --- the grammar regex, tested independently of validate_target ----------------

REGEX_MATCHES = [
    "circle",
    "lib/shapes:circle",
    "docs/hoplite/glossary:term",
    "refines::circle",
    "refines::lib/shapes:circle",
    "refines::docs/hoplite/glossary:term",
    "circle#properties",
    "circle#properties#radius",
    "circle#^radius-def",
    "refines::circle#properties",  # stereotype + page + anchor
    "ghost:draft-idea",
    "refines::ghost:draft-idea",
    "circle.md",            # dots are ordinary
    "contrast::kind.md",
    "my.file.name.xyz",
    "#properties",          # same-page section, no page (nav link)
    "#^block-id",           # same-page block
]

REGEX_REJECTS = [
    "",                     # no page
    "circle|shown",         # `|` is not a name char
    "foo!bar",              # `!` is not a name char
    "::circle",             # empty stereotype
    "circle::",             # empty page
    "a::b::c",              # two stereotype separators
    "a:b:c:d",              # multiple namespace colons
    "lib/shapes:",          # namespace, no page
    "docs/hoplite/hoplite.md",  # slash in page, no namespace colon
    "circle/area",          # subpages are gone
    "ghost/draft",          # ghost must use the colon namespace
    "../parent",            # relative navigation is gone
    "/child",               # leading slash is gone
    "refines::#section",    # a stereotype needs a page, not a bare anchor
    "café",                 # non-ASCII is outside the strict NAME set
    "circle#",              # trailing anchor, empty heading
]


@pytest.mark.parametrize("target", REGEX_MATCHES)
def test_regex_accepts(target: str) -> None:
    assert TARGET_RE.match(target) is not None, target


@pytest.mark.parametrize("target", REGEX_REJECTS)
def test_regex_rejects(target: str) -> None:
    assert TARGET_RE.match(target) is None, target


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
    msg = validate_target('"a::b::c"')
    assert msg is not None and "more than one" in msg


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


# --- edge cases ---------------------------------------------------------------


def test_whitespace_is_trimmed() -> None:
    assert validate_target("  circle  ") is None


def test_anchor_only_is_valid_not_a_false_positive() -> None:
    # same-page nav links are valid targets, not malformed edges — the inline
    # scanner sees every [[...]] and must not flag [[#summary]]
    assert validate_target("#summary") is None
    assert validate_target("#^block") is None
    assert validate_target("#summary", inline=True) is None


def test_inline_stereotype_with_display() -> None:
    assert validate_target("refines::circle|shown", inline=True) is None


def test_missing_namespace_colon_is_rejected() -> None:
    # subpages are gone, so `/` lives only inside a namespace (colon-terminated).
    # a slash path with no colon has no parseable page name, so it is rejected —
    # the mis-address is caught structurally, no resolver needed.
    assert validate_target("docs/notes/foo.md") is not None
    assert validate_target("docs/notes:foo.md") is None


def test_empty_flow_list() -> None:
    assert frontmatter_edge_targets(["edges: []"]) == []


def test_trailing_comma_in_flow() -> None:
    assert frontmatter_edge_targets(["edges: [a, b,]"]) == ["a", "b"]


def test_block_list_with_blank_line() -> None:
    assert frontmatter_edge_targets(["edges:", "  - a", "", "  - b"]) == ["a", "b"]


def test_empty_block_list() -> None:
    assert frontmatter_edge_targets(["edges:", "title: t"]) == []


def test_inline_embed_with_stereotype_and_display() -> None:
    assert inline_wikilinks("![[refines::circle|shown]]") == [("refines::circle|shown", 1)]
    assert validate_target("refines::circle|shown", inline=True) is None


def test_inline_nav_link_extracted_and_valid() -> None:
    assert inline_wikilinks("jump to [[#summary]] below") == [("#summary", 1)]
    assert validate_target("#summary", inline=True) is None
