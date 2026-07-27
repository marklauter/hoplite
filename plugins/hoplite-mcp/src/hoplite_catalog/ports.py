"""The filesystem port.

``contents`` used to call ``iterdir``, ``glob``, ``resolve``, and ``read_text`` inline, so
the walk had no seam: a test that needed an unreadable directory or a symlink out of the
corpus had to reach into ``pathlib`` or ask the real filesystem for one. The first is
mocking what this package does not own; the second is not portable, since an unwritable
mode is ignored by root and a symlink needs elevation on Windows, which left eight tests
skipping and the containment guarantees unverified on a plain Windows box.

``Files`` is the whole of what the walk needs from a filesystem, and it is all the core
imports. The adapter that satisfies it lives in ``adapters``, which only ``server`` may
import — an `import-linter` contract says so, because a port the core can bypass is not
a boundary. A test hands the walk an in-memory corpus instead.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

__all__ = ["Files"]


class Files(Protocol):
    """Read-only access to a directory tree. Every method may raise ``OSError``.

    Links are followed the way the filesystem follows them: ``is_directory``, ``is_file``,
    and ``read_text`` answer about the target, and ``resolve`` is what names it. Nothing
    here writes, and nothing here reports where a link points except ``resolve``, which the
    walk uses to check containment and never emits.
    """

    def entries(self, directory: Path) -> tuple[Path, ...]:
        """Everything directly in ``directory``, in no particular order.

        Materialized rather than lazy. ``iterdir`` raises mid-iteration, so a lazy port
        would move the failure into whichever comprehension happened to consume it, and
        every caller would need the ``try`` around the consumer rather than the call.
        """
        ...

    def is_directory(self, path: Path) -> bool: ...

    def is_file(self, path: Path) -> bool: ...

    def is_symlink(self, path: Path) -> bool:
        """True when ``path`` itself is a link, whatever it points at.

        The one method here that does not follow. The walk needs it to tell a directory
        apart from a second name for one: both answer the same to everything else, and
        which of the two it descends must not be decided by sort order.
        """
        ...

    def exists(self, path: Path) -> bool: ...

    def resolve(self, path: Path) -> Path:
        """Where ``path`` actually points, links followed and ``..`` collapsed."""
        ...

    def read_text(self, path: Path) -> str:
        """The file's text. Raises ``UnicodeDecodeError`` when it is not text."""
        ...
