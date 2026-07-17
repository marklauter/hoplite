"""Tests for run-hook.sh — the launcher that probes the configured interpreter.

The launcher reads ``CLAUDE_PLUGIN_OPTION_PYTHON_PATH`` (falling back to ``python3``),
probes it with a no-op, and either explains the python_path option on stderr (exit 2)
or execs check-frontmatter.py with stdin passed through.

Run: ``python -m pytest plugins/hoplite-skills/hooks/test_run_hook.py``
Needs ``sh`` on PATH (Git Bash on Windows); skipped otherwise.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
RUN_HOOK = HOOKS_DIR / "run-hook.sh"
PYTHON = sys.executable.replace("\\", "/")


def _find_sh() -> str | None:
    """``sh`` from PATH, or from the Git for Windows install next to ``git``."""
    found = shutil.which("sh")
    if found is not None:
        return found
    git = shutil.which("git")
    if git is not None:
        for candidate in ("bin/sh.exe", "usr/bin/sh.exe"):
            sh = Path(git).parents[1] / candidate
            if sh.is_file():
                return str(sh)
    return None


SH = _find_sh()

pytestmark = pytest.mark.skipif(SH is None, reason="needs sh (Git Bash on Windows)")


def run_hook(stdin: str = "{}", python_path: str | None = None, path_prefix: Path | None = None):
    assert SH is not None  # skipif guarantees this
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_OPTION_PYTHON_PATH"}
    env["CLAUDE_PLUGIN_ROOT"] = str(HOOKS_DIR.parent)
    if python_path is not None:
        env["CLAUDE_PLUGIN_OPTION_PYTHON_PATH"] = python_path
    if path_prefix is not None:
        env["PATH"] = f"{path_prefix}{os.pathsep}{env['PATH']}"
    return subprocess.run(
        [SH, str(RUN_HOOK)],
        input=stdin,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def write_shim(directory: Path, name: str, body: str) -> Path:
    shim = directory / name
    shim.write_text(f"#!/bin/sh\n{body}\n", newline="\n")
    shim.chmod(0o755)
    return shim


# --- interpreter selection ----------------------------------------------------


def test_working_interpreter_runs_hook() -> None:
    result = run_hook(python_path=PYTHON)
    assert result.returncode == 0, result.stderr


def test_missing_interpreter_explains_option() -> None:
    result = run_hook(python_path="python-that-does-not-exist")
    assert result.returncode == 2
    assert "python_path" in result.stderr
    assert "python-that-does-not-exist" in result.stderr


def test_broken_interpreter_explains_option(tmp_path: Path) -> None:
    # Exists and runs, but fails the no-op probe — the Store-stub shape.
    stub = write_shim(tmp_path, "python-stub", "exit 9")
    result = run_hook(python_path=str(stub).replace("\\", "/"))
    assert result.returncode == 2
    assert "python_path" in result.stderr


def test_unset_option_falls_back_to_python3(tmp_path: Path) -> None:
    write_shim(tmp_path, "python3", f'exec "{PYTHON}" "$@"')
    result = run_hook(path_prefix=tmp_path)
    assert result.returncode == 0, result.stderr


# --- pass-through -------------------------------------------------------------


def test_stdin_and_advisory_pass_through(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "note.md"
    doc.parent.mkdir()
    doc.write_text('---\ncites: "[[a:b:c]]"\n---\n', encoding="utf-8")
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(doc)}})
    result = run_hook(stdin=payload, python_path=PYTHON)
    assert result.returncode == 2
    assert "[frontmatter-check]" in result.stderr
