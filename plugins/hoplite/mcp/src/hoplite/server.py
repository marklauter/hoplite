"""FastMCP wiring for `graph_mcp`.

Exposes the four-tool agent-facing surface defined in docs/hoplite/tool-api.md.
Tool bodies live in `hoplite.tools`; the corpus root is set at module import
to ``<cwd>/docs`` and the in-memory graph builds lazily on the first tool call.
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from hoplite import tools

mcp = FastMCP("graph_mcp")

tools.set_root(Path.cwd())


mcp.tool(
    name="hoplite_match_nodes",
    annotations=ToolAnnotations(
        title="Search the hoplite knowledge graph",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)(tools.match_nodes)

mcp.tool(
    name="hoplite_traverse_nodes",
    annotations=ToolAnnotations(
        title="Walk hoplite's wikilink and related-edge graph",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)(tools.traverse_nodes)

mcp.tool(
    name="hoplite_reindex",
    annotations=ToolAnnotations(
        title="Rebuild the hoplite in-memory graph",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)(tools.reindex)

mcp.tool(
    name="hoplite_dump_index",
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
