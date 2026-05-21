from mcp.server.fastmcp import FastMCP

mcp = FastMCP("skills-hello")


@mcp.tool()
def hello(name: str = "world") -> str:
    """Return a friendly greeting."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run()
