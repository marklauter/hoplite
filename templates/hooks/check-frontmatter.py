"""PostToolUse hook: warn when a .md file under docs/ is written without valid Hoplite frontmatter.

Exits 2 with an advisory on stderr so Claude Code surfaces the warning to the agent as
tool-result feedback. The write is not rolled back; the agent is expected to follow up
with an Edit that prepends or corrects the frontmatter block.

Validation is line-scan based — no PyYAML dependency, since the hook runs under
whatever ``python`` is on PATH, not the hoplite project's venv. The indexer at reindex
is the authoritative validator (it parses YAML for real and checks types); this hook
catches the structural issues that are cheap to detect:

- Missing opening ``---`` fence.
- Missing closing ``---`` fence.
- Either of the two mandatory keys (title, summary) absent. Both are bare
  first-class fields; the other bare fields (``created``, ``tags``, ``aliases``)
  and everything in the property bag (any ``document.<key>``) are optional.
  The scanner still flattens nested ``document:`` / ``edge:`` blocks to dotted keys,
  mirroring the indexer.

Wrong types, typos in keys, malformed YAML — left to the indexer.

The canonical guidance shown in the advisory is inlined at build time from
``templates/components/shape/frontmatter.md`` so the hook and the writing skills
teach exactly the same shape.
"""

import json
import sys
from pathlib import Path

WATCHED_TOOLS = {"Write", "Edit", "MultiEdit"}
REQUIRED_FIELDS = {"title", "summary"}
# Top-level keys whose indented mapping expands into dotted keys (the nested form).
NESTED_CLASSES = {"document", "edge"}

_FRONTMATTER_GUIDANCE = """\
{{components/shape/frontmatter.md}}
"""

ADVISORY_TEMPLATE = """\
[frontmatter-check] {path} — {issue}.

Hoplite skips documents with malformed frontmatter at reindex. Canonical shape:

{guidance}
"""


def _frontmatter_issue(path: Path) -> str | None:
    """Return the first structural issue found in the file's frontmatter, or None.

    Catches missing opening fence, missing closing fence, and missing mandatory
    keys. Doesn't validate value types or YAML correctness — that's the indexer's job.
    """
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return None  # can't read; not our concern

    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return "missing opening --- fence"

    closing_idx = next(
        (i for i, line in enumerate(lines[1:], start=1) if line == "---"),
        None,
    )
    if closing_idx is None:
        return "missing closing --- fence"

    keys: set[str] = set()
    nested_class: str | None = None  # set while inside a `document:`/`edge:` block
    for line in lines[1:closing_idx]:
        if not line or line.lstrip().startswith("#"):
            continue
        indented = line[0].isspace()
        if ":" not in line:
            if not indented:
                nested_class = None  # a non-mapping top-level line closes any block
            continue
        key = line.split(":", 1)[0].strip()
        if indented:
            if nested_class is not None:
                keys.add(f"{nested_class}.{key}")
            continue
        # Top-level line. An empty value after `class:` opens a nested block;
        # anything else is a flat key and closes any open block.
        value = line.split(":", 1)[1].strip()
        if not value and key in NESTED_CLASSES:
            nested_class = key
        else:
            nested_class = None
            keys.add(key)

    missing = sorted(REQUIRED_FIELDS - keys)
    if missing:
        return f"missing mandatory fields: {missing}"

    return None


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

    issue = _frontmatter_issue(path)
    if issue is None:
        return 0

    sys.stderr.write(
        ADVISORY_TEMPLATE.format(
            path=file_path,
            issue=issue,
            guidance=_FRONTMATTER_GUIDANCE,
        ),
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
