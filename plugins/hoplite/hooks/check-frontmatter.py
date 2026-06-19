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
## Frontmatter

Every document in the Hoplite corpus, docs/, opens with a YAML frontmatter block. Hoplite indexes documents through this block; a document with missing or malformed frontmatter generates a warning at reindex (in `WriteResult.warnings`) and stays out of the graph until you fix it.

Five keys are bare — written flat at the top level, no namespace prefix: `title`, `summary`, `tags`, `created`, and `aliases`. `title` and `summary` are first-class FTS-indexed fields; `tags`, `created`, and `aliases` are recognized fields the indexer maps to their roles (classification, creation date, alternate paths). Every other key is namespaced. A **node property** — a fact stored on the document's own graph node — is written `document.<key>`. An **edge stereotype** — a labeled link from this document to another, a typed `declared` edge — is written `edge.<stereotype>`.

Two mandatory fields:

- `title` (string, bare) — short, human-readable name.
- `summary` (string, bare) — one-line lede. `where` and `relatives` return it so callers can scan candidates without opening the file.

Optional bare fields:

- `created` (ISO date string, `YYYY-MM-DD`) — creation date. Stays stable across edits when present.
- `tags` (list of strings) — tag slugs the document carries. Use kebab-case lowercase (`graph-db`, not `Graph DB` or `graph_db`); the indexer casefolds for lookup. A document may carry no tags.
- `aliases` (list of strings) — alternate paths that resolve to this document; add on rename so wikilinks pointing at the old name still resolve.

`tags` and `aliases` are lists and follow the omit-when-empty rule: include the key only when it carries at least one element, otherwise leave it out.

Beyond the bare fields, any `document.<key>` becomes a node property and any `edge.<stereotype>: [paths]` becomes a stereotyped `declared` edge — Hoplite accepts and stores them. Examples: `document.status: draft`, `document.priority: high`, `document.due: 2026-06-01`, `edge.blocked_by: [docs/notes/foo.md]`. External tools like Obsidian or Dataview read them too.

### Namespace spelling and list spelling

A namespaced key carries spelling freedom on two independent axes — the namespace on the left, the list value on the right. The bare fields (`title`, `summary`, `tags`, `created`, `aliases`) take neither; they are always flat.

The **namespace** (`document`, `edge`) can be written two ways, and Hoplite normalizes both to the same key before indexing:

- **Dotted** — `document.status: draft`. The namespace is part of the key.
- **Nested** — a `document:` mapping with its keys indented underneath. Reads cleaner when a document carries several properties.

YAML treats these as different structures — `document.status` is one key with a dot in its name; the nested form is a mapping under `document`. Hoplite's parser flattens the mapping to the dotted key, so the two are equivalent by Hoplite's rule, not YAML's. Neither is preferred. A file can mix them — a nested `document:` block alongside dotted `edge.<stereotype>` lines.

A **list value** accepts any valid YAML sequence — flow or block are identical here, because YAML itself parses them to the same list:

```yaml
tags: [note, design]
```

```yaml
tags:
  - note
  - design
```

`tags`, `aliases`, and every `edge.<stereotype>` must be sequences. Any `document.<key>` may be a bare scalar — `document.status: draft` stores as a single-value property, the same as `document.status: [draft]`.

### Tags are set membership; properties are named axes

A tag is unnamed set membership — the document carries `note` or it doesn't. You filter with boolean tag expressions (`note & !draft`). Tags answer "what is this document?": its type, classification, the shape of artifact it represents. They are immutable once applied; removing one erases the document's identity as that kind of artifact and breaks queries that rely on the classification.

A property is a named axis holding a value — `severity` is the axis, `high` is the value. The value can be lifecycle state (`document.status` moving from `open` to `closed`), an ordered grade (`document.severity: high|med|low`), or a descriptive category (`document.issue-type: doc|code`). State is one kind of value a property carries, not what defines it; what defines a property is the named axis.

The deciding question between the two: do you need the axis name? If you will ask "what is the severity?" or want exactly one value on a known dimension, use a property. If you only need "is it tagged `doc`?", use a tag.

Two anti-patterns fall out. State-as-tag — a `resolved`, `closed`, or `draft` tag forces lifecycle churn through the identity axis; use a `document.status` property instead. Axis-duplication — a `document.type: <kind>` property duplicates signal a type tag already carries; let the tag answer it.

Canonical example:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
tags: [graph-db, note]
created: 2026-05-25
document.status: draft
---
```

The same document with a nested `document:` block and an `edge.<stereotype>` line — bare fields stay flat above it:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
tags: [graph-db, note]
created: 2026-05-25
document:
  status: draft
  priority: high
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
