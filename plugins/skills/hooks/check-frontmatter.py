"""PostToolUse hook: warn when a .md file under docs/ is written or edited without Hoplite frontmatter.

Exits 2 with an advisory on stderr so Claude Code surfaces the warning to the agent as
tool-result feedback. The write is not rolled back; the agent is expected to follow up
with an Edit that prepends the frontmatter block.
"""

import json
import sys
from pathlib import Path

WATCHED_TOOLS = {"Write", "Edit", "MultiEdit"}

ADVISORY = """\
[frontmatter-check] {path} is under docs/ but is missing YAML frontmatter.

Hoplite skips notes without frontmatter at reindex. Prepend a block with the five
mandatory fields before continuing:

---
title: Short human-readable title
summary: One-line lede returned by hoplite_match_nodes / hoplite_traverse_nodes.
tags: [tag-one, tag-two]
created: YYYY-MM-DD
aliases: []
---
"""


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

    try:
        with path.open("r", encoding="utf-8-sig") as fh:
            first = fh.readline().rstrip("\r\n")
    except OSError:
        return 0

    if first == "---":
        return 0

    sys.stderr.write(ADVISORY.format(path=file_path))
    return 2


if __name__ == "__main__":
    sys.exit(main())
