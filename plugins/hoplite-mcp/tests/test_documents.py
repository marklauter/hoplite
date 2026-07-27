"""Tests for the frontmatter slicer and the records it produces.

Text in, records out: nothing here needs a corpus, a ``tmp_path``, or a fake, which is
the boundary the layering contract now asserts.
"""

from __future__ import annotations

from hoplite_catalog.documents import (
    Entry,
    Property,
    Unreadable,
    group_properties,
    slice_frontmatter,
)


class TestSliceFrontmatter:
    def test_returns_the_lines_between_the_fences(self) -> None:
        lines = ["---", "title: Edge", "tags: [glossary]", "---", "", "# Edge"]
        assert slice_frontmatter(lines) == ("title: Edge", "tags: [glossary]")

    def test_no_opening_fence_is_no_block(self) -> None:
        assert slice_frontmatter(["# Edge", "prose"]) is None

    def test_empty_file_is_no_block(self) -> None:
        assert slice_frontmatter([]) is None

    def test_unterminated_block_is_no_block(self) -> None:
        # Emitting to EOF would pull the whole body into the listing.
        assert slice_frontmatter(["---", "title: Edge", "", "# Edge"]) is None

    def test_empty_block_is_kept_apart_from_no_block(self) -> None:
        assert slice_frontmatter(["---", "---", "# Edge"]) == ()

    def test_fences_match_despite_trailing_whitespace(self) -> None:
        assert slice_frontmatter(["--- ", "title: Edge", " ---", "body"]) == ("title: Edge",)

    def test_a_fence_in_the_body_is_not_reached(self) -> None:
        lines = ["---", "title: Edge", "---", "", "some prose", "---", "more prose"]
        assert slice_frontmatter(lines) == ("title: Edge",)

    def test_values_are_verbatim(self) -> None:
        # No YAML parse, so quoting, spacing, and key order survive untouched.
        lines = ["---", 'is-a:   "[[relationship]]"', "zzz: 1", "aaa: 2", "---"]
        assert slice_frontmatter(lines) == ('is-a:   "[[relationship]]"', "zzz: 1", "aaa: 2")


class TestGroupProperties:
    def test_each_key_owns_its_own_line(self) -> None:
        grouped = group_properties(["title: Edge", "status: locked"])
        assert [(prop.key, prop.lines) for prop in grouped] == [
            ("title", ("title: Edge",)),
            ("status", ("status: locked",)),
        ]

    def test_a_block_list_belongs_to_the_key_above_it(self) -> None:
        # The counterexample the vocabulary count is built on: a scanner reading only the
        # `key:` line sees an empty value, and one reading raw lines sees three keys.
        grouped = group_properties(["cites:", '  - "[[a]]"', '  - "[[b]]"'])
        assert [prop.key for prop in grouped] == ["cites"]
        assert grouped[0].lines == ("cites:", '  - "[[a]]"', '  - "[[b]]"')

    def test_an_unindented_list_item_is_still_a_continuation(self) -> None:
        # `- "[[a]]"` at column zero is legal YAML and is not a key.
        grouped = group_properties(["cites:", '- "[[a]]"'])
        assert [prop.key for prop in grouped] == ["cites"]

    def test_a_malformed_root_line_rides_with_the_key_above(self) -> None:
        grouped = group_properties(["title: Edge", "nonsense"])
        assert [prop.key for prop in grouped] == ["title"]
        assert grouped[0].lines == ("title: Edge", "nonsense")

    def test_lines_before_the_first_key_belong_to_no_property(self) -> None:
        assert group_properties(["  orphaned", "title: Edge"]) == group_properties(["title: Edge"])

    def test_an_unindented_comment_belongs_to_no_property(self) -> None:
        # A YAML comment is not a value, and emitted verbatim its `#` forges a report
        # heading. It does not ride with the key above it the way a malformed line does.
        grouped = group_properties(["title: Edge", "# a note", "status: locked"])
        assert [(prop.key, prop.lines) for prop in grouped] == [
            ("title", ("title: Edge",)),
            ("status", ("status: locked",)),
        ]

    def test_an_indented_hash_line_is_kept(self) -> None:
        # Inside a block scalar a `#` line is data, not a comment, and it is indented.
        grouped = group_properties(["summary: |", "  # a heading in the value"])
        assert grouped[0].lines == ("summary: |", "  # a heading in the value")

    def test_nothing_in_means_nothing_out(self) -> None:
        assert group_properties([]) == ()


