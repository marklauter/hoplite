"""Tests for the edge-target grammar — the executable form of expressing-edges.md.

Obsidian-native grammar: a target is a slug, an optional folder-path prefix, and an
optional anchor. No colons; the folder path is the namespace. In frontmatter an edge
is a property whose value is a quoted wikilink, and the key is the stereotype.

Run: ``python -m pytest plugins/hoplite/hooks/test_edge_grammar.py``
"""

from __future__ import annotations

import pytest

from edge_grammar import (
    TARGET_RE,
    frontmatter_wikilink_targets,
    inline_edges,
    inline_wikilinks,
    validate_target,
)

# --- valid targets ------------------------------------------------------------

VALID = [
    "circle",                       # bare slug
    "lib/shapes/circle",            # folder-path prefix
    "docs/hoplite/glossary/term",   # the canonical corpus form
    "circle#properties",            # section
    "circle#properties#radius",     # nested section
    "circle#cross sections",        # section label keeps its spaces
    "circle#^radius-def",           # block
    "circle.md",                    # dots are ordinary — .md is not special
    "my.file.name.xyz",             # several dots, still one slug
    "draft-idea",                   # a ghost is a plain, not-yet-resolved slug
    "#summary",                     # same-page section (nav link)
    "#^block-id",                   # same-page block
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
    ("docs/hoplite:term", "colon"),     # no colons — the folder path is the namespace
    ("a:b:c", "colon"),
    ("refines::circle", "stereotype"),  # stereotypes are frontmatter keys, not targets
    ("circle|shown", "body-only"),      # display is body-only
    ("foo!bar", "body-only"),           # embed is body-only
    ("café", "does not match"),         # non-ASCII is outside the strict segment set
    ("circle#", "does not match"),      # trailing anchor, empty heading
    ("circle/", "does not match"),      # trailing slash, no second segment
    ("circle#^", "does not match"),     # empty block id
]


@pytest.mark.parametrize(("target", "needle"), INVALID)
def test_invalid_reports_specific(target: str, needle: str) -> None:
    msg = validate_target(target)
    assert msg is not None, target
    assert needle in msg, f"{target!r} -> {msg!r}"


def test_stereotype_colon_points_to_frontmatter_key() -> None:
    msg = validate_target("cites::circle")
    assert msg is not None and "stereotype" in msg


def test_display_text_rejected_in_frontmatter() -> None:
    msg = validate_target("circle|shown")
    assert msg is not None and "body-only" in msg


def test_md_extension_is_optional() -> None:
    assert validate_target("circle.md") is None
    assert validate_target("circle") is None


# --- the grammar regex, tested independently of validate_target ----------------

REGEX_MATCHES = [
    "circle",
    "lib/shapes/circle",
    "docs/hoplite/glossary/term",
    "circle#properties",
    "circle#properties#radius",
    "circle#cross sections",
    "circle#^radius-def",
    "circle.md",
    "my.file.name.xyz",
    "draft-idea",
    "#summary",
    "#^block-id",
]

REGEX_REJECTS = [
    "",                         # no page
    "docs/hoplite:term",        # colons are gone
    "refines::circle",          # stereotype colons are gone
    "a:b:c:d",                  # any colon
    "circle|shown",             # `|` is not a segment char
    "foo!bar",                  # `!` is not a segment char
    "café",                     # non-ASCII
    "circle/",                  # trailing slash, no second segment
    "/circle",                  # leading slash
    "circle#",                  # trailing anchor, empty heading
    "circle#^",                 # empty block id
    "#",                        # bare hash, no label
]


@pytest.mark.parametrize("target", REGEX_MATCHES)
def test_regex_accepts(target: str) -> None:
    assert TARGET_RE.match(target) is not None, target


@pytest.mark.parametrize("target", REGEX_REJECTS)
def test_regex_rejects(target: str) -> None:
    assert TARGET_RE.match(target) is None, target


def test_section_label_allows_spaces() -> None:
    assert TARGET_RE.match("note#A Heading With Spaces") is not None
    assert validate_target("circle#cross sections") is None


def test_block_id_is_dash_and_alnum_only() -> None:
    # Obsidian block ids are letters, numbers, dashes — underscore is not one
    assert TARGET_RE.match("circle#^radius-def") is not None
    assert TARGET_RE.match("circle#^radius_def") is None
    # but a section label tolerates the underscore
    assert TARGET_RE.match("circle#radius_def") is not None


def test_folder_path_is_the_namespace() -> None:
    assert validate_target("docs/hoplite/term") is None
    assert validate_target("docs/hoplite:term") is not None


# --- frontmatter wikilink extraction ------------------------------------------


def test_fm_scalar() -> None:
    assert frontmatter_wikilink_targets(['cites: "[[circle]]"']) == [("circle", True, 0)]


