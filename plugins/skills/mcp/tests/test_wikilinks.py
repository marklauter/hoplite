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


def test_single_link() -> None:
    assert extract("see [[foo]] for details") == ["foo"]


def test_repeated_link_collapses() -> None:
    assert extract("[[foo]] and again [[foo]] and once more [[foo]]") == ["foo"]


def test_two_distinct_links_in_document_order() -> None:
    assert extract("first [[alpha]] then [[beta]]") == ["alpha", "beta"]


def test_whitespace_around_id_collapses() -> None:
    # `[[ foo ]]` and `[[foo]]` are the same id; ordering follows the
    # first occurrence in the body.
    assert extract("[[ foo ]] and later [[foo]] and [[ bar  ]]") == ["foo", "bar"]


def test_empty_capture_skipped() -> None:
    assert extract("nothing here [[]] just brackets") == []


def test_whitespace_only_capture_skipped() -> None:
    assert extract("nothing here [[   ]] just spaces") == []


def test_link_inside_fenced_code_block_extracted() -> None:
    # The indexer parses every `[[...]]` regardless of context; fenced
    # code blocks are not skipped per docs/mcp/behavior.md.
    body = "prose [[outside]]\n\n```\ncode with [[inside]] here\n```\n"
    assert extract(body) == ["outside", "inside"]


def test_path_shaped_id_extracted_verbatim() -> None:
    # Validation of the slug rule lives in ids.py; extract just hands
    # back what it captured.
    assert extract("look at [[notes/foo.md]] please") == ["notes/foo.md"]


# --- properties (hypothesis) --------------------------------------------------


@given(
    ids=st.lists(
        st.text(alphabet="abcdefghij-/", min_size=1, max_size=20),
        min_size=0,
        max_size=20,
    ),
)
def test_extract_roundtrips_token_join(ids: list[str]) -> None:
    # Alphabet excludes `]` (the regex terminator) and whitespace (which
    # the extractor strips), so every id round-trips through `[[id]]`.
    body = " ".join(f"[[{i}]]" for i in ids)
    expected: list[str] = []
    seen: set[str] = set()
    for i in ids:
        if i not in seen:
            seen.add(i)
            expected.append(i)
    assert extract(body) == expected
