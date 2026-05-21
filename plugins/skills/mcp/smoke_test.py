"""Smoke test: spawn the server, do the MCP handshake, call the hello tool."""
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    params = StdioServerParameters(command="python", args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print(f"server: {init.serverInfo.name} v{init.serverInfo.version}")

            tools = await session.list_tools()
            print(f"tools: {[t.name for t in tools.tools]}")

            result = await session.call_tool("hello", {"name": "Mark"})
            print(f"hello -> {result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