def test_fm_flow_list() -> None:
    got = frontmatter_wikilink_targets(['cites: ["[[a]]", "[[b]]"]'])
    assert got == [("a", True, 0), ("b", True, 0)]


def test_fm_block_list() -> None:
    lines = ["contrast:", '  - "[[x]]"', '  - "[[y]]"']
    assert frontmatter_wikilink_targets(lines) == [("x", True, 1), ("y", True, 2)]


def test_fm_unquoted_is_flagged() -> None:
    assert frontmatter_wikilink_targets(["cites: [[circle]]"]) == [("circle", False, 0)]


def test_fm_special_keys_skipped() -> None:
    # title/summary/aliases/tags are read by meaning, not edges
    assert frontmatter_wikilink_targets(['title: "[[foo]]"']) == []
    assert frontmatter_wikilink_targets(['aliases: ["[[old]]"]']) == []


def test_fm_scalar_properties_ignored() -> None:
    assert frontmatter_wikilink_targets(["status: draft", "created: 2026-05-25"]) == []


def test_fm_multiple_edges() -> None:
    lines = ['refines: "[[pi]]"', 'cites: ["[[a]]", "[[b]]"]']
    assert frontmatter_wikilink_targets(lines) == [
        ("pi", True, 0),
        ("a", True, 1),
        ("b", True, 1),
    ]


def test_fm_extracted_targets_validate() -> None:
    lines = ['cites: ["[[circle]]", "[[docs/hoplite/glossary/term]]"]']
    for target, quoted, _ in frontmatter_wikilink_targets(lines):
        assert quoted, target
        assert validate_target(target) is None, target


# --- inline extraction --------------------------------------------------------


def test_inline_basic() -> None:
    assert inline_wikilinks("see [[circle]] here") == [("circle", 1)]


def test_inline_path_link() -> None:
    assert inline_wikilinks("[[docs/hoplite/glossary/term]]") == [("docs/hoplite/glossary/term", 1)]


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
    assert inline_wikilinks("[[circle|shown]]") == [("circle|shown", 1)]
    assert validate_target("circle|shown", inline=True) is None


def test_inline_nav_link_extracted_and_valid() -> None:
    assert inline_wikilinks("jump to [[#summary]] below") == [("#summary", 1)]
    assert validate_target("#summary", inline=True) is None


# --- edge cases ---------------------------------------------------------------


def test_whitespace_is_trimmed() -> None:
    assert validate_target("  circle  ") is None


def test_surrounding_quotes_stripped() -> None:
    assert validate_target('"circle"') is None


def test_anchor_only_is_valid_not_a_false_positive() -> None:
    assert validate_target("#summary") is None
    assert validate_target("#^block") is None


# --- inline stereotypes (typed inline edges) ----------------------------------


def test_inline_edges_bare_is_untyped() -> None:
    assert inline_edges("see [[circle]] here") == [("circle", None, 1)]


def test_inline_edges_html_comment() -> None:
    assert inline_edges("[[circle]]<!--refines-->") == [("circle", "refines", 1)]


def test_inline_edges_obsidian_comment() -> None:
    assert inline_edges("[[circle]]%%refines%%") == [("circle", "refines", 1)]


def test_inline_edges_dataview_field() -> None:
    assert inline_edges("[refines:: [[circle]]]") == [("circle", "refines", 1)]


def test_inline_edges_comment_with_spaces() -> None:
    assert inline_edges("[[circle]] <!-- refines -->") == [("circle", "refines", 1)]


def test_inline_edges_comment_needs_adjacency() -> None:
    # a comment separated by words does not type the link
    assert inline_edges("[[circle]] and also <!--refines-->") == [("circle", None, 1)]


def test_inline_edges_embed_marker_with_stereotype() -> None:
    assert inline_edges("![[circle]]<!--refines-->") == [("circle", "refines", 1)]


def test_inline_edges_anchored_target_with_stereotype() -> None:
    assert inline_edges("[[circle#properties]]<!--refines-->") == [("circle#properties", "refines", 1)]


def test_inline_edges_skips_code() -> None:
    assert inline_edges("an example `[[circle]]<!--refines-->` is skipped") == []


def test_inline_edges_multiple_in_order() -> None:
    body = "[[a]]<!--x-->\nand [[b]] bare\n[c:: [[d]]]"
    assert inline_edges(body) == [("a", "x", 1), ("b", None, 2), ("d", "c", 3)]


def test_inline_edges_extracts_target_for_validation() -> None:
    # the stereotype wrapper never affects which target is extracted or its validity
    edges = inline_edges("[[circle]]<!--refines-->\n[bad:: [[x/]]]")
    assert edges == [("circle", "refines", 1), ("x/", "bad", 2)]
    assert validate_target("circle") is None
    assert validate_target("x/") is not None
