"""Tests for the pathlib adapter.

What these prove is narrow and worth naming. ``contents`` is built on beliefs about the
substrate — that a dangling link is neither a file nor a directory, that ``resolve``
follows a link, that a byte-order mark would hide the opening fence, that a non-text file
raises ``UnicodeDecodeError`` rather than ``OSError``. The fake encodes those beliefs, so
every test written against it inherits them. These are the tests that check them, and they
are the only ones in the suite that run against a real filesystem for that purpose.

A test here that skips is a belief left unverified on this machine, not a test that passed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fakes import REAL


class TestEntries:
    def test_lists_everything_directly_in_the_directory(self, tmp_path: Path) -> None:
        (tmp_path / "sub").mkdir()
        (tmp_path / "a.md").write_text("", encoding="utf-8")
        (tmp_path / "sub" / "deep.md").write_text("", encoding="utf-8")
        assert set(REAL.entries(tmp_path)) == {tmp_path / "sub", tmp_path / "a.md"}

    def test_an_unreadable_directory_raises_at_the_call(self, tmp_path: Path) -> None:
        # Two things at once. `UnlistableDirectory` depends on the failure arriving as an
        # exception rather than an empty tuple, and on it arriving here rather than
        # mid-iteration, which is where bare `iterdir` raises — that would move the failure
        # into whichever comprehension in `contents` happened to consume it.
        with pytest.raises(OSError):
            REAL.entries(tmp_path / "never-created")


class TestKindAndExistence:
    def test_a_directory_a_file_and_neither(self, tmp_path: Path) -> None:
        (tmp_path / "sub").mkdir()
        (tmp_path / "a.md").write_text("", encoding="utf-8")
        assert REAL.is_directory(tmp_path / "sub")
        assert REAL.is_file(tmp_path / "a.md")
        assert not REAL.is_directory(tmp_path / "a.md")
        assert not REAL.is_file(tmp_path / "sub")

    def test_a_dangling_link_is_neither_a_file_nor_a_directory(self, tmp_path: Path) -> None:
        # Why `markdown_in` tests `not is_directory()` instead of `is_file()`: the latter
        # would drop a dangling link silently, and a document on disk must not go missing.
        link = tmp_path / "gone.md"
        try:
            link.symlink_to(tmp_path / "never-created.md")
        except OSError as exc:  # Windows needs developer mode or elevation
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert not REAL.is_file(link)
        assert not REAL.is_directory(link)
        assert link in REAL.entries(tmp_path)

    def test_exists_is_false_for_what_was_never_created(self, tmp_path: Path) -> None:
        assert not REAL.exists(tmp_path / "never-created")

    def test_is_symlink_answers_about_the_link_not_its_target(self, tmp_path: Path) -> None:
        # The one method on the port that does not follow. A linked directory and the
        # directory it points at answer the same to `is_directory`, `resolve`, and
        # `entries`; this is what tells them apart.
        target = tmp_path / "target"
        target.mkdir()
        (target / "deep.md").write_text("", encoding="utf-8")
        link = tmp_path / "link"
        try:
            link.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert REAL.is_symlink(link)
        assert not REAL.is_symlink(target)
        assert REAL.is_directory(link) == REAL.is_directory(target)
        # Reached through a link is not the same as being one.
        assert not REAL.is_symlink(link / "deep.md")

    def test_a_dangling_link_is_still_a_link(self, tmp_path: Path) -> None:
        link = tmp_path / "gone.md"
        try:
            link.symlink_to(tmp_path / "never-created.md")
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert REAL.is_symlink(link)
        assert not REAL.exists(link)


class TestResolve:
    def test_it_collapses_a_relative_step(self, tmp_path: Path) -> None:
        (tmp_path / "sub").mkdir()
        assert REAL.resolve(tmp_path / "sub" / ".." / "sub") == (tmp_path / "sub").resolve()

    def test_it_follows_a_link_to_its_target(self, tmp_path: Path) -> None:
        # The containment check is built on this: a directory inside the corpus whose
        # target is outside it is only detectable by resolving.
        target = tmp_path / "target"
        target.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert REAL.resolve(link) == target.resolve()

    def test_it_follows_a_link_an_ancestor_stands_for(self, tmp_path: Path) -> None:
        target = tmp_path / "target"
        target.mkdir()
        (target / "deep.md").write_text("", encoding="utf-8")
        link = tmp_path / "link"
        try:
            link.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"cannot create a symlink here: {exc}")

        assert REAL.resolve(link / "deep.md") == (target / "deep.md").resolve()


class TestReadText:
    def test_it_returns_the_text(self, tmp_path: Path) -> None:
        path = tmp_path / "a.md"
        path.write_text("---\ntitle: A\n---\n", encoding="utf-8")
        assert REAL.read_text(path) == "---\ntitle: A\n---\n"

    def test_a_byte_order_mark_is_stripped(self, tmp_path: Path) -> None:
        # Left in, it sits in front of the opening fence and hides the whole block.
        path = tmp_path / "a.md"
        path.write_bytes("---\ntitle: A\n---\n".encode("utf-8-sig"))
        assert REAL.read_text(path).splitlines()[0] == "---"

    def test_crlf_is_translated(self, tmp_path: Path) -> None:
        # So a file Obsidian wrote on Windows slices the same as one written on Linux.
        path = tmp_path / "a.md"
        path.write_bytes(b"---\r\ntitle: A\r\n---\r\n")
        assert REAL.read_text(path).splitlines() == ["---", "title: A", "---"]

    def test_a_non_text_file_raises_unicode_decode_error(self, tmp_path: Path) -> None:
        # Not an OSError. `collect` catches both because of this: catching OSError alone
        # let one mis-encoded file fail the whole call.
        path = tmp_path / "diagram.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")
        with pytest.raises(UnicodeDecodeError):
            REAL.read_text(path)

    def test_a_missing_file_raises_os_error(self, tmp_path: Path) -> None:
        with pytest.raises(OSError):
            REAL.read_text(tmp_path / "never-created.md")
