"""FastMCP wiring for `hoplite_mcp`.

Exposes the four-tool agent-facing surface defined in docs/hoplite/tool-api.md.
Tool bodies live in `hoplite.tools`; the vault root is set at module import
to ``<cwd>/docs`` and the in-memory graph builds lazily on the first tool call.
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from hoplite import tools

mcp = FastMCP("hoplite_mcp")

tools.set_root(Path.cwd())


_READONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

_REINDEX = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=True,
    openWorldHint=False,
)

_DUMP = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=True,
    openWorldHint=False,
)


mcp.tool(name="hoplite_match_nodes", annotations=_READONLY)(tools.match_nodes)
mcp.tool(name="hoplite_traverse_nodes", annotations=_READONLY)(tools.traverse_nodes)
mcp.tool(name="hoplite_reindex", annotations=_REINDEX)(tools.reindex)
mcp.tool(name="hoplite_dump_index", annotations=_DUMP)(tools.dump_index)


if __name__ == "__main__":
    mcp.run()
