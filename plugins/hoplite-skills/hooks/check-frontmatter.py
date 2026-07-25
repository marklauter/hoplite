"""PostToolUse hook: warn when a .md file under docs/ has a malformed wikilink.

Exits 2 with an advisory on stderr so Claude Code surfaces it to the agent. The write
is not rolled back; the agent fixes the link in a follow-up edit.

Two things are checked. Every edge target is validated against the shared grammar in
the sibling ``edge_grammar`` module — the executable form of
../references/expressing-edges.md:

- Frontmatter: each ``[[wikilink]]`` in a non-special property value (an edge), plus
  whether it is quoted, since Obsidian indexes only quoted links.
- Body: each inline ``[[wikilink]]``, with code spans and fences skipped.

And the frontmatter block, if one is present, is checked for structural well-formedness.
Nothing in frontmatter is mandatory, but a block that exists must be well formed: this
hook flags the malformations a line scan can name without false positives — an unclosed
fence, a tab in indentation, and a root line that is not a ``key: value`` mapping entry.
Value types, key typos, and real YAML parsing stay the indexer's job. Line-scan based,
no PyYAML, since the hook runs under whatever ``python`` is on PATH, not the project venv.
"""

import json
import re
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
Frontmatter, when present, must be well-formed YAML: indent with spaces (never tabs) \
and write each property as a `key: value` mapping entry — a key needs a colon followed \
by a space. Every `[[wikilink]]` in a property value is an edge and must be quoted \
(`cites: "[[circle]]"`); an edge target is a page path — a slug with an optional folder \
prefix (`lib/shapes/circle`) and an optional `#section`/`#^block` anchor, no colons. \
Display text (`|`) and embedding (`!`) are body-only. Full grammar: \
references/frontmatter.md and references/expressing-edges.md in the hoplite-skills plugin.
"""

ADVISORY_TEMPLATE = """\
[frontmatter-check] {path} — frontmatter issue(s):
{problems}

{guidance}"""


_TAB_INDENT_RE = re.compile(r"^ *\t")           # a tab used for indentation
_MAPPING_COLON_RE = re.compile(r":(?:\s|$)")    # the `key:` of a mapping entry


def _wellformedness_issues(fm_lines: list[str]) -> list[str]:
    """Line-scan checks that the frontmatter block is structurally valid YAML.

    Nothing in frontmatter is mandatory, but a block that exists must be well formed.
    These are the malformations a line scan can name without false positives: a tab in
    indentation (YAML forbids it) and a root line that is not a ``key: value`` mapping
    entry (a bare scalar, or a ``key:value`` missing the space that makes it a mapping).
    Value types, key typos, and full YAML parsing stay the indexer's job.

    ``fm_lines`` is the block between the ``---`` fences; line numbers are file lines
    (``fm_lines[0]`` is file line 2, after the opening ``---``). ``flow_depth`` tracks
    open ``[``/``{`` across lines so a wrapped flow collection reads as a continuation,
    not a stray root line — miscounting only ever suppresses a check, never invents one.
    """
    problems: list[str] = []
    flow_depth = 0
    for idx, line in enumerate(fm_lines):
        line_no = idx + 2

        if _TAB_INDENT_RE.match(line):
            problems.append(f"line {line_no}: tab in indentation — YAML requires spaces")

        stripped = line.strip()
        at_root = flow_depth == 0 and bool(line[:1]) and not line[0].isspace()
        if at_root and stripped and not stripped.startswith("#"):
            is_list_item = stripped == "-" or stripped.startswith("- ")
            if not is_list_item and not _MAPPING_COLON_RE.search(line):
                shown = stripped if len(stripped) <= 40 else stripped[:37] + "..."
                problems.append(
                    f"line {line_no}: `{shown}` is not a `key: value` mapping entry "
                    "(a key needs a colon followed by a space)"
                )

        flow_depth = max(
            0,
            flow_depth
            + line.count("[") + line.count("{")
            - line.count("]") - line.count("}"),
        )
    return problems


def _document_issues(path: Path) -> list[str]:
    """Return one message per issue: frontmatter well-formedness, then malformed or
    unquoted wikilinks (frontmatter, then body)."""
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

    problems.extend(_wellformedness_issues(fm_lines))

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
