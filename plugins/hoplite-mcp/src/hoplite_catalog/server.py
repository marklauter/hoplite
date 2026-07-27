"""Stdio JSON-RPC host for the `catalog` MCP server.

The transport is hand-rolled on the standard library, and stays that way. ``contents``
needs no YAML parser and no SDK, so the server needs no dependencies either, and the
plugin runs under whatever Python is on PATH with no venv to bootstrap — the same choice
the frontmatter hook next door makes. Adding a dependency here reintroduces that install
step for every user, and the graph tools designed in ``docs/specs/hoplite-tool-api.md``
do not change that: they are more tools on this host, not a reason to adopt another one.

MCP stdio framing is one JSON message per line. Stdout carries protocol traffic and
nothing else, so every log line goes to stderr, where Claude Code surfaces it under
``--debug mcp``.
"""

from __future__ import annotations

import io
import json
import sys
import traceback
from pathlib import Path
from typing import Final, TextIO, cast

from hoplite_catalog.adapters import RealFiles
from hoplite_catalog.contents import collect, other_files, resolve_under, walk
from hoplite_catalog.corpus import Corpus
from hoplite_catalog.errors import CallerError
from hoplite_catalog.rendering import render, render_report, render_vocabulary
from hoplite_catalog.vocabulary import tally

__all__ = ["DEFAULT_UNDER", "PROTOCOL_VERSION", "SERVER_NAME", "TOOLS", "respond", "serve"]

SERVER_NAME: Final = "catalog"
# Pinned to .claude-plugin/plugin.json by a test, since initialize reports it.
SERVER_VERSION: Final = "0.2.0"
PROTOCOL_VERSION: Final = "2025-06-18"
# The corpus root, not a folder name. One corpus keeps its documents in `docs`, another in
# `vault`, another at the top level with no wrapper folder at all. Defaulting to any of
# those names guesses at someone's layout and fails for everyone else; defaulting to the
# root shows the caller what the layout is, which is the orientation call this tool is for.
DEFAULT_UNDER: Final = "."

_PARSE_ERROR: Final = -32700
_INVALID_REQUEST: Final = -32600
_METHOD_NOT_FOUND: Final = -32601
_INTERNAL_ERROR: Final = -32603

# Shaped like method help: one line on what it does, then Returns. When to call it stays
# out — the authoring skills already say when to search the corpus for a pre-existing
# document, and a trigger here would fire on writes that have nothing to do with the
# corpus. The skills do not name this tool yet, which is the gap that connects them.
_CONTENTS_DESCRIPTION: Final = (
    "Survey one folder of the markdown corpus and trace its documents' edges.\n\n"
    "Returns three groups, each under a `#` heading.\n\n"
    "`# directories` is the folder tree rooted at the one asked for, to full depth, each "
    "with the count of documents directly in it — call again with one of those folders to "
    "read it. `# other files` is the non-markdown files in the folder. `# documents` is "
    "the path per document in that folder alone, and, if available, its frontmatter "
    "properties, one per line, with a blank line between documents. A property whose "
    "value is a `[[wikilink]]` is an edge; anything else is a claim about the document.\n\n"
    "Anything the tool will not follow is named rather than hidden. A folder or file "
    "marked `links outside the corpus`, or a folder marked `cannot be listed`, was not "
    "read. A document that could not be read carries the reason where its properties "
    "would be."
)

_VOCABULARY_DESCRIPTION: Final = (
    "Count the frontmatter keys in use across a folder of the markdown corpus.\n\n"
    "Returns one `key: documents` line per distinct key, ordered by key, where the "
    "number is how many documents carry it. Recurses. Call it before `contents` with "
    "`keys`, since a key that does not exist returns nothing."
)

_UNDER_SCHEMA: Final[dict[str, object]] = {
    "type": "string",
    "description": (
        "Folder relative to the corpus root, like 'docs/glossary'. Defaults to the corpus "
        "root, which is where to start when you do not yet know how the corpus is laid out. "
        "Hidden folders are never walked into, though naming one directly still works."
    ),
}

