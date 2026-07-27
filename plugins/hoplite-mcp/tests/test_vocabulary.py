"""Tests for the frontmatter key count."""

from __future__ import annotations

from hoplite_catalog.documents import Entry
from hoplite_catalog.vocabulary import KeyUse, tally


def _entry(path: str, *lines: str) -> Entry:
    return Entry(path=path, frontmatter=lines)


class TestTally:
    def test_counts_the_documents_carrying_each_key(self) -> None:
        entries = [
            _entry("a.md", "title: A", "status: locked"),
            _entry("b.md", "title: B"),
        ]
        assert tally(entries) == (
            KeyUse(key="status", documents=1),
            KeyUse(key="title", documents=2),
        )

    def test_keys_are_ordered_alphabetically(self) -> None:
        # Deterministic text, and a caller looking for one key can scan for it.
        entries = [_entry("a.md", "zzz: 1", "aaa: 2", "mmm: 3")]
        assert [use.key for use in tally(entries)] == ["aaa", "mmm", "zzz"]

    def test_a_block_list_counts_its_key_once_and_its_items_never(self) -> None:
        # A scanner reading only the `key:` line sees an empty value; one reading raw
        # lines counts each `- "[[link]]"` as a key of its own. Neither is right.
        entries = [_entry("a.md", "cites:", '  - "[[identifiers]]"', '  - "[[facts]]"')]
        assert tally(entries) == (KeyUse(key="cites", documents=1),)

    def test_the_same_key_in_two_documents_counts_twice(self) -> None:
        entries = [_entry("a.md", "cites: x"), _entry("b.md", "cites:", "  - y")]
        assert tally(entries) == (KeyUse(key="cites", documents=2),)

    def test_a_key_repeated_in_one_document_counts_once(self) -> None:
        # The number is documents, not occurrences: it answers how much of the corpus a
        # `keys: [status]` call would return.
        entries = [_entry("a.md", "status: draft", "status: locked")]
        assert tally(entries) == (KeyUse(key="status", documents=1),)

    def test_a_document_without_frontmatter_contributes_nothing(self) -> None:
        assert tally([Entry(path="a.md", frontmatter=None)]) == ()

    def test_an_empty_block_contributes_nothing(self) -> None:
        assert tally([Entry(path="a.md", frontmatter=())]) == ()

    def test_no_documents_means_no_keys(self) -> None:
        assert tally([]) == ()

    def test_special_keys_are_counted_like_any_other(self) -> None:
        # Nothing here judges a key, so title and tags are ordinary rows.
        entries = [_entry("a.md", "title: A", "tags: [note]", "cites: x")]
        assert [use.key for use in tally(entries)] == ["cites", "tags", "title"]
