"""Tests for hoplite.ids."""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hoplite import ids, tools
from hoplite.ids import resolve, slugify_text, validate_id

# --- slugify_text -------------------------------------------------------------


_SLUGIFY_CASES = [
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
]


@pytest.mark.parametrize(("raw", "expected"), _SLUGIFY_CASES)
def test_slugify_text(raw: str, expected: str) -> None:
    assert slugify_text(raw) == expected


@pytest.mark.parametrize("raw", [raw for raw, _ in _SLUGIFY_CASES])
def test_slugify_text_idempotent(raw: str) -> None:
    once = slugify_text(raw)
    assert slugify_text(once) == once


# --- validate_id --------------------------------------------------------------


@pytest.mark.parametrize(
    "id_str",
    [
        # Every example from docs/mcp/behavior.md#slug-and-id-rules.
        "foo.md",
        "notes/skill-composition.md",
        "journal/2026-05-24-today-was-warm.md",
        "mcp/data-model.md",
    ],
)
def test_validate_id_accepts_valid(id_str: str) -> None:
    assert validate_id(id_str) is None


@pytest.mark.parametrize(
    "id_str",
    [
        "",  # empty
        "Foo.md",  # uppercase letter
        "foo_bar.md",  # underscore
        "foo bar.md",  # whitespace
        "/foo.md",  # leading slash
        "foo.md/",  # trailing slash
        "foo//bar.md",  # double slash
        "foo",  # missing extension
        "notes/.md",  # empty segment before extension
        "foo.bar/baz.md",  # dot inside non-final segment
        "../foo.md",  # `..` segment (leading)
        "foo/../bar.md",  # `..` segment (interior traversal attempt)
        "foo.md\n",  # trailing newline — guards against `$` matching before `\n`
        "archive.tar.gz",  # multi-dot extension — single-extension only
    ],
)
def test_validate_id_rejects_invalid(id_str: str) -> None:
    with pytest.raises(ValueError, match="id does not match"):
        validate_id(id_str)


# --- resolve ------------------------------------------------------------------


def test_resolve_nested_id(tmp_path: Path) -> None:
    result = resolve("notes/skill-composition.md", tmp_path)
    assert result == tmp_path / "docs" / "notes" / "skill-composition.md"


def test_resolve_top_level_id(tmp_path: Path) -> None:
    result = resolve("foo.md", tmp_path)
    assert result == tmp_path / "docs" / "foo.md"


def test_resolve_rejects_invalid_id_before_path_math(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="id does not match"):
        resolve("../foo.md", tmp_path)


# --- re-export identity -------------------------------------------------------


def test_tools_slugify_is_ids_slugify() -> None:
    # Locks in the re-export so a future split doesn't silently fork
    # the implementation.
    assert tools.slugify_text is ids.slugify_text


# --- properties (hypothesis) --------------------------------------------------


_SEGMENT = st.from_regex(r"[a-z0-9-]{1,16}", fullmatch=True)


@given(segments=st.lists(_SEGMENT, min_size=1, max_size=4))
def test_resolve_stays_under_docs(segments: list[str]) -> None:
    # Compose an id from bounded segments joined by `/` and a `.md`
    # suffix so the result passes validate_id. The property: resolve
    # always produces a path under <corpus>/docs/. See
    # docs/mcp/behavior.md#slug-and-id-rules for the structural
    # guarantee the regex provides.
    id_str = "/".join(segments) + ".md"
    corpus_root = Path("/tmp/corpus")
    resolved = resolve(id_str, corpus_root)
    assert resolved.is_relative_to(corpus_root / "docs")
