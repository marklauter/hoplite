"""Smoke test: spawn the server, do the MCP handshake, call the hello tool."""
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_hello_tool_roundtrip() -> None:
    params = StdioServerParameters(command="python", args=["-m", "hoplite.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            assert init.serverInfo.name == "skills-hello"

            tools = await session.list_tools()
            assert "hello" in [t.name for t in tools.tools]

            result = await session.call_tool("hello", {"name": "Mark"})
            assert result.content[0].text == "Hello, Mark!"
