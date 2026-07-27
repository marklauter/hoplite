"""The in-memory ``Files`` fake, and the real adapter under test.

Two ways to give the walk a corpus. ``REAL`` puts it on the actual filesystem under
``tmp_path``, which is what pins ``RealFiles`` to real pathlib behavior. ``FakeFiles``
describes one in a dict, which is what makes the cases the filesystem will not reliably
produce — a symlink out of the corpus, a directory that cannot be read, a link back to an
ancestor — deterministic on every platform. Eight tests used to ``pytest.skip`` when the OS
refused a symlink, so on a plain Windows box the containment guarantees went unverified.

The filesystem tests are not marked ``integration``. They run in half a second against a
``tmp_path`` the test owns, so splitting the suite would buy nothing.
"""

from __future__ import annotations

import os.path
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, final

from hoplite_catalog.files import RealFiles

__all__ = ["CORPUS", "REAL", "FakeFiles", "document"]

REAL: Final = RealFiles()

# An absolute path that never exists. `Path("/corpus")` is not absolute on Windows, where
# a path needs a drive, and `corpus_path` calls `absolute()` on what it emits.
CORPUS: Final = Path(os.path.abspath("/corpus"))


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
    unreadable one does, and ``undecodable`` names files that are not text.

    Every mapping is keyed by absolute path, so a test reads as the tree it describes.
    """

    texts: Mapping[Path, str] = field(default_factory=dict)
    directories: frozenset[Path] = frozenset()
    links: Mapping[Path, Path] = field(default_factory=dict)
    denied: frozenset[Path] = frozenset()
    undecodable: frozenset[Path] = frozenset()

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
        return self.resolve(path) in self.directories

    def is_file(self, path: Path) -> bool:
        target = self.resolve(path)
        return target in self.texts or target in self.undecodable

    def exists(self, path: Path) -> bool:
        return self.is_file(path) or self.is_directory(path)

    def resolve(self, path: Path) -> Path:
        """Follow a link, including one an ancestor stands for, the way the OS does."""
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
