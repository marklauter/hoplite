"""FastMCP wiring for `hoplite_mcp`.

Exposes the 11-tool agent-facing surface defined in docs/mcp/tool-api.md.
All tool bodies are echo-style stubs in `hoplite.tools`; this module is the
MCP boundary — names, hint annotations, and the stdio runner.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from hoplite import tools

mcp = FastMCP("hoplite_mcp")


_READONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

_INIT = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

_INSERT = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)

_DESTRUCTIVE_IDEMPOTENT = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=True,
    openWorldHint=False,
)

_DESTRUCTIVE_NON_IDEMPOTENT = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=False,
)


mcp.tool(name="hoplite_init_corpus", annotations=_INIT)(tools.init_corpus)
mcp.tool(name="hoplite_match_nodes", annotations=_READONLY)(tools.match_nodes)
mcp.tool(name="hoplite_traverse_nodes", annotations=_READONLY)(tools.traverse_nodes)
mcp.tool(name="hoplite_invoke_node", annotations=_READONLY)(tools.invoke_node)
mcp.tool(name="hoplite_read_node", annotations=_READONLY)(tools.read_node)
mcp.tool(name="hoplite_insert_node", annotations=_INSERT)(tools.insert_node)
mcp.tool(name="hoplite_update_node", annotations=_DESTRUCTIVE_IDEMPOTENT)(tools.update_node)
mcp.tool(name="hoplite_index_node", annotations=_DESTRUCTIVE_IDEMPOTENT)(tools.index_node)
mcp.tool(name="hoplite_delete_node", annotations=_DESTRUCTIVE_NON_IDEMPOTENT)(tools.delete_node)
mcp.tool(name="hoplite_apply_framing", annotations=_DESTRUCTIVE_IDEMPOTENT)(tools.apply_framing)


if __name__ == "__main__":
    mcp.run()