TOOLS: Final[tuple[dict[str, object], ...]] = (
    {
        "name": "contents",
        "title": "List one folder of the corpus with its documents' frontmatter",
        "description": _CONTENTS_DESCRIPTION,
        "inputSchema": {
            "type": "object",
            "properties": {
                "under": _UNDER_SCHEMA,
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Frontmatter properties to keep, like ['title', 'tags']. Omit to "
                        "get every property, including summary. An empty list returns "
                        "paths alone. Use it to trade detail for size when a folder is "
                        "too large to read whole. `vocabulary` lists the keys in use."
                    ),
                },
            },
            "additionalProperties": False,
        },
        "annotations": {
            "title": "List one folder of the corpus with its documents' frontmatter",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "vocabulary",
        "title": "Count the frontmatter keys in use",
        "description": _VOCABULARY_DESCRIPTION,
        "inputSchema": {
            "type": "object",
            "properties": {"under": _UNDER_SCHEMA},
            "additionalProperties": False,
        },
        "annotations": {
            "title": "Count the frontmatter keys in use",
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


def _string_set(value: object, name: str) -> frozenset[str] | None:
    """Read an optional list-of-strings argument, or ``None`` when it is absent.

    An empty list is not the same as an omitted one: ``keys: []`` asks for paths alone,
    where an omitted ``keys`` asks for every property.
    """
    if value is None:
        return None
    if not isinstance(value, list):
        raise CallerError(f"{name!r} must be a list of strings")
    items = cast("list[object]", value)
    if not all(isinstance(item, str) for item in items):
        raise CallerError(f"{name!r} must be a list of strings")
    return frozenset(cast("list[str]", items))


def _under_argument(arguments: dict[str, object]) -> str:
    """Read the ``under`` argument, which every tool takes and defaults the same way."""
    under = arguments.get("under", DEFAULT_UNDER)
    if not isinstance(under, str):
        raise CallerError("'under' must be a string")
    return under


def _call_contents(corpus: Corpus, arguments: dict[str, object]) -> dict[str, object]:
    """Run the ``contents`` tool. Raises ``CallerError`` on a bad argument."""
    under = _under_argument(arguments)
    keys = _string_set(arguments.get("keys"), "keys")

    target = resolve_under(corpus, under)
    documents = collect(corpus, target)
    projected = [document.projected(keys) for document in documents]

    # A misspelled key would otherwise return a bare path list, which reads as "these
    # documents have no frontmatter" rather than "that key does not exist". The
    # `had_frontmatter` guard is what separates those two: a folder where nothing has
    # frontmatter at all is not the caller's mistake, so it must not be blamed on the keys.
    # An empty `keys` is exempt too — it asks for paths alone, and gets them.
    #
    # The refusal carries the keys that are in use, because the caller's next move is a
    # second call with a corrected `keys`, and the answer to "corrected to what" was already
    # read to decide this. Withholding it costs them a `vocabulary` round trip to learn what
    # this call already knows. The list is what one directory carries, which is the scope
    # the retry is against, and is bounded by that — ten keys in the busiest folder here.
    had_frontmatter = any(document.properties() for document in documents)
    kept_any = any(document.properties() for document in projected)
    if keys and had_frontmatter and not kept_any:
        in_use = [use.key for use in tally(documents)]
        raise CallerError(
            f"none of the requested keys appear in any document under {under!r}: "
            f"{sorted(keys)}; the keys in use there are {in_use}"
        )

    # A single document as `under` has no subtree and no siblings to report, so it gets the
    # listing alone. Wrapping one document in three headings would be all frame, no picture.
    if corpus.is_file(target):
        return _text_result(render(projected))
    return _text_result(render_report(walk(corpus, target), other_files(corpus, target), projected))


def _call_vocabulary(corpus: Corpus, arguments: dict[str, object]) -> dict[str, object]:
    """Run the ``vocabulary`` tool. Raises ``CallerError`` on a bad argument."""
    under = _under_argument(arguments)
    uses = tally(collect(corpus, resolve_under(corpus, under), recurse=True))
    if not uses:
        return _text_result(f"no frontmatter keys under {under!r}")
    return _text_result(render_vocabulary(uses))


def _call_tool(corpus: Corpus, params: dict[str, object]) -> dict[str, object]:
    """Dispatch ``tools/call``. An unknown tool or bad argument comes back as an error
    result rather than a JSON-RPC error, so the agent can read the message and retry.

    Only ``CallerError`` gets that treatment. This used to catch ``ValueError``, which is
    the same class a bug raises, so a defect in the walk came back as a readable message the
    agent would retry against and nothing reached the log. A plain ``ValueError`` now
    travels to ``respond``, which reports it as an internal error and prints the traceback.
    """
    name = params.get("name")
    arguments = _as_mapping(params.get("arguments")) or {}
    try:
        match name:
            case "contents":
                return _call_contents(corpus, arguments)
            case "vocabulary":
                return _call_vocabulary(corpus, arguments)
            case _:
                raise CallerError(f"unknown tool: {name!r}")
    except CallerError as exc:
        return _text_result(str(exc), is_error=True)
    except OSError as exc:
        # The backstop, not the normal path: an unreadable document and an unreadable
        # directory are both reported in the listing. `exc.strerror` rather than `exc`,
        # because the full message carries an absolute host path, which nothing else the
        # server emits does.
        return _text_result(
            f"cannot read the corpus: {exc.strerror or type(exc).__name__}", is_error=True
        )


def _dispatch(corpus: Corpus, method: str, params: dict[str, object]) -> dict[str, object] | None:
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
            return _call_tool(corpus, params)
        case "ping":
            return {}
        case _:
            return None


def _error(request_id: object, code: int, message: str) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def respond(corpus: Corpus, line: str) -> dict[str, object] | None:
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

    if request_id is None:
        # Nothing is owed, so nothing is run. Dispatching first and discarding the result
        # let a `tools/call` notification read every document in the corpus for no reply.
        return None

    try:
        result = _dispatch(corpus, method, _as_mapping(message.get("params")) or {})
    except Exception:
        # The host boundary, and the only place this package catches broadly. A bug must
        # not take the server down mid-session, and it must not be disguised as an answer
        # either: the agent gets a protocol-level error it cannot mistake for a result, and
        # the traceback goes to stderr, where Claude Code surfaces it under `--debug mcp`.
        # The message carries nothing, because an exception's own text carries host paths.
        # `Exception`, not `BaseException`, so KeyboardInterrupt still stops the process.
        traceback.print_exc(file=sys.stderr)
        return _error(request_id, _INTERNAL_ERROR, f"internal error handling {method}")
    if result is None:
        return _error(request_id, _METHOD_NOT_FOUND, f"unknown method: {method}")
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def serve(corpus: Corpus, stdin: TextIO, stdout: TextIO) -> int:
    """Read newline-delimited JSON from ``stdin`` until it closes, replying on ``stdout``.

    ``strip`` takes a leading byte-order mark along with the whitespace. A conforming
    client never sends one, but a Windows shell piping into the process does, and the
    resulting parse error is a confusing way to learn that.
    """
    for line in stdin:
        stripped = line.strip("﻿ \t\r\n")
        if not stripped:
            continue
        message = respond(corpus, stripped)
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
    # The composition root: the one place the real filesystem is named, and the one place a
    # `Corpus` is built from it. Everything below takes the corpus and never the port.
    return serve(Corpus(RealFiles(), root), sys.stdin, sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
