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
- Any of the four mandatory keys (title, summary, document.tags, document.created) absent.
  ``title`` and ``summary`` are bare first-class fields; ``document.tags`` and
  ``document.created`` carry the ``document.`` class prefix like every other property.
  Both the flat dotted form (``document.tags``) and the nested mapping form
  (``document:`` then an indented ``tags:``) are recognized — the scanner flattens
  nested ``document:`` / ``edge:`` blocks to dotted keys, mirroring the indexer.

Wrong types, typos in keys, malformed YAML — left to the indexer.

The canonical guidance shown in the advisory is inlined at build time from
``templates/components/shape/frontmatter.md`` so the hook and the writing skills
teach exactly the same shape.
"""

import json
import sys
from pathlib import Path

WATCHED_TOOLS = {"Write", "Edit", "MultiEdit"}
REQUIRED_FIELDS = {"title", "summary", "document.tags", "document.created"}
# Top-level keys whose indented mapping expands into dotted keys (the nested form).
NESTED_CLASSES = {"document", "edge"}

_FRONTMATTER_GUIDANCE = """\
## Frontmatter

Every document in the Hoplite corpus, docs/, opens with a YAML frontmatter block. Hoplite indexes documents through this block; a document with missing or malformed frontmatter generates a warning at reindex (in `WriteResult.warnings`) and stays out of the graph until you fix it.

Keys carry a class prefix that declares which side of the property graph they affect: `document.` for node properties, `edge.` for edge stereotypes. `title` and `summary` are the exception — they are first-class, FTS-indexed fields, not properties, so they stay **bare**.

Four mandatory fields:

- `title` (string, bare) — short, human-readable name.
- `summary` (string, bare) — one-line lede. `where` and `relatives` return it so callers can scan candidates without opening the file.
- `document.tags` (list of strings) — tag slugs the document carries. Use kebab-case lowercase (`graph-db`, not `Graph DB` or `graph_db`); the indexer casefolds for lookup, but consistent authoring keeps the corpus tidy. Empty list `document.tags: []` is fine.
- `document.created` (ISO date string, `YYYY-MM-DD`) — creation date. Stays stable across edits.

Optional fields:

- `document.aliases` (list of strings) — alternate paths that resolve to this document. Omit the key when there are no aliases; add it on rename so wikilinks pointing at the old name still resolve.

Beyond the mandatory fields, any `document.<key>` becomes a node property and any `edge.<stereotype>: [paths]` becomes a stereotyped `mentions` edge — Hoplite accepts and stores them. Examples: `document.status: draft`, `document.priority: high`, `document.due: 2026-06-01`, `edge.blocked_by: [docs/notes/foo.md]`. External tools like Obsidian or Dataview read them too. Only `title` and `summary` are bare; everything else is prefixed.

### Dotted or nested — same shape

The class prefix can be written two ways, and Hoplite normalizes both to the same dotted keys before indexing:

- **Dotted** — `document.tags: [...]`. The prefix is part of the key.
- **Nested** — a `document:` mapping with the keys indented under it. Easier to read when a document carries several properties.

A file can mix the two — a nested `document:` block alongside dotted `edge.<stereotype>` lines, for instance. `title` and `summary` stay bare in both forms. The mandatory-field, list-type, and class-prefix rules above apply to the normalized keys regardless of how they were authored, so the corpus uses nested for `document` properties by convention while the rules read in dotted terms.

### Tags classify; properties carry state

A tag answers "what is this document?" — its type, classification, the shape of artifact it represents. Tags are immutable once applied. Removing one erases the document's identity as that kind of artifact and breaks queries that rely on the classification.

A property answers "what state is this document in?" Fields that change as the lifecycle progresses (`document.status` moving from `open` to `closed`, `document.priority` re-triaged). State changes update the value, not the tag set.

State-as-tag is the anti-pattern — a `resolved`, `closed`, or `draft` tag conflates identity and state, because rewriting `document.tags` to track lifecycle churns the identity axis. Use a `document.status` property instead. The reverse also holds: do not invent a `document.type: <kind>` property to duplicate signal the type tag already carries.

Canonical example — dotted form:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
document.tags: [graph-db, note]
document.created: 2026-05-25
document.status: draft
---
```

The same document in nested form (the corpus convention), with an `edge.<stereotype>` line shown dotted alongside the nested `document:` block:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
document:
  tags: [graph-db, note]
  created: 2026-05-25
  status: draft
edge.supports: [docs/notes/sqlite-hybrid.md]
---
```

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
