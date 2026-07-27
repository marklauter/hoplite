"""The in-memory ``Files`` fake, and the real adapter under test.

Three ways to give the walk a corpus. ``REAL`` puts it on the actual filesystem under
``tmp_path``, which is what pins ``RealFiles`` to real pathlib behavior. ``FakeFiles``
describes one in a dict, which is what makes the cases the filesystem will not reliably
produce — a symlink out of the corpus, a directory that cannot be read, a link back to an
ancestor — deterministic on every platform. Eight tests used to ``pytest.skip`` when the OS
refused a symlink, so on a plain Windows box the containment guarantees went unverified.

``CountingFiles`` wraps either of them and counts what was asked of it, which is how
the cost claims — one ``entries`` call per directory per call — are pinned rather than
asserted in a commit message.

The filesystem tests are not marked ``integration``. They run in half a second against a
``tmp_path`` the test owns, so splitting the suite would buy nothing.
"""

from __future__ import annotations

import errno
import os.path
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, final

from hoplite_catalog.adapters import RealFiles
from hoplite_catalog.corpus import Corpus
from hoplite_catalog.ports import Files

__all__ = ["CORPUS", "REAL", "CountingFiles", "FakeFiles", "document", "fake", "real"]

REAL: Final = RealFiles()

# An absolute path that never exists. `Path("/corpus")` is not absolute on Windows, where
# a path needs a drive, and `Corpus.path_of` calls `absolute()` on what it emits.
CORPUS: Final = Path(os.path.abspath("/corpus"))


def real(root: Path) -> Corpus:
    """The real filesystem rooted at ``root``, which is a ``tmp_path`` the test owns."""
    return Corpus.rooted_at(REAL, root)


def fake(files: FakeFiles) -> Corpus:
    """An in-memory corpus rooted at ``CORPUS``, the root every ``FakeFiles`` tree uses."""
    return Corpus.rooted_at(files, CORPUS)


def document(title: str) -> str:
    """A document carrying one property, for tests about the walk rather than the slice."""
    return f"---\ntitle: {title}\n---\n"


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FakeFiles:
    """An in-memory corpus, described rather than created.

    ``texts`` maps a file to its content and ``directories`` names the folders. ``links``
    maps a path to what it resolves to, which is how a symlink is expressed — including one
    whose target sits outside ``CORPUS``. ``denied`` names directories that raise the way an
    unreadable one does, ``undecodable`` names files that are not text, and ``unresolvable``
    names paths whose target cannot be reached at all — a symlink loop, a share that went
    away — which is the one failure the filesystem raises from ``resolve`` itself.

    Every mapping is keyed by absolute path, so a test reads as the tree it describes.
    """

    texts: Mapping[Path, str] = field(default_factory=dict)
    directories: frozenset[Path] = frozenset()
    links: Mapping[Path, Path] = field(default_factory=dict)
    denied: frozenset[Path] = frozenset()
    undecodable: frozenset[Path] = frozenset()
    unresolvable: frozenset[Path] = frozenset()

    def _known(self) -> frozenset[Path]:
        return frozenset(self.texts) | self.directories | frozenset(self.links)

    def entries(self, directory: Path) -> tuple[Path, ...]:
        """Children named under the path asked for, as ``iterdir`` names them.

        A linked directory lists its target's children, but under the link's own path:
        ``docs/mirror`` holding ``docs/glossary/edge.md`` yields ``docs/mirror/edge.md``.
        That is what makes one document reachable by two paths, which the walk's visited
        set exists to handle.
        """
        target = self.resolve(directory)
        if target in self.denied:
            raise PermissionError(13, "Permission denied", str(directory))
        return tuple(
            sorted(directory / path.name for path in self._known() if path.parent == target)
        )

    def is_directory(self, path: Path) -> bool:
        try:
            return self.resolve(path) in self.directories
        except OSError:
            return False

    def is_file(self, path: Path) -> bool:
        """A path that cannot be resolved is neither file nor directory, the way pathlib's
        predicates swallow the ``OSError`` and answer ``False``. It still appears in
        ``entries``, so the listing sees it and has to say something about it."""
        try:
            target = self.resolve(path)
        except OSError:
            return False
        return target in self.texts or target in self.undecodable

    def is_symlink(self, path: Path) -> bool:
        """The link itself, not its target — so an entry reached *through* a link is not
        one. ``docs/mirror`` is a link; ``docs/mirror/edge.md`` is a file underneath one."""
        return path in self.links

    def exists(self, path: Path) -> bool:
        return self.is_file(path) or self.is_directory(path)

    def resolve(self, path: Path) -> Path:
        """Follow a link, including one an ancestor stands for, the way the OS does."""
        if path in self.unresolvable:
            raise OSError(errno.ELOOP, "Too many levels of symbolic links", str(path))
        if path in self.links:
            return self.links[path]
        for parent in path.parents:
            if parent in self.links:
                return self.links[parent] / path.relative_to(parent)
        return path

    def read_text(self, path: Path) -> str:
        target = self.resolve(path)
        if target in self.undecodable:
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
        if target not in self.texts:
            raise FileNotFoundError(2, "No such file or directory", str(path))
        return self.texts[target]


@final
@dataclass(frozen=True, slots=True)
class CountingFiles:
    """A ``Files`` that answers from another one and counts what it was asked.

    How often the corpus is read is part of the contract — the whole design of the listing
    is that a caller pays for the directory it asked for — and it is the part that drifts
    silently, since a second read of the same directory returns the same answer. Counting
    at the port is the only place the number is visible.
    """

    inner: Files
    calls: Counter[str] = field(default_factory=Counter)

    def entries(self, directory: Path) -> tuple[Path, ...]:
        self.calls["entries"] += 1
        return self.inner.entries(directory)

    def is_directory(self, path: Path) -> bool:
        self.calls["is_directory"] += 1
        return self.inner.is_directory(path)

    def is_file(self, path: Path) -> bool:
        self.calls["is_file"] += 1
        return self.inner.is_file(path)

    def is_symlink(self, path: Path) -> bool:
        self.calls["is_symlink"] += 1
        return self.inner.is_symlink(path)

    def exists(self, path: Path) -> bool:
        self.calls["exists"] += 1
        return self.inner.exists(path)

    def resolve(self, path: Path) -> Path:
        self.calls["resolve"] += 1
        return self.inner.resolve(path)

    def read_text(self, path: Path) -> str:
        self.calls["read_text"] += 1
        return self.inner.read_text(path)
