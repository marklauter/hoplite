"""The filesystem port and its pathlib adapter.

``contents`` used to call ``iterdir``, ``glob``, ``resolve``, and ``read_text`` inline, so
the walk had no seam: a test that needed an unreadable directory or a symlink out of the
corpus had to reach into ``pathlib`` or ask the real filesystem for one. The first is
mocking what this package does not own; the second is not portable, since an unwritable
mode is ignored by root and a symlink needs elevation on Windows, which left eight tests
skipping and the containment guarantees unverified on a plain Windows box.

``Files`` is the whole of what the walk needs from a filesystem. ``RealFiles`` is the only
adapter shipped; the composition root in ``server`` constructs it, and a test hands the
walk an in-memory corpus instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, final

__all__ = ["Files", "RealFiles"]


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

    def exists(self, path: Path) -> bool: ...

    def resolve(self, path: Path) -> Path:
        """Where ``path`` actually points, links followed and ``..`` collapsed."""
        ...

    def read_text(self, path: Path) -> str:
        """The file's text. Raises ``UnicodeDecodeError`` when it is not text."""
        ...


@final
@dataclass(frozen=True, slots=True)
class RealFiles:
    """``Files`` over ``pathlib``. The I/O edge of the package.

    Stateless, so one instance serves every call. It is a class rather than a module of
    functions because the port is a type, and a fake has to be substitutable for it.
    """

    def entries(self, directory: Path) -> tuple[Path, ...]:
        return tuple(directory.iterdir())

    def is_directory(self, path: Path) -> bool:
        return path.is_dir()

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def exists(self, path: Path) -> bool:
        return path.exists()

    def resolve(self, path: Path) -> Path:
        return path.resolve()

    def read_text(self, path: Path) -> str:
        """``utf-8-sig`` strips a byte-order mark, which would otherwise sit in front of
        the opening fence and hide it. Text mode translates CRLF, so a file Obsidian wrote
        on Windows slices the same as one written on Linux. Both are decisions about how
        bytes become text, which is this adapter's business and not the walk's."""
        return path.read_text(encoding="utf-8-sig")
