"""The pathlib adapter for the ``Files`` port. The I/O edge of the package.

The only module that touches a filesystem, and the only one ``server`` needs in order to
construct one. Kept apart from ``ports`` so the contract can say the core imports the
port and never the adapter; in one module, nothing stops ``contents`` from reaching past
its own boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import final

__all__ = ["RealFiles"]


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

    def is_symlink(self, path: Path) -> bool:
        return path.is_symlink()

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
