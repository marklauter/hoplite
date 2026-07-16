"""Tests for hoplite.urls."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from hoplite.urls import extract


def test_empty_body_returns_empty() -> None:
    assert extract("") == []


def test_body_without_links_returns_empty() -> None:
    assert extract("just some prose with no links anywhere") == []


def test_single_https_link_carries_position() -> None:
    # `[text](url)` starts at column 5 on line 1
    assert extract("see [docs](https://example.com) here") == [
        ("https://example.com", 1, 5)
    ]


def test_http_scheme_also_matches() -> None:
    assert extract("see [legacy](http://example.com) here") == [
        ("http://example.com", 1, 5)
    ]


def test_repeated_url_keeps_first_occurrence() -> None:
    body = "[a](https://example.com) and [b](https://example.com)"
    assert extract(body) == [("https://example.com", 1, 1)]


def test_two_distinct_urls_in_document_order() -> None:
    assert extract("[a](https://alpha.org) then [b](https://beta.org)") == [
        ("https://alpha.org", 1, 1),
        ("https://beta.org", 1, 29),
    ]


def test_url_inside_fenced_code_block_skipped() -> None:
    body = "prose [outside](https://outside.com)\n\n```\nsample [inside](https://inside.com)\n```\n"
    assert extract(body) == [("https://outside.com", 1, 7)]


def test_url_inside_inline_code_skipped() -> None:
    body = "real [out](https://out.com) and sample `[in](https://in.com)` in prose"
    assert extract(body) == [("https://out.com", 1, 6)]


def test_wikilink_pattern_not_matched() -> None:
    # `[[wikilink]]` is not a markdown link — different module owns it.
    assert extract("see [[docs/notes/foo.md]] for details") == []


def test_autolink_not_matched() -> None:
    # `<https://...>` autolink syntax is out of scope day one.
    assert extract("see <https://example.com> directly") == []


def test_bare_url_not_matched() -> None:
    # A URL not wrapped in `[text](url)` is out of scope.
    assert extract("see https://example.com directly") == []


def test_url_with_query_and_fragment_captured_verbatim() -> None:
    body = "[link](https://example.com/path?query=1&q2=2#section)"
    assert extract(body) == [("https://example.com/path?query=1&q2=2#section", 1, 1)]


def test_relative_path_link_skipped() -> None:
    # `[text](../foo.md)` is a relative filesystem link, not a URL.
    assert extract("see [neighbor](../other.md) sometime") == []


def test_mailto_link_skipped() -> None:
    assert extract("contact [me](mailto:me@example.com)") == []


def test_multi_line_positions() -> None:
    body = "line one has [a](https://a.com)\nline two has [b](https://b.com)\n\nline four has [c](https://c.com)"
    assert extract(body) == [
        ("https://a.com", 1, 14),
        ("https://b.com", 2, 14),
        ("https://c.com", 4, 15),
    ]


@given(
    paths=st.lists(
        st.text(alphabet="abcdefghij", min_size=1, max_size=10),
        min_size=0,
        max_size=10,
    ),
)
def test_extract_dedupes_in_order(paths: list[str]) -> None:
    body = " ".join(f"[{p}](https://{p}.test)" for p in paths)
    expected: list[str] = []
    seen: set[str] = set()
    for p in paths:
        url = f"https://{p}.test"
        if url not in seen:
            seen.add(url)
            expected.append(url)
    extracted = [u for u, _line, _col in extract(body)]
    assert extracted == expected
