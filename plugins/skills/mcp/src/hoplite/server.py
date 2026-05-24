import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DB_PATH = Path(__file__).resolve().parents[2] / "hello.db"


def _init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, text TEXT NOT NULL)"
        )
        (count,) = conn.execute("SELECT COUNT(*) FROM messages").fetchone()
        if count == 0:
            conn.execute("INSERT INTO messages (text) VALUES (?)", ("hello world",))


_init_db()

mcp = FastMCP("skills-hello")


@mcp.tool()
def hello(name: str = "world") -> str:
    """Return a friendly greeting."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run()
