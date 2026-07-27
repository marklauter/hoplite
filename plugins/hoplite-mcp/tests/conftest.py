"""Fixtures shared across the suite."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "edge.md").write_text("---\ntitle: Edge\n---\n\n# Edge\n", encoding="utf-8")
    (docs / "loose.md").write_text("# Loose\n", encoding="utf-8")
    return tmp_path
