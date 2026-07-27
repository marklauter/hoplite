"""Fixtures shared across the suite."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from hoplite_catalog import contents


@pytest.fixture
def deny(monkeypatch: pytest.MonkeyPatch) -> Callable[[str, Path], None]:
    """Make one directory raise the way an unreadable one does.

    Patched at ``subdirectories`` and ``markdown_in``, which this package owns, rather than
    at ``iterdir`` and ``glob``, which it does not. A directory a test process cannot read
    is not something a test can create portably — an unwritable mode is ignored by root and
    by Windows — and the contract under test is what the walk does when the read fails, not
    which errno produced it.
    """

    def _deny(name: str, denied: Path) -> None:
        original: Callable[[Path], tuple[Path, ...]] = getattr(contents, name)

        def failing(directory: Path) -> tuple[Path, ...]:
            if directory == denied:
                raise PermissionError(13, "Permission denied", str(directory))
            return original(directory)

        monkeypatch.setattr(contents, name, failing)

    return _deny
