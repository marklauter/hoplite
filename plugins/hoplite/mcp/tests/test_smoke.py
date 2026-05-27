"""End-to-end smoke test: spawn the MCP server against a tmp corpus and exercise the 4 tools.

Builds a small corpus with mandatory frontmatter, a wikilink between two notes,
a forward reference to a missing target (ghost materialization), and a shared
tag across two documents. Then drives the server through all four tools and
inspects the dumped SQLite file.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, cast  # cast: used by callers of _parse_json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = frozenset(
    {
        "where",
        "relatives",
        "refresh",
        "export",
    },
)


_FRONTMATTER_TEMPLATE = """\
---
title: {title}
summary: {summary}
tags: [{tags}]
created: 2026-05-25
aliases: []
---
{body}
"""


def _write_corpus(root: Path) -> None:
    """Build a 3-document corpus under ``root/docs/`` with the shape the smoke test expects."""
    notes = root / "docs" / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    (notes / "alpha.md").write_text(
        _FRONTMATTER_TEMPLATE.format(
            title="Alpha",
            summary="The alpha document references beta and a missing one.",
            tags="shared, alpha-tag",
            body=(
                # `[[notes/beta]]` exercises the spec's extension-tolerant resolution —
                # it must resolve to notes/beta.md (per architecture.md#wikilinks-and-ghost-documents).
                "See [[notes/beta]] for the next step. Also [[notes/missing.md]] is unwritten.\n"
            ),
        ),
        encoding="utf-8",
    )
    (notes / "beta.md").write_text(
        _FRONTMATTER_TEMPLATE.format(
            title="Beta",
            summary="The beta document, downstream of alpha.",
            tags="shared, beta-tag",
            body="This is beta. Alpha mentions us.\n",
        ),
        encoding="utf-8",
    )
    (notes / "gamma.md").write_text(
        _FRONTMATTER_TEMPLATE.format(
            title="Gamma",
            summary="Unrelated to the others.",
            tags="gamma-tag",
            body="Gamma stands alone.\n",
        ),
        encoding="utf-8",
    )


async def _drive_server(root: Path) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "hoplite.server"],
        cwd=str(root),
    )
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        init = await session.initialize()
        assert init.serverInfo.name == "catalog"

        tool_list = await session.list_tools()
        names = {t.name for t in tool_list.tools}
        assert names == EXPECTED_TOOLS, f"expected exactly {EXPECTED_TOOLS}, got {names}"

        # match_nodes — text search should find alpha when querying for its body terms.
        match_result = await session.call_tool(
            "where",
            {"predicate": {"text": "alpha"}, "k": 3},
        )
        assert not match_result.isError, match_result.content
        hits = cast(list[dict[str, Any]], _parse_json(match_result))
        hit_paths = {h["path"] for h in hits}
        assert "notes/alpha.md" in hit_paths

        # match_nodes — tag predicate post-filter narrows to the two docs tagged "shared".
        tag_result = await session.call_tool(
            "where",
            {"predicate": {"text": "document", "tagged": "shared"}, "k": 5},
        )
        assert not tag_result.isError, tag_result.content
        tag_hits = cast(list[dict[str, Any]], _parse_json(tag_result))
        tag_paths = {h["path"] for h in tag_hits}
        assert tag_paths == {"notes/alpha.md", "notes/beta.md"}

        # traverse_nodes — from alpha at depth 1 reaches beta via the wikilink edge.
        traverse_result = await session.call_tool(
            "relatives",
            {"from_": "notes/alpha.md", "depth": 1},
        )
        assert not traverse_result.isError, traverse_result.content
        traversal = cast(list[dict[str, Any]], _parse_json(traverse_result))
        reached = {h["path"] for h in traversal}
        assert "notes/beta.md" in reached
        assert "notes/missing.md" in reached  # ghost is reachable too

        # dump_index — snapshot to a temp file and inspect.
        # .hoplite/ sits at the cwd level, alongside docs/, not inside it.
        dump_destination = root / ".hoplite" / "index.sqlite"
        dump_result = await session.call_tool(
            "export",
            {"path": str(dump_destination)},
        )
        assert not dump_result.isError, dump_result.content
        dump_payload = cast(dict[str, Any], _parse_json(dump_result))
        assert dump_payload["counts"]["documents"] == 3
        assert dump_payload["counts"]["ghosts"] == 1

        # Verify the dumped SQLite file matches the in-memory state.
        conn = sqlite3.connect(str(dump_destination))
        try:
            # documents — five-column shape, three resolved + one ghost.
            cursor = conn.execute("SELECT COUNT(*) FROM documents WHERE resolved = 1")
            assert cursor.fetchone()[0] == 3
            cursor = conn.execute("SELECT COUNT(*) FROM documents WHERE resolved = 0")
            assert cursor.fetchone()[0] == 1

            # nodes — every document has a row; kind is always 'document' day one.
            cursor = conn.execute("SELECT COUNT(*) FROM nodes WHERE kind = 'document'")
            assert cursor.fetchone()[0] == 4  # 3 resolved + 1 ghost

            # edges — only mentions and related, no member.
            cursor = conn.execute("SELECT COUNT(*) FROM edges WHERE kind = 'mentions'")
            assert cursor.fetchone()[0] >= 2  # alpha→beta and alpha→missing
            cursor = conn.execute("SELECT COUNT(*) FROM edges WHERE kind = 'member'")
            assert cursor.fetchone()[0] == 0  # member edges abolished

            # node_properties — tags live here as (node_id, 'tags', slug) rows.
            cursor = conn.execute(
                "SELECT COUNT(*) FROM node_properties WHERE key = 'tags' AND value = 'shared'",
            )
            assert cursor.fetchone()[0] == 2  # alpha and beta both carry 'shared'

            # Every resolved document has a title property row.
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT node_id) FROM node_properties WHERE key = 'title'
            """)
            assert cursor.fetchone()[0] == 3

            # Cross-table join — relational shape works end-to-end.
            cursor = conn.execute("""
                SELECT d.path, COUNT(p.key) AS prop_count
                FROM documents d
                LEFT JOIN node_properties p ON p.node_id = d.id
                WHERE d.resolved = 1
                GROUP BY d.path
                ORDER BY d.path
            """)
            rows = cursor.fetchall()
            assert len(rows) == 3
            for _path, prop_count in rows:
                # Each resolved doc carries title, summary, created, tags (>=1 row) — at least 4.
                assert prop_count >= 4
        finally:
            conn.close()


def _parse_json(result: object) -> Any:
    """Pull the structured payload from an MCP tool result; unwrap ``{"result": ...}``."""
    structured: Any = getattr(result, "structuredContent", None)
    if structured is None:
        # Fallback for tools without an output_schema — parse the text content.
        content = getattr(result, "content", None)
        assert content, f"empty content on result: {result}"
        text = getattr(content[0], "text", None)
        assert text is not None, f"no text on content block: {content[0]}"
        return json.loads(text)
    try:
        keys = list(structured.keys())
    except AttributeError:
        return structured
    if keys == ["result"]:
        return structured["result"]
    return structured


def test_server_end_to_end(tmp_path: Path) -> None:
    _write_corpus(tmp_path)
    asyncio.run(_drive_server(tmp_path))
