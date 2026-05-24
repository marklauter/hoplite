"""Contract tests for hoplite.tools.slugify_text.

Locks in the five transforms documented at docs/mcp/tool-api.md §hoplite_slugify_text:
lowercase; whitespace → `-`; non-`[a-z0-9-]` stripped; `-+` collapsed; edges trimmed.
"""

from __future__ import annotations

import pytest

from hoplite.tools import slugify_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Foo Bar Baz", "foo-bar-baz"),
        ("foo", "foo"),
        ("FOO", "foo"),
        ("foo--bar", "foo-bar"),
        ("foo___bar", "foobar"),
        ("  foo  ", "foo"),
        ("-foo-", "foo"),
        ("foo!@#bar", "foobar"),
        ("foo bar  baz", "foo-bar-baz"),
        ("", ""),
        ("   ", ""),
        ("---", ""),
    ],
)
def test_slugify_text(raw: str, expected: str) -> None:
    assert slugify_text(raw) == expected
