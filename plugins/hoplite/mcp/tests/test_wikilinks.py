"""Tests for hoplite.wikilinks."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from hoplite.wikilinks import extract

# --- example-based ------------------------------------------------------------


def test_empty_body_returns_empty() -> None:
    assert extract("") == []


def test_body_without_links_returns_empty() -> None:
    assert extract("just some prose with no wiki-links anywhere") == []


def test_single_link_carries_position() -> None:
    # `[[foo]]` starts at column 5 (1-indexed) on line 1
    assert extract("see [[foo]] for details") == [("foo", 1, 5)]


def test_repeated_link_keeps_first_occurrence() -> None:
    # Three occurrences of `[[foo]]`; dedup keeps the first's position
    body = "[[foo]] and again [[foo]] and once more [[foo]]"
    assert extract(body) == [("foo", 1, 1)]


def test_two_distinct_links_in_document_order() -> None:
    assert extract("first [[alpha]] then [[beta]]") == [
        ("alpha", 1, 7),
        ("beta", 1, 22),
    ]


def test_whitespace_around_target_collapses() -> None:
    # `[[ foo ]]` and `[[foo]]` are the same target; ordering follows the
    # first occurrence in the body.
    body = "[[ foo ]] and later [[foo]] and [[ bar  ]]"
    assert extract(body) == [("foo", 1, 1), ("bar", 1, 33)]


def test_empty_capture_skipped() -> None:
    assert extract("nothing here [[]] just brackets") == []


def test_whitespace_only_capture_skipped() -> None:
    assert extract("nothing here [[   ]] just spaces") == []


def test_link_inside_fenced_code_block_skipped() -> None:
    # Sample-wikilink convention: anything in a fenced block is illustration,
    # not a cross-reference. Extract skips it.
    body = "prose [[outside]]\n\n```\ncode with [[inside]] here\n```\n"
    assert extract(body) == [("outside", 1, 7)]


def test_link_inside_inline_code_skipped() -> None:
    # Same convention for inline code spans.
    body = "real [[outside]] and sample `[[inside]]` in prose"
    assert extract(body) == [("outside", 1, 6)]


def test_link_after_fenced_block_still_extracted() -> None:
    # Masking the fence shouldn't bleed into surrounding prose.
    body = "```\nfenced [[sample]]\n```\nreal [[after]] link"
    result = extract(body)
    assert result == [("after", 4, 6)]


def test_link_with_double_backtick_inline_skipped() -> None:
    body = "see ``[[double]]`` for the sample and [[real]] for the link"
    assert extract(body) == [("real", 1, 39)]


def test_path_shaped_target_extracted_verbatim() -> None:
    # Target validation lives in the walker; extract just hands back
    # what it captured.
    assert extract("look at [[notes/foo.md]] please") == [("notes/foo.md", 1, 9)]


def test_multi_line_positions() -> None:
    body = "first line has [[a]]\nsecond line has [[b]]\n\nfourth has [[c]]"
    assert extract(body) == [
        ("a", 1, 16),
        ("b", 2, 17),
        ("c", 4, 12),
    ]


# --- properties (hypothesis) --------------------------------------------------


@given(
    targets=st.lists(
        st.text(alphabet="abcdefghij-/", min_size=1, max_size=20),
        min_size=0,
        max_size=20,
    ),
)
def test_extract_dedupes_in_order(targets: list[str]) -> None:
    # Alphabet excludes `]` (the regex terminator) and whitespace (which
    # the extractor strips), so every target round-trips through `[[target]]`.
    body = " ".join(f"[[{t}]]" for t in targets)
    expected_targets: list[str] = []
    seen: set[str] = set()
    for t in targets:
        if t not in seen:
            seen.add(t)
            expected_targets.append(t)
    extracted_targets = [target for target, _line, _col in extract(body)]
    assert extracted_targets == expected_targets


@given(
    targets=st.lists(
        st.text(alphabet="abcdefghij-/", min_size=1, max_size=20),
        min_size=0,
        max_size=20,
    ),
)
def test_extract_positions_within_bounds(targets: list[str]) -> None:
    body = " ".join(f"[[{t}]]" for t in targets)
    for _target, line, column in extract(body):
        assert line >= 1
        assert column >= 1
