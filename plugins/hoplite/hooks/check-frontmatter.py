"""PostToolUse hook: warn when a .md file under docs/ has a malformed wikilink.

Exits 2 with an advisory on stderr so Claude Code surfaces it to the agent. The write
is not rolled back; the agent fixes the link in a follow-up edit.

Every edge target is validated against the shared grammar in the sibling
``edge_grammar`` module — the executable form of docs/hoplite/expressing-edges.md:

- Frontmatter: each ``[[wikilink]]`` in a non-special property value (an edge), plus
  whether it is quoted, since Obsidian indexes only quoted links.
- Body: each inline ``[[wikilink]]``, with code spans and fences skipped.

Nothing in frontmatter is mandatory, so this hook does not check for required keys or
field types — that, and real YAML parsing, are the indexer's job. Line-scan based, no
PyYAML, since the hook runs under whatever ``python`` is on PATH, not the project venv.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edge_grammar import (  # noqa: E402  — sibling module; the hook runs by path (see hooks.json)
    frontmatter_wikilink_targets,
    inline_wikilinks,
    validate_target,
)

WATCHED_TOOLS = {"Write", "Edit", "MultiEdit"}

_GUIDANCE = """\
An edge target is a page path: a slug with an optional folder prefix (`circle`, \
`lib/shapes/circle`) and an optional `#section` or `#^block` anchor. There are no \
colons — the folder path is the namespace. In frontmatter a wikilink must be quoted \
(`cites: "[[circle]]"`); display text (`|`) and embedding (`!`) are body-only. \
Full grammar: docs/hoplite/expressing-edges.md.
"""

ADVISORY_TEMPLATE = """\
[frontmatter-check] {path} — malformed wikilink(s):
{problems}

{guidance}"""


def _document_issues(path: Path) -> list[str]:
    """Return one message per malformed or unquoted wikilink, frontmatter then body."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return []  # can't read; not our concern

    lines = text.splitlines()
    problems: list[str] = []

    if lines and lines[0] == "---":
        closing = next((i for i, ln in enumerate(lines[1:], start=1) if ln == "---"), None)
        if closing is None:
            return ["opening `---` has no closing `---` (unclosed frontmatter)"]
        fm_lines = lines[1:closing]
        body = "\n".join(lines[closing + 1 :])
        body_offset = closing + 1  # body line 1 == file line closing + 2
    else:
        fm_lines = []
        body = text
        body_offset = 0

    for target, quoted, idx in frontmatter_wikilink_targets(fm_lines):
        line_no = idx + 2  # fm_lines[0] is file line 2 (after the opening `---`)
        if not quoted:
            problems.append(
                f'line {line_no}: `{target}` is unquoted — write `"[[{target}]]"` '
                "(Obsidian indexes only quoted links)"
            )
        msg = validate_target(target)
        if msg is not None:
            problems.append(f"line {line_no}: {msg}")

    for target, line in inline_wikilinks(body):
        msg = validate_target(target, inline=True)
        if msg is not None:
            problems.append(f"line {line + body_offset}: {msg}")

    return problems


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") not in WATCHED_TOOLS:
        return 0

    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return 0

    path = Path(file_path)
    if path.suffix.lower() != ".md":
        return 0

    if "docs" not in {part.lower() for part in path.parts}:
        return 0

    if not path.is_file():
        return 0

    problems = _document_issues(path)
    if not problems:
        return 0

    advisory = ADVISORY_TEMPLATE.format(
        path=file_path,
        problems="\n".join(f"  - {p}" for p in problems),
        guidance=_GUIDANCE,
    )
    # Write UTF-8 bytes directly: the guidance carries em-dashes and other non-ASCII,
    # and a Windows interpreter's text-mode stderr defaults to a locale codec (cp1252),
    # which Claude Code then misreads as UTF-8 (mojibake).
    try:
        sys.stderr.buffer.write(advisory.encode("utf-8"))
        sys.stderr.buffer.flush()
    except (AttributeError, ValueError):
        sys.stderr.write(advisory)
    return 2


if __name__ == "__main__":
    sys.exit(main())
