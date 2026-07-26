"""Tests for the frontmatter slicer."""

from __future__ import annotations

from pathlib import Path

import pytest

from hoplite_catalog.contents import (
    Entry,
    collect,
    is_excluded,
    project,
    read_entry,
    render,
    resolve_under,
    slice_frontmatter,
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
    def test_document_with_frontmatter_is_fenced(self) -> None:
        entry = Entry(path="docs/a.md", frontmatter=("title: A",))
        assert render([entry]) == "docs/a.md\n---\ntitle: A\n---"

    def test_document_without_frontmatter_is_its_path_alone(self) -> None:
        assert render([Entry(path="docs/a.md", frontmatter=None)]) == "docs/a.md"

    def test_empty_block_round_trips_as_an_empty_block(self) -> None:
        assert render([Entry(path="docs/a.md", frontmatter=())]) == "docs/a.md\n---\n---"

    def test_entries_are_separated_by_a_blank_line(self) -> None:
        entries = [
            Entry(path="docs/a.md", frontmatter=("title: A",)),
            Entry(path="docs/b.md", frontmatter=None),
        ]
        assert render(entries) == "docs/a.md\n---\ntitle: A\n---\n\ndocs/b.md"

    def test_no_entries_renders_empty(self) -> None:
        assert render([]) == ""


class TestProject:
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
        assert project(self.FULL, None) == self.FULL

    def test_keeps_only_the_named_properties(self) -> None:
        assert project(self.FULL, frozenset({"title", "tags"})).frontmatter == (
            "title: Edge",
            "tags: [glossary, hoplite]",
        )

    def test_a_block_list_keeps_its_continuation_lines(self) -> None:
        assert project(self.FULL, frozenset({"disjoint-with"})).frontmatter == (
            "disjoint-with:",
            '  - "[[node]]"',
            '  - "[[claim]]"',
        )

    def test_a_continuation_line_is_dropped_with_its_key(self) -> None:
        kept = project(self.FULL, frozenset({"title"})).frontmatter
        assert kept == ("title: Edge",)

    def test_an_empty_key_set_leaves_the_path_alone(self) -> None:
        projected = project(self.FULL, frozenset())
        assert projected.frontmatter is None
        assert render([projected]) == "docs/glossary/edge.md"

    def test_an_unmatched_key_leaves_the_path_alone(self) -> None:
        assert project(self.FULL, frozenset({"nonesuch"})).frontmatter is None

    def test_a_document_without_frontmatter_is_untouched(self) -> None:
        bare = Entry(path="docs/a.md", frontmatter=None)
        assert project(bare, frozenset({"title"})) == bare

    def test_the_path_is_never_changed(self) -> None:
        assert project(self.FULL, frozenset({"title"})).path == self.FULL.path


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


class TestCollect:
    def test_recurses_and_orders_by_path(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "b.md", "---\ntitle: B\n---\n")
        _write(tmp_path / "docs" / "a.md", "---\ntitle: A\n---\n")
        _write(tmp_path / "docs" / "sub" / "c.md", "# C\n")
        entries = collect(tmp_path, tmp_path / "docs")
        assert [entry.path for entry in entries] == ["docs/a.md", "docs/b.md", "docs/sub/c.md"]

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

    def test_excluded_folders_are_skipped(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "notes" / "a.md", "---\ntitle: A\n---\n")
        _write(tmp_path / "docs" / "journal" / "b.md", "---\ntitle: B\n---\n")
        _write(tmp_path / "docs" / "journal" / "deep" / "c.md", "---\ntitle: C\n---\n")
        entries = collect(tmp_path, tmp_path / "docs", frozenset({"docs/journal"}))
        assert [entry.path for entry in entries] == ["docs/notes/a.md"]

    def test_exclusion_matches_whole_segments(self, tmp_path: Path) -> None:
        # 'docs/journal' must not exclude a sibling whose name merely starts the same way.
        _write(tmp_path / "docs" / "journal" / "a.md", "---\ntitle: A\n---\n")
        _write(tmp_path / "docs" / "journals-are-not-notes.md", "---\ntitle: B\n---\n")
        entries = collect(tmp_path, tmp_path / "docs", frozenset({"docs/journal"}))
        assert [entry.path for entry in entries] == ["docs/journals-are-not-notes.md"]

    def test_excluding_everything_collects_nothing(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "a.md", "---\ntitle: A\n---\n")
        assert collect(tmp_path, tmp_path / "docs", frozenset({"docs"})) == ()


class TestIsExcluded:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("docs/journal/2026-07-26.md", True),
            ("docs/journal/deep/nested.md", True),
            ("docs/journal", True),
            ("docs/journals-are-not-notes.md", False),
            ("docs/notes/journal.md", False),
            ("docs/notes/a.md", False),
        ],
    )
    def test_matches_whole_segments_only(self, path: str, expected: bool) -> None:
        assert is_excluded(path, frozenset({"docs/journal"})) is expected

    def test_no_exclusions_excludes_nothing(self) -> None:
        assert is_excluded("docs/journal/a.md", frozenset()) is False


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
