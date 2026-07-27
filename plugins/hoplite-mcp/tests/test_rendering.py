"""Tests for the text an agent reads.

Every string a caller sees is written in ``rendering``, so every test of wording is here.
The walk's own tests assert which record it produced, never how that record reads.
"""

from __future__ import annotations

import pytest

from hoplite_catalog.contents import (
    Directory,
    File,
    ForeignDirectory,
    ForeignFile,
    Report,
    UnlistableDirectory,
    UnreadableFile,
)
from hoplite_catalog.documents import Document, Entry, Unreadable
from hoplite_catalog.refusals import (
    Missing,
    NoSuchKeys,
    NotAList,
    NotAString,
    NotMarkdown,
    OutsideRoot,
    Refusal,
    ResolvesOutside,
    UnknownTool,
)
from hoplite_catalog.rendering import (
    render,
    render_refusal,
    render_report,
    render_vocabulary,
)
from hoplite_catalog.vocabulary import KeyUse


def _report(
    tree: tuple[Directory | ForeignDirectory | UnlistableDirectory, ...] = (),
    others: tuple[File | ForeignFile | UnreadableFile, ...] = (),
    documents: tuple[Document, ...] = (),
) -> Report:
    return Report(tree=tree, others=others, documents=documents)


class TestRender:
    def test_properties_follow_the_path_one_per_line(self) -> None:
        entry = Entry(path="docs/a.md", frontmatter=("title: A", "tags: [x]"))
        assert render([entry]) == "docs/a.md\ntitle: A\ntags: [x]"

    def test_no_fences_are_emitted(self) -> None:
        assert "---" not in render([Entry(path="docs/a.md", frontmatter=("title: A",))])

    def test_document_without_frontmatter_is_its_path_alone(self) -> None:
        assert render([Entry(path="docs/a.md", frontmatter=None)]) == "docs/a.md"

    def test_an_empty_block_renders_as_the_path_alone(self) -> None:
        assert render([Entry(path="docs/a.md", frontmatter=())]) == "docs/a.md"

    def test_entries_are_separated_by_a_blank_line(self) -> None:
        entries = [
            Entry(path="docs/a.md", frontmatter=("title: A",)),
            Entry(path="docs/b.md", frontmatter=None),
        ]
        assert render(entries) == "docs/a.md\ntitle: A\n\ndocs/b.md"

    def test_a_blank_line_inside_a_block_cannot_split_a_record(self) -> None:
        # Otherwise the blank-line separator would turn one document into two records.
        entry = Entry(path="docs/a.md", frontmatter=("title: A", "   ", "tags: [x]"))
        assert render([entry]) == "docs/a.md\ntitle: A\ntags: [x]"

    def test_a_frontmatter_comment_cannot_forge_a_heading(self) -> None:
        # The report's only group boundary is a leading `#`, so a comment emitted verbatim
        # would read as a fourth group.
        entry = Entry(path="docs/a.md", frontmatter=("# documents", "title: A"))
        assert render([entry]) == "docs/a.md\ntitle: A"

    def test_a_document_renders_the_same_projected_and_not(self) -> None:
        # Both paths read the grouping from one scanner, so the projection cannot keep a
        # line the plain listing drops.
        entry = Entry(path="docs/a.md", frontmatter=("# a note", "title: A"))
        assert render([entry]) == render([entry.projected(frozenset({"title"}))])

    def test_an_unreadable_document_puts_its_reason_where_properties_would_be(self) -> None:
        unreadable = Unreadable(path="docs/a.md", reason="cannot be read (not UTF-8 text)")
        assert render([unreadable]) == "docs/a.md\ncannot be read (not UTF-8 text)"

    def test_no_entries_renders_empty(self) -> None:
        assert render([]) == ""


