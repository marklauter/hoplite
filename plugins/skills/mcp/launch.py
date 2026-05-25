"""System-Python entry point that runs the MCP server under the bootstrapped venv.

Invoked by Claude Code per the plugin manifest's ``mcpServers.skills.command``.
Resolves ``${CLAUDE_PLUGIN_DATA}/venv/{Scripts,bin}/python(.exe)`` and runs
``hoplite.server`` under it as a child process. The venv is created and populated by
the SessionStart hook (``hooks/bootstrap-venv.py``); this script assumes it exists
and fails loudly if it does not.

Uses ``subprocess.run`` with inherited stdio rather than ``os.execv``. On Windows,
``os.execv`` doesn't truly replace the process — CPython spawns a child and the
parent exits, which breaks the MCP supervisor's stdio pipe management. The
parent-stays-alive model works identically on Windows and POSIX.

Stdlib only — runs under whatever Python is on PATH at the moment Claude Code spawns
the MCP server.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _resolve_venv_python(data: Path) -> Path | None:
    """Return the path to the venv's Python interpreter, or ``None`` if absent."""
    venv = data / "venv"
    for candidate in (venv / "Scripts" / "python.exe", venv / "bin" / "python"):
        if candidate.is_file():
            return candidate
    return None


def main() -> int:
    data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data:
        sys.stderr.write("[hoplite-launch] CLAUDE_PLUGIN_DATA not set in environment\n")
        return 1

    python = _resolve_venv_python(Path(data))
    if python is None:
        sys.stderr.write(
            f"[hoplite-launch] venv interpreter not found under {data}/venv; "
            "the SessionStart bootstrap should have created it\n",
        )
        return 1

    # Run the server as a child; stdin/stdout/stderr inherit from the parent so the
    # MCP supervisor's pipes stay connected. The parent process stays alive until the
    # child exits, propagating its return code. Signals (SIGINT/SIGTERM, or Windows
    # console control events) reach the child via the OS process group.
    return subprocess.run([str(python), "-m", "hoplite.server"]).returncode


if __name__ == "__main__":
    sys.exit(main())
