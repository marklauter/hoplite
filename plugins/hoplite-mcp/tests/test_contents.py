"""Tests for the directory walk and the frontmatter slicer."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from hoplite_catalog.contents import (
    Directory,
    Entry,
    ForeignDirectory,
    UnlistableDirectory,
    Unreadable,
    collect,
    group_properties,
    markdown_in,
    other_files,
    read_entry,
    render,
    render_report,
    resolve_under,
    slice_frontmatter,
    subdirectories,
    walk,
)


def _write(path: Path, text: str, *, encoding: str = "utf-8", newline: str = "\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding=encoding, newline=newline)
    return path


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

    def test_no_entries_renders_empty(self) -> None:
        assert render([]) == ""


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

    def test_an_empty_key_set_leaves_the_path_alone(self) -> None:
        projected = self.FULL.projected(frozenset())
        assert projected.frontmatter is None
        assert render([projected]) == "docs/glossary/edge.md"

    def test_an_unmatched_key_leaves_the_path_alone(self) -> None:
        assert self.FULL.projected(frozenset({"nonesuch"})).frontmatter is None

    def test_a_document_without_frontmatter_is_untouched(self) -> None:
        bare = Entry(path="docs/a.md", frontmatter=None)
        assert bare.projected(frozenset({"title"})) == bare

    def test_the_path_is_never_changed(self) -> None:
        assert self.FULL.projected(frozenset({"title"})).path == self.FULL.path


class TestReadEntry:
    def test_path_is_corpus_relative_and_posix(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "glossary" / "edge.md", "---\ntitle: Edge\n---\n")
        entry = read_entry(tmp_path, tmp_path / "docs" / "glossary" / "edge.md")
        assert entry.path == "docs/glossary/edge.md"
        assert entry.frontmatter == ("title: Edge",)

    def test_byte_order_mark_does_not_hide_the_opening_fence(self, tmp_path: Path) -> None:
        _write(tmp_path / "a.md", "---\ntitle: A\n---\n", encoding="utf-8-sig")
        assert read_entry(tmp_path, tmp_path / "a.md").frontmatter == ("title: A",)

    def test_crlf_slices_the_same_as_lf(self, tmp_path: Path) -> None:
        _write(tmp_path / "a.md", "---\ntitle: A\n---\n\n# A\n", newline="\r\n")
        assert read_entry(tmp_path, tmp_path / "a.md").frontmatter == ("title: A",)

    def test_non_ascii_survives(self, tmp_path: Path) -> None:
        _write(tmp_path / "a.md", "---\nsummary: a kernel — the genus\n---\n")
        assert read_entry(tmp_path, tmp_path / "a.md").frontmatter == (
            "summary: a kernel — the genus",
        )

    def test_a_symlinked_document_reports_the_link_path(self, tmp_path: Path) -> None:
        # docs/specs/frontmatter.md is a symlink into plugins/hoplite-skills/references/.
        # The listing must report the path the corpus links to, not where the bytes live.
        target = _write(tmp_path / "references" / "frontmatter.md", "---\ntitle: F\n---\n")
        link = tmp_path / "docs" / "specs" / "frontmatter.md"
        link.parent.mkdir(parents=True)
        try:
            link.symlink_to(target)
        except OSError as exc:  # Windows needs developer mode or elevation
            pytest.skip(f"cannot create a symlink here: {exc}")

        entry = read_entry(tmp_path, link)
        assert entry.path == "docs/specs/frontmatter.md"
        assert entry.frontmatter == ("title: F",)


class TestMarkdownIn:
    def test_finds_the_documents_directly_in_the_folder(self, tmp_path: Path) -> None:
        _write(tmp_path / "b.md", "")
        _write(tmp_path / "a.md", "")
        _write(tmp_path / "sub" / "c.md", "")
        assert [path.name for path in markdown_in(tmp_path)] == ["a.md", "b.md"]

    def test_an_empty_folder_holds_no_documents(self, tmp_path: Path) -> None:
        assert markdown_in(tmp_path) == ()

    def test_a_directory_named_like_a_document_is_not_one(self, tmp_path: Path) -> None:
        # Obsidian corpora do produce these. Counted as a document it would be tallied in
        # the subtree that also lists it as a directory, then handed to read_entry.
        (tmp_path / "sub.md").mkdir()
        _write(tmp_path / "real.md", "")
        assert [path.name for path in markdown_in(tmp_path)] == ["real.md"]

    def test_a_dangling_link_is_still_a_document(self, tmp_path: Path) -> None:
        # is_file() would drop it here and collect would never refuse it, so a document
        # visible on disk would vanish from the listing. The filter is `not is_dir()`.
        try:
            (tmp_path / "dangling.md").symlink_to(tmp_path / "never-created.md")
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert [path.name for path in markdown_in(tmp_path)] == ["dangling.md"]


class TestOtherFiles:
    def test_non_markdown_files_are_reported_by_path(self, tmp_path: Path) -> None:
        # Hiding them makes the listing lie about what the folder holds.
        _write(tmp_path / "docs" / "a.md", "")
        _write(tmp_path / "docs" / "notes.txt", "")
        _write(tmp_path / "docs" / "graph.pdf", "")
        assert other_files(tmp_path, tmp_path / "docs") == ("docs/graph.pdf", "docs/notes.txt")

    def test_markdown_is_never_reported_here(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "a.md", "")
        assert other_files(tmp_path, tmp_path / "docs") == ()

    def test_subfolders_are_not_reported_here(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "sub" / "deep.pdf", "")
        assert other_files(tmp_path, tmp_path / "docs") == ()

    def test_a_directory_is_never_an_other_file(self, tmp_path: Path) -> None:
        # Including one named like a document, which is a directory in both groups' eyes.
        (tmp_path / "docs" / "sub.md").mkdir(parents=True)
        (tmp_path / "docs" / "plain").mkdir()
        assert other_files(tmp_path, tmp_path / "docs") == ()

    def test_a_link_out_of_the_corpus_is_marked(self, tmp_path: Path) -> None:
        # A bare path here asserts the file is in the corpus, and for this one that is
        # false. Only the name would leak, never the bytes — but the claim is still untrue.
        outside = tmp_path.parent / f"{tmp_path.name}-outside"
        outside.mkdir(exist_ok=True)
        _write(outside / "secret.pdf", "")
        (tmp_path / "docs").mkdir()
        try:
            (tmp_path / "docs" / "leak.pdf").symlink_to(outside / "secret.pdf")
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        listed = other_files(tmp_path, tmp_path / "docs")
        assert listed == ("docs/leak.pdf links outside the corpus",)
        assert "secret.pdf" not in listed[0]
        assert str(outside) not in listed[0]

    def test_a_link_inside_the_corpus_is_not_marked(self, tmp_path: Path) -> None:
        _write(tmp_path / "assets" / "graph.pdf", "")
        (tmp_path / "docs").mkdir()
        try:
            (tmp_path / "docs" / "graph.pdf").symlink_to(tmp_path / "assets" / "graph.pdf")
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert other_files(tmp_path, tmp_path / "docs") == ("docs/graph.pdf",)

    def test_a_dangling_link_is_reported_rather_than_dropped(self, tmp_path: Path) -> None:
        # It is neither a file nor a directory, so is_file() would leave it in no group.
        (tmp_path / "docs").mkdir()
        try:
            (tmp_path / "docs" / "gone.pdf").symlink_to(tmp_path / "never-created.pdf")
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert other_files(tmp_path, tmp_path / "docs") == ("docs/gone.pdf",)

    def test_hidden_files_are_skipped_like_hidden_directories(self, tmp_path: Path) -> None:
        # With the corpus root as the default, listing them put .env and .gitignore in a
        # corpus report while .git/ was correctly absent from the tree beside them.
        _write(tmp_path / "docs" / ".env", "")
        _write(tmp_path / "docs" / ".gitignore", "")
        _write(tmp_path / "docs" / "notes.txt", "")
        assert other_files(tmp_path, tmp_path / "docs") == ("docs/notes.txt",)

    def test_a_hidden_markdown_file_is_still_a_document(self, tmp_path: Path) -> None:
        # It is addressable by a wikilink, so it belongs in the documents group, not here.
        _write(tmp_path / "docs" / ".draft.md", "")
        assert other_files(tmp_path, tmp_path / "docs") == ()
        assert [path.name for path in markdown_in(tmp_path / "docs")] == [".draft.md"]

    def test_every_entry_lands_in_exactly_one_group(self, tmp_path: Path) -> None:
        # The three groups partition the directory: subdirectory, document, or other file.
        _write(tmp_path / "docs" / "a.md", "")
        _write(tmp_path / "docs" / "b.markdown", "")
        _write(tmp_path / "docs" / "c.pdf", "")
        (tmp_path / "docs" / "sub.md").mkdir()
        (tmp_path / "docs" / "plain").mkdir()

        directories = {path.name for path in subdirectories(tmp_path / "docs")}
        documents = {path.name for path in markdown_in(tmp_path / "docs")}
        others = {path.rsplit("/", 1)[-1] for path in other_files(tmp_path, tmp_path / "docs")}

        assert directories == {"sub.md", "plain"}
        assert documents == {"a.md"}
        assert others == {"b.markdown", "c.pdf"}
        assert directories | documents | others == {
            path.name for path in (tmp_path / "docs").iterdir()
        }


class TestSubdirectories:
    def test_lists_child_directories_in_order(self, tmp_path: Path) -> None:
        for name in ("z", "a", "m"):
            (tmp_path / name).mkdir()
        _write(tmp_path / "a.md", "")
        assert [path.name for path in subdirectories(tmp_path)] == ["a", "m", "z"]

    @pytest.mark.parametrize("name", [".git", ".venv", ".obsidian"])
    def test_hidden_directories_are_never_walked_into(self, tmp_path: Path, name: str) -> None:
        # A leading dot is the filesystem's own "not content" marker, and .git and .venv
        # are each thousands of directories that no corpus addresses.
        (tmp_path / name).mkdir()
        (tmp_path / "docs").mkdir()
        assert [path.name for path in subdirectories(tmp_path)] == ["docs"]

    def test_a_dot_inside_the_name_is_not_hidden(self, tmp_path: Path) -> None:
        (tmp_path / "v1.2").mkdir()
        assert [path.name for path in subdirectories(tmp_path)] == ["v1.2"]


class TestWalk:
    def test_reports_the_folder_itself_first(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "a.md", "")
        assert walk(tmp_path, tmp_path / "docs") == (Directory(path="docs", depth=0, documents=1),)

    def test_recurses_to_full_depth_in_pre_order(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "glossary" / "a.md", "")
        _write(tmp_path / "docs" / "glossary" / "deep" / "b.md", "")
        _write(tmp_path / "docs" / "notes" / "c.md", "")
        assert [(node.path, node.depth) for node in walk(tmp_path, tmp_path / "docs")] == [
            ("docs", 0),
            ("docs/glossary", 1),
            ("docs/glossary/deep", 2),
            ("docs/notes", 1),
        ]

    def test_counts_are_direct_not_cumulative(self, tmp_path: Path) -> None:
        # The count is what a caller gets by asking for that folder, which is what they
        # are budgeting against.
        _write(tmp_path / "docs" / "sub" / "a.md", "")
        _write(tmp_path / "docs" / "sub" / "b.md", "")
        counts = {node.path: node for node in walk(tmp_path, tmp_path / "docs")}
        assert counts["docs"] == Directory(path="docs", depth=0, documents=0)
        assert counts["docs/sub"] == Directory(path="docs/sub", depth=1, documents=2)

    def test_a_folder_holding_no_documents_is_reported_with_zero(self, tmp_path: Path) -> None:
        (tmp_path / "docs").mkdir()
        assert walk(tmp_path, tmp_path / "docs") == (Directory(path="docs", depth=0, documents=0),)

    def test_it_does_not_open_any_document(self, tmp_path: Path) -> None:
        # The walk is at stat level, so an unreadable document costs the subtree nothing.
        (tmp_path / "docs").mkdir()
        try:
            (tmp_path / "docs" / "dangling.md").symlink_to(tmp_path / "docs" / "never-created.md")
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert walk(tmp_path, tmp_path / "docs")[0].path == "docs"

    def test_is_deterministic(self, tmp_path: Path) -> None:
        for name in ("z", "m", "a"):
            _write(tmp_path / "docs" / name / "a.md", "")
        assert walk(tmp_path, tmp_path / "docs") == walk(tmp_path, tmp_path / "docs")

    def test_a_hidden_folder_and_its_whole_subtree_stay_out(self, tmp_path: Path) -> None:
        # The bound: walking a repository must not report .git or .venv, which are each
        # thousands of directories deep and hold nothing the corpus addresses.
        _write(tmp_path / ".git" / "objects" / "ab" / "x.md", "")
        _write(tmp_path / "docs" / "a.md", "")
        assert [node.path for node in walk(tmp_path, tmp_path)] == [".", "docs"]

    def test_naming_a_hidden_folder_outright_still_walks_it(self, tmp_path: Path) -> None:
        # The rule is about what a walk wanders into, not about what may be asked for.
        _write(tmp_path / ".github" / "workflows" / "ci.md", "")
        assert [node.path for node in walk(tmp_path, tmp_path / ".github")] == [
            ".github",
            ".github/workflows",
        ]

    def test_a_directory_named_like_a_document_is_a_directory_not_a_count(
        self, tmp_path: Path
    ) -> None:
        # It appeared twice before: as a directory node and in its parent's count.
        (tmp_path / "docs" / "sub.md").mkdir(parents=True)
        assert walk(tmp_path, tmp_path / "docs") == (
            Directory(path="docs", depth=0, documents=0),
            Directory(path="docs/sub.md", depth=1, documents=0),
        )

    def test_the_corpus_root_is_walkable(self, tmp_path: Path) -> None:
        # Someone whose corpus is the working directory has no wrapper folder to name.
        _write(tmp_path / "docs" / "a.md", "")
        assert walk(tmp_path, tmp_path)[0] == Directory(path=".", depth=0, documents=0)

    def test_a_symlinked_folder_pointing_out_of_the_root_is_named_not_walked(
        self, tmp_path: Path
    ) -> None:
        # Without this the folder shows as walkable and fails only on the second call.
        outside = tmp_path.parent / f"{tmp_path.name}-outside"
        outside.mkdir(exist_ok=True)
        _write(outside / "secret.md", "---\ntitle: Secret\n---\n")
        (tmp_path / "docs").mkdir()
        try:
            (tmp_path / "docs" / "external").symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        nodes = walk(tmp_path, tmp_path / "docs")
        assert nodes[1] == ForeignDirectory(path="docs/external", depth=1)
        assert "secret" not in render_report(nodes, (), ())

    def test_a_symlinked_folder_resolving_inside_the_root_is_walked(self, tmp_path: Path) -> None:
        _write(tmp_path / "references" / "a.md", "")
        (tmp_path / "docs").mkdir()
        try:
            (tmp_path / "docs" / "specs").symlink_to(
                tmp_path / "references", target_is_directory=True
            )
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert walk(tmp_path, tmp_path / "docs")[1] == Directory(
            path="docs/specs", depth=1, documents=1
        )

    def test_a_folder_mirroring_a_sibling_is_still_listed(self, tmp_path: Path) -> None:
        # Testing the visited set before emitting dropped the node entirely, hiding a
        # folder the caller can see on disk — the lie ForeignDirectory exists to prevent.
        _write(tmp_path / "docs" / "glossary" / "edge.md", "")
        try:
            (tmp_path / "docs" / "mirror").symlink_to(
                tmp_path / "docs" / "glossary", target_is_directory=True
            )
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert walk(tmp_path, tmp_path / "docs") == (
            Directory(path="docs", depth=0, documents=0),
            Directory(path="docs/glossary", depth=1, documents=1),
            Directory(path="docs/mirror", depth=1, documents=1),
        )

    def test_a_mirrored_folder_is_named_but_not_walked_twice(self, tmp_path: Path) -> None:
        # The visited set governs the descent, so the children are not listed under a
        # second name. Asking for the mirror directly walks them.
        _write(tmp_path / "docs" / "glossary" / "deep" / "a.md", "")
        try:
            (tmp_path / "docs" / "mirror").symlink_to(
                tmp_path / "docs" / "glossary", target_is_directory=True
            )
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert [node.path for node in walk(tmp_path, tmp_path / "docs")] == [
            "docs",
            "docs/glossary",
            "docs/glossary/deep",
            "docs/mirror",
        ]
        assert [node.path for node in walk(tmp_path, tmp_path / "docs" / "mirror")] == [
            "docs/mirror",
            "docs/mirror/deep",
        ]

    def test_a_link_back_to_an_ancestor_is_named_and_does_not_loop(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "a.md", "")
        (tmp_path / "docs" / "sub").mkdir(parents=True)
        try:
            (tmp_path / "docs" / "sub" / "loop").symlink_to(
                tmp_path / "docs", target_is_directory=True
            )
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert walk(tmp_path, tmp_path / "docs") == (
            Directory(path="docs", depth=0, documents=1),
            Directory(path="docs/sub", depth=1, documents=0),
            Directory(path="docs/sub/loop", depth=2, documents=1),
        )


class TestUnlistableDirectory:
    """One directory the process cannot read used to fail the whole call, and the raw
    OSError carried an absolute host path."""

    def _corpus(self, tmp_path: Path) -> Path:
        _write(tmp_path / "docs" / "a.md", "---\ntitle: A\n---\n")
        _write(tmp_path / "docs" / "open" / "b.md", "---\ntitle: B\n---\n")
        _write(tmp_path / "docs" / "closed" / "c.md", "---\ntitle: C\n---\n")
        _write(tmp_path / "docs" / "closed" / "deep" / "d.md", "---\ntitle: D\n---\n")
        return tmp_path / "docs"

    @pytest.mark.parametrize("failing", ["markdown_in", "subdirectories"])
    def test_it_is_named_and_the_rest_of_the_subtree_survives(
        self, tmp_path: Path, deny: Callable[[str, Path], None], failing: str
    ) -> None:
        docs = self._corpus(tmp_path)
        deny(failing, docs / "closed")

        assert walk(tmp_path, docs) == (
            Directory(path="docs", depth=0, documents=1),
            UnlistableDirectory(path="docs/closed", depth=1),
            Directory(path="docs/open", depth=1, documents=1),
        )

    @pytest.mark.parametrize("failing", ["markdown_in", "subdirectories"])
    def test_it_is_not_descended_into(
        self, tmp_path: Path, deny: Callable[[str, Path], None], failing: str
    ) -> None:
        # Its children are unreachable through it, so `deep` is not on the tree either.
        docs = self._corpus(tmp_path)
        deny(failing, docs / "closed")
        assert "docs/closed/deep" not in [node.path for node in walk(tmp_path, docs)]

    def test_it_renders_as_one_line_beside_the_others(
        self, tmp_path: Path, deny: Callable[[str, Path], None]
    ) -> None:
        docs = self._corpus(tmp_path)
        deny("markdown_in", docs / "closed")
        rendered = render_report(walk(tmp_path, docs), (), ())
        assert "  closed/ cannot be listed" in rendered

    def test_it_costs_the_recursive_read_only_its_own_documents(
        self, tmp_path: Path, deny: Callable[[str, Path], None]
    ) -> None:
        # The key count recurses from the corpus root, so raising here took the whole corpus.
        docs = self._corpus(tmp_path)
        deny("subdirectories", docs / "closed")
        collected = collect(tmp_path, docs, recurse=True)
        assert [document.path for document in collected] == ["docs/a.md", "docs/open/b.md"]

    def test_asking_for_it_directly_reports_rather_than_fails(
        self, tmp_path: Path, deny: Callable[[str, Path], None]
    ) -> None:
        docs = self._corpus(tmp_path)
        deny("markdown_in", docs / "closed")
        assert collect(tmp_path, docs / "closed") == ()
        assert other_files(tmp_path, docs / "closed") == ()
        assert walk(tmp_path, docs / "closed") == (
            UnlistableDirectory(path="docs/closed", depth=0),
        )

    def test_no_host_path_reaches_the_report(
        self, tmp_path: Path, deny: Callable[[str, Path], None]
    ) -> None:
        docs = self._corpus(tmp_path)
        deny("markdown_in", docs / "closed")
        rendered = render_report(walk(tmp_path, docs), other_files(tmp_path, docs), ())
        assert str(tmp_path) not in rendered


class TestRenderReport:
    TREE = (
        Directory(path="docs", depth=0, documents=0),
        Directory(path="docs/glossary", depth=1, documents=2),
        Directory(path="docs/glossary/deep", depth=2, documents=1),
    )

    def test_the_three_groups_come_in_order_under_their_headings(self) -> None:
        report = render_report(
            self.TREE,
            ("docs/graph.pdf",),
            (Entry(path="docs/a.md", frontmatter=("title: A",)),),
        )
        assert report == (
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
        report = render_report(self.TREE, (), ())
        assert "docs/ 0" in report
        assert "  glossary/ 2" in report

    def test_an_empty_group_says_none(self) -> None:
        # A folder holding no documents is a real answer, not an error.
        report = render_report((Directory(path="docs", depth=0, documents=0),), (), ())
        assert report.endswith("# other files\nnone\n\n# documents\nnone")

    def test_a_foreign_folder_is_named_as_unlistable(self) -> None:
        report = render_report((ForeignDirectory(path="docs/external", depth=1),), (), ())
        assert "  external/ links outside the corpus" in report

    def test_a_pdf_is_distinguishable_from_a_frontmatterless_document(self) -> None:
        # Both render as a bare path, so only the heading tells them apart.
        report = render_report(
            (Directory(path="docs", depth=0, documents=1),),
            ("docs/graph.pdf",),
            (Entry(path="docs/bare.md", frontmatter=None),),
        )
        assert "# other files\ndocs/graph.pdf" in report
        assert "# documents\ndocs/bare.md" in report


class TestCollect:
    def test_lists_the_folder_and_does_not_recurse(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "b.md", "---\ntitle: B\n---\n")
        _write(tmp_path / "docs" / "a.md", "---\ntitle: A\n---\n")
        _write(tmp_path / "docs" / "sub" / "c.md", "# C\n")
        entries = collect(tmp_path, tmp_path / "docs")
        assert [entry.path for entry in entries] == ["docs/a.md", "docs/b.md"]

    def test_recurse_reaches_the_whole_subtree(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "a.md", "---\ntitle: A\n---\n")
        _write(tmp_path / "docs" / "sub" / "c.md", "# C\n")
        entries = collect(tmp_path, tmp_path / "docs", recurse=True)
        assert [entry.path for entry in entries] == ["docs/a.md", "docs/sub/c.md"]

    def test_recurse_skips_hidden_folders(self, tmp_path: Path) -> None:
        # A .venv is full of markdown — every package's README. Reading it would tally
        # frontmatter out of site-packages while the subtree says the folder is not there.
        _write(tmp_path / ".venv" / "Lib" / "pkg" / "README.md", "---\ntitle: V\n---\n")
        _write(tmp_path / "docs" / "a.md", "---\ntitle: A\n---\n")
        entries = collect(tmp_path, tmp_path, recurse=True)
        assert [entry.path for entry in entries] == ["docs/a.md"]

    def test_recurse_follows_a_symlinked_folder_the_subtree_advertises(
        self, tmp_path: Path
    ) -> None:
        # rglob never follows a directory symlink, so the subtree said `mirror/ 3` while
        # the key count saw none of the three. Both now read the same walk.
        _write(tmp_path / "docs" / "a.md", "---\ntitle: A\n---\n")
        for name in ("x.md", "y.md", "z.md"):
            _write(tmp_path / "other" / "deep" / name, "---\nstatus: locked\n---\n")
        try:
            (tmp_path / "docs" / "mirror").symlink_to(
                tmp_path / "other" / "deep", target_is_directory=True
            )
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert walk(tmp_path, tmp_path / "docs") == (
            Directory(path="docs", depth=0, documents=1),
            Directory(path="docs/mirror", depth=1, documents=3),
        )
        assert [doc.path for doc in collect(tmp_path, tmp_path / "docs", recurse=True)] == [
            "docs/a.md",
            "docs/mirror/x.md",
            "docs/mirror/y.md",
            "docs/mirror/z.md",
        ]

    def test_recurse_reads_a_mirrored_folder_only_once(self, tmp_path: Path) -> None:
        # docs/mirror -> docs/glossary is named in the subtree but not descended, so its
        # documents are not collected a second time under a second address.
        _write(tmp_path / "docs" / "glossary" / "edge.md", "---\ntitle: E\n---\n")
        try:
            (tmp_path / "docs" / "mirror").symlink_to(
                tmp_path / "docs" / "glossary", target_is_directory=True
            )
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert [doc.path for doc in collect(tmp_path, tmp_path / "docs", recurse=True)] == [
            "docs/glossary/edge.md"
        ]

    def test_recurse_and_walk_agree_on_which_folders_exist(self, tmp_path: Path) -> None:
        # Same rule in both, so `vocabulary` never counts a folder `contents` won't show.
        _write(tmp_path / ".venv" / "pkg" / "README.md", "---\ntitle: V\n---\n")
        _write(tmp_path / "docs" / "a.md", "---\ntitle: A\n---\n")
        walked = {node.path for node in walk(tmp_path, tmp_path)}
        collected = {
            entry.path.rsplit("/", 1)[0] for entry in collect(tmp_path, tmp_path, recurse=True)
        }
        assert collected <= walked

    def test_recurse_into_a_hidden_folder_named_outright_still_reads_it(
        self, tmp_path: Path
    ) -> None:
        _write(tmp_path / ".github" / "sub" / "ci.md", "---\ntitle: CI\n---\n")
        entries = collect(tmp_path, tmp_path / ".github", recurse=True)
        assert [entry.path for entry in entries] == [".github/sub/ci.md"]

    def test_ignores_non_markdown(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "a.md", "---\ntitle: A\n---\n")
        _write(tmp_path / "docs" / "notes.txt", "---\ntitle: not markdown\n---\n")
        assert [entry.path for entry in collect(tmp_path, tmp_path / "docs")] == ["docs/a.md"]

    def test_is_deterministic(self, tmp_path: Path) -> None:
        for name in ("z.md", "m.md", "a.md"):
            _write(tmp_path / "docs" / name, f"---\ntitle: {name}\n---\n")
        first = render(collect(tmp_path, tmp_path / "docs"))
        assert first == render(collect(tmp_path, tmp_path / "docs"))

    def test_a_single_file_target_lists_that_file(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "a.md", "---\ntitle: A\n---\n")
        entries = collect(tmp_path, tmp_path / "docs" / "a.md")
        assert [entry.path for entry in entries] == ["docs/a.md"]

    def test_empty_folder_collects_nothing(self, tmp_path: Path) -> None:
        (tmp_path / "docs").mkdir()
        assert collect(tmp_path, tmp_path / "docs") == ()

    def test_a_directory_named_like_a_document_does_not_break_the_call(
        self, tmp_path: Path
    ) -> None:
        # It used to reach read_entry, where the read failed and took the listing with it.
        (tmp_path / "docs" / "sub.md").mkdir(parents=True)
        _write(tmp_path / "docs" / "real.md", "---\ntitle: R\n---\n")
        assert [entry.path for entry in collect(tmp_path, tmp_path / "docs")] == ["docs/real.md"]

    def test_recurse_also_skips_a_directory_named_like_a_document(self, tmp_path: Path) -> None:
        (tmp_path / "docs" / "sub.md").mkdir(parents=True)
        _write(tmp_path / "docs" / "sub.md" / "inner.md", "---\ntitle: I\n---\n")
        entries = collect(tmp_path, tmp_path / "docs", recurse=True)
        assert [entry.path for entry in entries] == ["docs/sub.md/inner.md"]


class TestCollectContainment:
    def _leaky_corpus(self, tmp_path: Path) -> Path:
        outside = tmp_path.parent / f"{tmp_path.name}-outside"
        outside.mkdir(exist_ok=True)
        _write(outside / "secret.md", "---\ntitle: Secret\n---\n")
        _write(tmp_path / "docs" / "ok.md", "---\ntitle: OK\n---\n")
        try:
            (tmp_path / "docs" / "leak.md").symlink_to(outside / "secret.md")
        except OSError as exc:  # Windows needs developer mode or elevation
            pytest.skip(f"cannot create a symlink here: {exc}")
        return tmp_path / "docs"

    def test_a_symlinked_file_pointing_out_of_the_root_is_not_read(self, tmp_path: Path) -> None:
        # The walk reads symlinked files like any other, so the guard has to sit here too:
        # otherwise foreign frontmatter comes back attached to an in-corpus path.
        docs = self._leaky_corpus(tmp_path)
        assert collect(tmp_path, docs) == (
            Unreadable(path="docs/leak.md", reason="links to a target outside the corpus"),
            Entry(path="docs/ok.md", frontmatter=("title: OK",)),
        )

    def test_one_bad_link_does_not_cost_the_listing(self, tmp_path: Path) -> None:
        # It used to raise, so a single planted link made the folder unlistable, and
        # through the recursive key count it took the whole subtree with it.
        docs = self._leaky_corpus(tmp_path)
        assert render(collect(tmp_path, docs)) == (
            "docs/leak.md\nlinks to a target outside the corpus\n\ndocs/ok.md\ntitle: OK"
        )

    def test_the_reason_names_no_host_path(self, tmp_path: Path) -> None:
        # Where the link points is a filesystem path the corpus does not otherwise expose,
        # and it adds nothing the caller can act on.
        docs = self._leaky_corpus(tmp_path)
        rendered = render(collect(tmp_path, docs))
        assert "docs/leak.md" in rendered
        assert "secret.md" not in rendered
        assert str(tmp_path.parent) not in rendered

    def test_a_link_dangling_inside_the_root_reports_the_read_failure(self, tmp_path: Path) -> None:
        # Passes the containment check, then fails at the read. The raw OSError would carry
        # an absolute host path and name the document by where its bytes were meant to live.
        _write(tmp_path / "docs" / "ok.md", "---\ntitle: OK\n---\n")
        try:
            (tmp_path / "docs" / "inner.md").symlink_to(tmp_path / "docs" / "never-created.md")
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        rendered = render(collect(tmp_path, tmp_path / "docs"))
        assert "docs/inner.md\ncannot be read (" in rendered
        assert "docs/ok.md\ntitle: OK" in rendered
        assert str(tmp_path) not in rendered

    def test_a_document_that_is_not_utf_8_is_reported_not_raised(self, tmp_path: Path) -> None:
        # UnicodeDecodeError is a ValueError, not an OSError, so it used to escape collect
        # and fail the whole call — one latin-1 file made its folder unlistable.
        _write(tmp_path / "docs" / "ok.md", "---\ntitle: OK\n---\n")
        (tmp_path / "docs" / "latin.md").write_bytes(b"---\ntitle: caf\xe9\n---\n")

        assert collect(tmp_path, tmp_path / "docs") == (
            Unreadable(path="docs/latin.md", reason="cannot be read (not UTF-8 text)"),
            Entry(path="docs/ok.md", frontmatter=("title: OK",)),
        )

    def test_a_binary_file_named_directly_is_reported_not_raised(self, tmp_path: Path) -> None:
        # `under` naming a file skips the `*.md` filter, so binary reaches the same read.
        image = tmp_path / "docs" / "diagram.png"
        image.parent.mkdir(parents=True)
        image.write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")

        assert collect(tmp_path, image) == (
            Unreadable(path="docs/diagram.png", reason="cannot be read (not UTF-8 text)"),
        )

    def test_an_unreadable_document_carries_no_properties(self, tmp_path: Path) -> None:
        # So the reason standing in for its frontmatter never enters the key vocabulary.
        docs = self._leaky_corpus(tmp_path)
        leak = next(doc for doc in collect(tmp_path, docs) if doc.path == "docs/leak.md")
        assert leak.properties() == ()
        assert leak.projected(frozenset({"title"})) == leak

    def test_a_symlink_resolving_inside_the_root_is_read(self, tmp_path: Path) -> None:
        target = _write(tmp_path / "references" / "frontmatter.md", "---\ntitle: F\n---\n")
        link = tmp_path / "docs" / "specs" / "frontmatter.md"
        link.parent.mkdir(parents=True)
        try:
            link.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        entries = collect(tmp_path, tmp_path / "docs" / "specs")
        assert [entry.path for entry in entries] == ["docs/specs/frontmatter.md"]


class TestResolveUnder:
    def test_resolves_relative_to_the_root(self, tmp_path: Path) -> None:
        (tmp_path / "docs" / "glossary").mkdir(parents=True)
        assert (
            resolve_under(tmp_path, "docs/glossary") == (tmp_path / "docs" / "glossary").resolve()
        )

    def test_the_root_itself_is_allowed(self, tmp_path: Path) -> None:
        assert resolve_under(tmp_path, "") == tmp_path.resolve()

    @pytest.mark.parametrize("under", ["..", "docs/../..", "../elsewhere"])
    def test_escaping_the_root_is_rejected(self, tmp_path: Path, under: str) -> None:
        (tmp_path / "docs").mkdir()
        with pytest.raises(ValueError, match="outside the corpus root"):
            resolve_under(tmp_path, under)

    def test_a_missing_folder_is_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="does not exist"):
            resolve_under(tmp_path, "docs/nope")

    def test_a_symlinked_folder_pointing_out_of_the_root_is_rejected(self, tmp_path: Path) -> None:
        # Lexically inside the corpus, physically outside it. Reads follow symlinks, so
        # without the resolved check this listing would report foreign files under docs/.
        outside = tmp_path.parent / f"{tmp_path.name}-outside"
        outside.mkdir(exist_ok=True)
        _write(outside / "secret.md", "---\ntitle: Secret\n---\n")
        corpus = tmp_path / "docs"
        corpus.mkdir()
        try:
            (corpus / "external").symlink_to(outside, target_is_directory=True)
        except OSError as exc:  # Windows needs developer mode or elevation
            pytest.skip(f"cannot create a symlink here: {exc}")

        with pytest.raises(ValueError, match="resolves outside the corpus root"):
            resolve_under(tmp_path, "docs/external")

    def test_a_symlink_resolving_inside_the_root_is_allowed(self, tmp_path: Path) -> None:
        # The docs/specs case: a symlink into plugins/, still inside the corpus root.
        target = _write(tmp_path / "references" / "frontmatter.md", "---\ntitle: F\n---\n")
        link = tmp_path / "docs" / "specs" / "frontmatter.md"
        link.parent.mkdir(parents=True)
        try:
            link.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert resolve_under(tmp_path, "docs/specs/frontmatter.md") == link

    def test_collapses_dot_segments_without_following_symlinks(self, tmp_path: Path) -> None:
        (tmp_path / "docs" / "specs").mkdir(parents=True)
        assert resolve_under(tmp_path, "docs/./notes/../specs") == tmp_path / "docs" / "specs"

    def test_naming_a_symlink_keeps_the_link_path(self, tmp_path: Path) -> None:
        # Passing the symlink itself as `under`, not reaching it through a folder walk.
        target = _write(tmp_path / "references" / "frontmatter.md", "---\ntitle: F\n---\n")
        link = tmp_path / "docs" / "specs" / "frontmatter.md"
        link.parent.mkdir(parents=True)
        try:
            link.symlink_to(target)
        except OSError as exc:  # Windows needs developer mode or elevation
            pytest.skip(f"cannot create a symlink here: {exc}")

        under = resolve_under(tmp_path, "docs/specs/frontmatter.md")
        assert collect(tmp_path, under)[0].path == "docs/specs/frontmatter.md"