class TestRenderReport:
    TREE = (
        Directory(path="docs", depth=0, documents=0),
        Directory(path="docs/glossary", depth=1, documents=2),
        Directory(path="docs/glossary/deep", depth=2, documents=1),
    )

    def test_the_three_groups_come_in_order_under_their_headings(self) -> None:
        report = _report(
            self.TREE,
            (File(path="docs/graph.pdf"),),
            (Entry(path="docs/a.md", frontmatter=("title: A",)),),
        )
        assert render_report(report) == (
            "# directories (documents directly in each)\n"
            "docs/ 0\n"
            "  glossary/ 2\n"
            "    deep/ 1\n"
            "\n"
            "# other files\n"
            "docs/graph.pdf\n"
            "\n"
            "# documents\n"
            "docs/a.md\n"
            "title: A"
        )

    def test_the_root_line_carries_the_path_and_children_carry_names(self) -> None:
        # Names are what make the subtree cheap enough to lead with; the root line is
        # where the caller reads off which folder it is looking at.
        report = render_report(_report(self.TREE))
        assert "docs/ 0" in report
        assert "  glossary/ 2" in report

    def test_the_corpus_root_is_named_by_the_path_it_carries(self) -> None:
        # `Corpus.path_of` returns `.` for the root, so the root line always has a name.
        assert "./ 0" in render_report(_report((Directory(path=".", depth=0, documents=0),)))

    def test_an_empty_group_says_none(self) -> None:
        # A folder holding no documents is a real answer, not an error.
        report = render_report(_report((Directory(path="docs", depth=0, documents=0),)))
        assert report.endswith("# other files\nnone\n\n# documents\nnone")

    def test_a_foreign_folder_is_named_as_unlistable(self) -> None:
        report = render_report(_report((ForeignDirectory(path="docs/external", depth=1),)))
        assert "  external/ links outside the corpus" in report

    def test_an_unlistable_folder_says_so_on_its_own_line(self) -> None:
        report = render_report(_report((UnlistableDirectory(path="docs/closed", depth=1),)))
        assert "  closed/ cannot be listed" in report

    def test_a_pdf_is_distinguishable_from_a_frontmatterless_document(self) -> None:
        # Both render as a bare path, so only the heading tells them apart.
        report = render_report(
            _report(
                (Directory(path="docs", depth=0, documents=1),),
                (File(path="docs/graph.pdf"),),
                (Entry(path="docs/bare.md", frontmatter=None),),
            )
        )
        assert "# other files\ndocs/graph.pdf" in report
        assert "# documents\ndocs/bare.md" in report

    def test_an_other_file_leaving_the_corpus_carries_the_directory_wording(self) -> None:
        # One phrase for the whole report: a file and a folder that leave say the same thing.
        report = render_report(_report(others=(ForeignFile(path="docs/leak.pdf"),)))
        assert "# other files\ndocs/leak.pdf links outside the corpus" in report

    def test_an_unreachable_other_file_says_so_on_its_own_line(self) -> None:
        # A symlink loop or a share that went away. The file is named either way, because a
        # file a caller can see on disk must not go missing from the listing.
        report = render_report(_report(others=(UnreadableFile(path="docs/loop.pdf"),)))
        assert "# other files\ndocs/loop.pdf cannot be read" in report


class TestRenderVocabulary:
    def test_one_key_colon_count_per_line(self) -> None:
        uses = (KeyUse(key="created", documents=162), KeyUse(key="status", documents=88))
        assert render_vocabulary(uses, "docs") == "created: 162\nstatus: 88"

    def test_a_folder_with_no_frontmatter_says_so_in_words(self) -> None:
        # A real answer, not a refusal. Empty text would read as a broken tool.
        assert render_vocabulary((), "docs/bare") == "no frontmatter keys under 'docs/bare'"


class TestRenderRefusal:
    """One sentence per refusal, naming what was asked and why it cannot be answered."""

    @pytest.mark.parametrize(
        ("refusal", "expected"),
        [
            (OutsideRoot(".."), "'..' is outside the corpus root"),
            (
                ResolvesOutside("docs/external"),
                "'docs/external' resolves outside the corpus root",
            ),
            (Missing("docs/nope"), "'docs/nope' does not exist"),
            (NotMarkdown(".env"), "'.env' is not a markdown document"),
            (NotAString("under"), "'under' must be a string"),
            (NotAList("keys"), "'keys' must be a list of strings"),
            (UnknownTool("nope"), "unknown tool: 'nope'"),
            (UnknownTool(None), "unknown tool: None"),
        ],
    )
    def test_each_refusal_reads_as_a_sentence(self, refusal: Refusal, expected: str) -> None:
        assert render_refusal(refusal) == expected

    def test_the_keys_refusal_names_both_lists(self) -> None:
        # The caller's next move is the same call with a corrected `keys`, and the call
        # that refused had already read the answer.
        refusal = NoSuchKeys(under="docs", requested=("titel",), in_use=("status", "title"))
        assert render_refusal(refusal) == (
            "none of the requested keys appear in any document under 'docs': "
            "['titel']; the keys in use there are ['status', 'title']"
        )
