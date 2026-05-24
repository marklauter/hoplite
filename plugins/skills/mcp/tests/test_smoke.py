"""Smoke test: spawn the server, check the 11-tool surface, run two roundtrips.

The slugify call is the only end-to-end assertion against a real implementation
(slugify is implemented, not stubbed). The insert call validates echo-style
return shape — WriteResult.id mirrors the input id.
"""

import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = frozenset(
    {
        "hoplite_init_corpus",
        "hoplite_match_nodes",
        "hoplite_traverse_nodes",
        "hoplite_invoke_node",
        "hoplite_read_node",
        "hoplite_insert_node",
        "hoplite_update_node",
        "hoplite_index_node",
        "hoplite_delete_node",
        "hoplite_apply_framing",
        "hoplite_slugify_text",
    }
)


async def _roundtrip() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "hoplite.server"])
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        init = await session.initialize()
        assert init.serverInfo.name == "hoplite_mcp"

        tool_list = await session.list_tools()
        names = {t.name for t in tool_list.tools}
        assert names >= EXPECTED_TOOLS, f"missing: {EXPECTED_TOOLS - names}"

        slug_result = await session.call_tool("hoplite_slugify_text", {"s": "Foo Bar Baz"})
        assert not slug_result.isError
        slug_block = slug_result.content[0]
        assert getattr(slug_block, "text", None) == "foo-bar-baz"

        insert_result = await session.call_tool(
            "hoplite_insert_node", {"id": "foo.md", "body": "hi"}
        )
        assert not insert_result.isError
        insert_block = insert_result.content[0]
        payload = json.loads(getattr(insert_block, "text", "{}"))
        assert payload["id"] == "foo.md"


def test_server_surface_and_roundtrips() -> None:
    asyncio.run(_roundtrip())
