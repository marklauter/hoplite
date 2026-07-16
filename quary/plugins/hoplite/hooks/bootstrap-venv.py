"""SessionStart hook: ensure the persistent venv at ${CLAUDE_PLUGIN_DATA}/venv exists and matches the bundled manifest.

Runs under the system Python before any pip-installed dep is available — stdlib only.
Idempotent: when the bundled ``pyproject.toml`` byte-matches the snapshot copy in
``${CLAUDE_PLUGIN_DATA}``, exits in milliseconds. On manifest drift or missing venv,
recreates the venv and re-installs the project editable.

Failure handling: if venv creation or pip install fails, the snapshot manifest is
deleted so the next session retries from scratch. The hook returns 0 unconditionally
so SessionStart doesn't block the session — ``mcp/launch.py`` will surface the
missing-venv error when the MCP supervisor next tries to spawn the server.

Progress and errors go to stderr; Claude Code surfaces SessionStart stderr to the user.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _venv_python(venv: Path) -> Path:
    """Return the path the venv's Python interpreter would live at on this OS."""
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _log(message: str) -> None:
    sys.stderr.write(f"[hoplite-bootstrap] {message}\n")
    sys.stderr.flush()


def _manifests_match(bundled: Path, snapshot: Path, python: Path) -> bool:
    """True iff the venv interpreter exists and the snapshot manifest matches the bundled one."""
    if not python.is_file() or not snapshot.is_file():
        return False
    return bundled.read_bytes() == snapshot.read_bytes()


def _rebuild(plugin_root: Path, data: Path) -> int:
    """Recreate the venv and pip install the project. Returns 0 on success, nonzero on failure."""
    mcp_dir = plugin_root / "mcp"
    bundled = mcp_dir / "pyproject.toml"
    snapshot = data / "pyproject.toml"
    venv = data / "venv"
    python = _venv_python(venv)

    data.mkdir(parents=True, exist_ok=True)
    if venv.exists():
        _log(f"removing stale venv at {venv}")
        shutil.rmtree(venv, ignore_errors=True)

    _log(f"creating venv at {venv}")
    rc = subprocess.run([sys.executable, "-m", "venv", str(venv)]).returncode
    if rc != 0:
        _log(f"venv creation failed (rc={rc})")
        shutil.rmtree(venv, ignore_errors=True)
        return rc

    _log("installing hoplite + deps via pip (editable)")
    rc = subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "-e",
            str(mcp_dir),
        ],
    ).returncode
    if rc != 0:
        _log(f"pip install failed (rc={rc})")
        # Tear down the partially-populated venv so launch.py's poll times out
        # cleanly instead of finding an empty venv and crashing on import yaml.
        shutil.rmtree(venv, ignore_errors=True)
        return rc

    shutil.copyfile(bundled, snapshot)
    _log("bootstrap complete")
    return 0


def main() -> int:
    plugin_root_env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    data_env = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not plugin_root_env or not data_env:
        _log("CLAUDE_PLUGIN_ROOT or CLAUDE_PLUGIN_DATA missing; skipping bootstrap")
        return 0

    plugin_root = Path(plugin_root_env)
    data = Path(data_env)
    bundled = plugin_root / "mcp" / "pyproject.toml"
    snapshot = data / "pyproject.toml"
    python = _venv_python(data / "venv")

    if _manifests_match(bundled, snapshot, python):
        return 0

    rc = _rebuild(plugin_root, data)
    if rc != 0:
        # Drop the snapshot so the next session retries from a clean slate.
        snapshot.unlink(missing_ok=True)
        _log("bootstrap FAILED — MCP server will not start until next session retries")

    # Always return 0: don't block the session. launch.py surfaces missing-venv if so.
    return 0


if __name__ == "__main__":
    sys.exit(main())