class TestEntryProperties:
    """The grouping is derived once, at construction, and is the same answer the scanner
    gives. It used to be a method, and one `contents` call asked it four times per
    document."""

    def test_the_block_is_grouped_by_root_key(self) -> None:
        entry = Entry(path="a.md", frontmatter=("cites:", "  - x", "title: A"))
        assert entry.properties == (
            Property(key="cites", lines=("cites:", "  - x")),
            Property(key="title", lines=("title: A",)),
        )

    def test_no_block_carries_no_properties(self) -> None:
        assert Entry(path="a.md", frontmatter=None).properties == ()

    def test_an_empty_block_carries_no_properties(self) -> None:
        assert Entry(path="a.md", frontmatter=()).properties == ()

    def test_a_projection_regroups_what_it_kept(self) -> None:
        # `replace` recomputes it, so the derived field cannot go stale against the block.
        entry = Entry(path="a.md", frontmatter=("title: A", "status: locked"))
        assert entry.projected(frozenset({"title"})).properties == (
            Property(key="title", lines=("title: A",)),
        )

    def test_two_entries_with_the_same_block_are_equal(self) -> None:
        # The derived field is not compared, because it cannot disagree.
        assert Entry(path="a.md", frontmatter=("title: A",)) == Entry(
            path="a.md", frontmatter=("title: A",)
        )

    def test_an_unreadable_document_carries_no_properties(self) -> None:
        # So the reason standing in for its frontmatter never enters the key vocabulary.
        unreadable = Unreadable(path="a.md", reason="cannot be read (not UTF-8 text)")
        assert unreadable.properties == ()
        assert unreadable.projected(frozenset({"title"})) == unreadable


class TestProjected:
    FULL = Entry(
        path="docs/glossary/edge.md",
        frontmatter=(
            "title: Edge",
            'summary: "A relationship between two documents."',
            "tags: [glossary, hoplite]",
            "disjoint-with:",
            '  - "[[node]]"',
            '  - "[[claim]]"',
        ),
    )

    def test_no_keys_keeps_everything(self) -> None:
        assert self.FULL.projected(None) == self.FULL

    def test_keeps_only_the_named_properties(self) -> None:
        assert self.FULL.projected(frozenset({"title", "tags"})).frontmatter == (
            "title: Edge",
            "tags: [glossary, hoplite]",
        )

    def test_a_block_list_keeps_its_continuation_lines(self) -> None:
        assert self.FULL.projected(frozenset({"disjoint-with"})).frontmatter == (
            "disjoint-with:",
            '  - "[[node]]"',
            '  - "[[claim]]"',
        )

    def test_a_continuation_line_is_dropped_with_its_key(self) -> None:
        kept = self.FULL.projected(frozenset({"title"})).frontmatter
        assert kept == ("title: Edge",)

    def test_an_empty_key_set_leaves_an_empty_block(self) -> None:
        # Empty, not absent: the document had a block, and "projected to nothing" is not
        # the same fact as "never had one". Only the record keeps them apart — both render
        # as the path alone.
        assert self.FULL.projected(frozenset()).frontmatter == ()

    def test_an_unmatched_key_leaves_an_empty_block(self) -> None:
        assert self.FULL.projected(frozenset({"nonesuch"})).frontmatter == ()

    def test_a_document_without_frontmatter_is_untouched(self) -> None:
        bare = Entry(path="docs/a.md", frontmatter=None)
        assert bare.projected(frozenset({"title"})) == bare
        assert bare.projected(frozenset({"title"})).frontmatter is None

    def test_the_path_is_never_changed(self) -> None:
        assert self.FULL.projected(frozenset({"title"})).path == self.FULL.path
