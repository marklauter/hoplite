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
- Any of the four mandatory keys (title, summary, tags, created) absent.

Wrong types, typos in keys, malformed YAML — left to the indexer.

The canonical example shown in the advisory is read at hook-invocation time from
``components/shape/frontmatter.md`` (the same fragment the writing skills inject),
so the advisory and the skill teach exactly the same shape.
"""

import json
import sys
from pathlib import Path

WATCHED_TOOLS = {"Write", "Edit", "MultiEdit"}
REQUIRED_FIELDS = {"title", "summary", "tags", "created"}

# Hook lives at <plugin_root>/hooks/check-frontmatter.py;
# component lives at <plugin_root>/components/shape/frontmatter.md.
_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_COMPONENT_PATH = _PLUGIN_ROOT / "components" / "shape" / "frontmatter.md"

ADVISORY_TEMPLATE = """\
[frontmatter-check] {path} — {issue}.

Hoplite skips documents with malformed frontmatter at reindex. The canonical shape
(from components/shape/frontmatter.md):

{example}
"""

_FALLBACK_EXAMPLE = (
    "(canonical shape not found — see components/shape/frontmatter.md)"
)


def _canonical_example() -> str:
    """Extract the first ```yaml ... ``` fence from the frontmatter component."""
    try:
        text = _COMPONENT_PATH.read_text(encoding="utf-8")
    except OSError:
        return _FALLBACK_EXAMPLE

    in_fence = False
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not in_fence and stripped == "```yaml":
            in_fence = True
            continue
        if in_fence:
            if stripped == "```":
                return "\n".join(lines) if lines else _FALLBACK_EXAMPLE
            lines.append(line)
    return _FALLBACK_EXAMPLE


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

    # Collect top-level keys (no leading whitespace, has a colon, not a comment).
    keys: set[str] = set()
    for line in lines[1:closing_idx]:
        if not line or line[0].isspace():
            continue
        if line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        keys.add(line.split(":", 1)[0].strip())

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
            example=_canonical_example(),
        ),
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
