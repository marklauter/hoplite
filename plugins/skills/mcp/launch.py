"""System-Python entry point that re-execs the MCP server under the bootstrapped venv.

Invoked by Claude Code per the plugin manifest's ``mcpServers.skills.command``.
Resolves ``${CLAUDE_PLUGIN_DATA}/venv/{Scripts,bin}/python(.exe)`` and execs
``hoplite.server`` under it. The venv is created and populated by the SessionStart
hook (``hooks/bootstrap-venv.py``); this script assumes it exists and fails loudly
if it does not.

Stdlib only — runs under whatever Python is on PATH at the moment Claude Code spawns
the MCP server.
"""

from __future__ import annotations

import os
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

    # execv replaces the current process — the MCP supervisor sees one PID, one
    # stdio pipe, and the venv Python running hoplite.server directly.
    os.execv(str(python), [str(python), "-m", "hoplite.server"])
    return 0  # unreachable on POSIX; reachable on Windows quirks


if __name__ == "__main__":
    sys.exit(main())
