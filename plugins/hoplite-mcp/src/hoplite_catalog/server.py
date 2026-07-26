"""Stdio JSON-RPC host for the `catalog` MCP server.

The transport is hand-rolled on the standard library. ``contents`` needs no YAML parser
and no SDK, so the server needs no dependencies either, and the plugin runs under
whatever Python is on PATH with no venv to bootstrap — the same choice the
frontmatter hook next door makes. When the graph tools in
``docs/specs/hoplite-tool-api.md`` land, this module is the layer to swap for the
official SDK: the tool body in ``hoplite_catalog.contents`` is pure and knows nothing
about transport.

MCP stdio framing is one JSON message per line. Stdout carries protocol traffic and
nothing else, so every log line goes to stderr, where Claude Code surfaces it under
``--debug mcp``.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Final, TextIO, cast

from hoplite_catalog.contents import collect, render, resolve_under

__all__ = ["DEFAULT_UNDER", "PROTOCOL_VERSION", "SERVER_NAME", "TOOLS", "respond", "serve"]

SERVER_NAME: Final = "catalog"
SERVER_VERSION: Final = "0.1.0"
PROTOCOL_VERSION: Final = "2025-06-18"
DEFAULT_UNDER: Final = "docs"

_PARSE_ERROR: Final = -32700
_INVALID_REQUEST: Final = -32600
_METHOD_NOT_FOUND: Final = -32601

# Shaped like method help: one line on what it does, then Returns. When to call it stays
# out — the authoring skills already say when to search the corpus for a pre-existing
# document, and a trigger here would fire on writes that have nothing to do with the
# corpus. The skills do not name this tool yet, which is the gap that connects them.
_CONTENTS_DESCRIPTION: Final = (
    "Survey a folder of the markdown corpus without opening files, or trace how its "
    "documents link.\n\n"
    "Returns: a path line per document, then its YAML frontmatter between `---` fences. "
    "Documents without frontmatter show just the path. A property whose value is a "
    "`[[wikilink]]` is an edge; anything else is a claim about the document."
)

TOOLS: Final[tuple[dict[str, object], ...]] = (
    {
        "name": "contents",
        "title": "List corpus documents with their frontmatter",
        "description": _CONTENTS_DESCRIPTION,
        "inputSchema": {
            "type": "object",
            "properties": {
                "under": {
                    "type": "string",
                    "description": (
                        "Folder to list, relative to the corpus root, like "
                        f"'docs/glossary'. Recurses into subfolders. Defaults to '{DEFAULT_UNDER}'."
                    ),
                }
            },
            "additionalProperties": False,
        },
        "annotations": {
            "title": "List corpus documents with their frontmatter",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
)


def _as_mapping(value: object) -> dict[str, object] | None:
    """Narrow decoded JSON to an object. JSON keys are always strings, so the cast is
    sound; ``isinstance`` alone would leave the key and value types unknown."""
    return cast("dict[str, object]", value) if isinstance(value, dict) else None


def _text_result(text: str, *, is_error: bool = False) -> dict[str, object]:
    """Wrap text in the MCP tool-result envelope."""
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def _call_contents(root: Path, arguments: dict[str, object]) -> dict[str, object]:
    """Run the ``contents`` tool. Raises ``ValueError`` on a bad argument."""
    under = arguments.get("under", DEFAULT_UNDER)
    if not isinstance(under, str):
        raise ValueError("'under' must be a string")
    listing = render(collect(root, resolve_under(root, under)))
    return _text_result(listing or f"no markdown documents under {under!r}")


def _call_tool(root: Path, params: dict[str, object]) -> dict[str, object]:
    """Dispatch ``tools/call``. An unknown tool or bad argument comes back as an error
    result rather than a JSON-RPC error, so the agent can read the message and retry."""
    name = params.get("name")
    arguments = _as_mapping(params.get("arguments")) or {}
    try:
        if name != "contents":
            raise ValueError(f"unknown tool: {name!r}")
        return _call_contents(root, arguments)
    except ValueError as exc:
        return _text_result(str(exc), is_error=True)
    except OSError as exc:
        return _text_result(f"cannot read the corpus: {exc}", is_error=True)


def _dispatch(root: Path, method: str, params: dict[str, object]) -> dict[str, object] | None:
    """Return the result for ``method``, or ``None`` when the method is unknown."""
    match method:
        case "initialize":
            return {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            }
        case "tools/list":
            return {"tools": list(TOOLS)}
        case "tools/call":
            return _call_tool(root, params)
        case "ping":
            return {}
        case _:
            return None


def _error(request_id: object, code: int, message: str) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def respond(root: Path, line: str) -> dict[str, object] | None:
    """Turn one incoming line into one outgoing message, or ``None`` when none is owed.

    A notification carries no ``id`` and gets no reply — that includes
    ``notifications/initialized``, which every client sends and no server answers.
    """
    try:
        decoded: object = json.loads(line)
    except json.JSONDecodeError as exc:
        return _error(None, _PARSE_ERROR, f"invalid JSON: {exc}")

    message = _as_mapping(decoded)
    if message is None:
        return _error(None, _INVALID_REQUEST, "message is not a JSON object")

    request_id: object = message.get("id")
    method: object = message.get("method")
    if not isinstance(method, str):
        return None if request_id is None else _error(request_id, _INVALID_REQUEST, "no method")

    result = _dispatch(root, method, _as_mapping(message.get("params")) or {})

    if request_id is None:
        return None  # a notification; the reply, if any, is discarded
    if result is None:
        return _error(request_id, _METHOD_NOT_FOUND, f"unknown method: {method}")
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def serve(root: Path, stdin: TextIO, stdout: TextIO) -> int:
    """Read newline-delimited JSON from ``stdin`` until it closes, replying on ``stdout``."""
    for line in stdin:
        stripped = line.strip()
        if not stripped:
            continue
        message = respond(root, stripped)
        if message is None:
            continue
        stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
        stdout.flush()
    return 0


def main() -> int:
    # A Windows interpreter's text streams default to a locale codec (cp1252), which
    # mangles the non-ASCII a corpus carries. Pin all three to UTF-8 before any traffic.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")

    root = Path.cwd()
    sys.stderr.write(f"[hoplite-catalog] serving; corpus root = {root}\n")
    sys.stderr.flush()
    return serve(root, sys.stdin, sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
