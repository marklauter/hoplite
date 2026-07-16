"""FastMCP wiring for `catalog`.

Exposes the four-tool agent-facing surface defined in docs/hoplite/hoplite-tool-api.md.
Tool bodies live in `hoplite.tools`; the corpus root is set at module import
to ``<cwd>/docs`` and the in-memory graph builds lazily on the first tool call.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from hoplite import tools

# FastMCP's stdio transport reserves stdout for JSON-RPC; stderr is the only
# safe log channel. Claude Code surfaces this stream under `--debug mcp`.
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[hoplite-server] %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP("catalog")

tools.set_root(Path.cwd())
logger.info("starting; corpus root = %s", Path.cwd() / "docs")


mcp.tool(
    name="where",
    annotations=ToolAnnotations(
        title="Search the hoplite knowledge graph",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)(tools.match_nodes)

mcp.tool(
    name="relatives",
    annotations=ToolAnnotations(
        title="Walk hoplite's wikilink and related-edge graph",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)(tools.traverse_nodes)

mcp.tool(
    name="refresh",
    annotations=ToolAnnotations(
        title="Rebuild the hoplite in-memory graph",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)(tools.reindex)

mcp.tool(
    name="export",
    annotations=ToolAnnotations(
        title="Dump the hoplite graph to a SQLite snapshot",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)(tools.dump_index)


if __name__ == "__main__":
    mcp.run()
