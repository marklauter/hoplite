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
  The scanner flattens a nested ``document:`` block to dotted keys.
- A retired ``edge.<stereotype>`` key. Edges are now the bare ``edges`` list;
  the advisory points the author at the new form.
- A malformed edge target — a frontmatter ``edges`` entry or an in-body
  ``[[wikilink]]``. Both are validated against the shared grammar in the sibling
  ``edge_grammar`` module, the executable form of docs/hoplite/expressing-edges.md.

Wrong types, typos in keys, malformed YAML — left to the indexer.

The canonical guidance shown in the advisory is inlined at build time from
``templates/components/shape/frontmatter.md`` so the hook and the writing skills
teach exactly the same shape.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edge_grammar import (  # noqa: E402  — sibling module; the hook runs by path (see hooks.json)
    frontmatter_edge_targets,
    inline_wikilinks,
    validate_target,
)

WATCHED_TOOLS = {"Write", "Edit", "MultiEdit"}
REQUIRED_FIELDS = {"title", "summary"}
# Top-level keys whose indented mapping expands into dotted keys (the nested form).
# `edge` is retired: edges are the bare `edges` list, not an `edge.<stereotype>` namespace.
NESTED_CLASSES = {"document"}

# Guidance is scoped to the error class: a structural frontmatter fault gets the
# full canonical shape; a malformed edge gets only the edge grammar, since the
# diagnostic already names the specific mistake.
_FRONTMATTER_GUIDANCE = """\
Hoplite skips documents with malformed frontmatter at reindex. Canonical shape:

## Frontmatter

Every document in the Hoplite corpus, docs/, opens with a YAML frontmatter block. Hoplite indexes documents through this block; a document with missing or malformed frontmatter generates a warning at reindex (in `WriteResult.warnings`) and stays out of the graph until you fix it.

Five keys are bare — written flat at the top level, no namespace prefix: `title`, `summary`, `tags`, `created`, and `aliases`. `title` and `summary` are first-class FTS-indexed fields; `tags`, `created`, and `aliases` are recognized fields the indexer maps to their roles (classification, creation date, alternate paths). Every other key is namespaced. A **node property** — a fact stored on the document's own graph node — is written `document.<key>`. An **edge** — a labeled link from this document to another, a typed `declared` edge — is expressed in the bare `edges` list (see [Edges](#edges)).

Two mandatory fields:

- `title` (string, bare) — short, human-readable name.
- `summary` (string, bare) — one-line lede. `where` and `relatives` return it so callers can scan candidates without opening the file.

Optional bare fields:

- `created` (ISO date string, `YYYY-MM-DD`) — creation date. Stays stable across edits when present.
- `tags` (list of strings) — tag slugs the document carries. Use kebab-case lowercase (`graph-db`, not `Graph DB` or `graph_db`); the indexer casefolds for lookup. A document may carry no tags.
- `aliases` (list of strings) — alternate paths that resolve to this document; add on rename so wikilinks pointing at the old name still resolve.

`tags` and `aliases` are lists and follow the omit-when-empty rule: include the key only when it carries at least one element, otherwise leave it out.

Beyond the bare fields, any `document.<key>` becomes a node property, and the bare `edges` list becomes stereotyped `declared` edges — Hoplite accepts and stores them. Examples: `document.status: draft`, `document.priority: high`, `document.due: 2026-06-01`, `edges: [blocked_by::foo]`. External tools like Obsidian or Dataview read them too.

### Namespace spelling and list spelling

A namespaced key carries spelling freedom on two independent axes — the namespace on the left, the list value on the right. The bare fields (`title`, `summary`, `tags`, `created`, `aliases`) take neither; they are always flat.

The **namespace** (`document`) can be written two ways, and Hoplite normalizes both to the same key before indexing:

- **Dotted** — `document.status: draft`. The namespace is part of the key.
- **Nested** — a `document:` mapping with its keys indented underneath. Reads cleaner when a document carries several properties.

YAML treats these as different structures — `document.status` is one key with a dot in its name; the nested form is a mapping under `document`. Hoplite's parser flattens the mapping to the dotted key, so the two are equivalent by Hoplite's rule, not YAML's. Neither is preferred. A file can mix forms — a nested `document:` block alongside a bare `edges` list and dotted `document.<key>` lines.

A **list value** accepts any valid YAML sequence — flow or block are identical here, because YAML itself parses them to the same list:

```yaml
tags: [note, design]
```

```yaml
tags:
  - note
  - design
```

`tags`, `aliases`, and `edges` must be sequences. Any `document.<key>` may be a bare scalar — `document.status: draft` stores as a single-value property, the same as `document.status: [draft]`.

### Tags are set membership; properties are named axes

A tag is unnamed set membership — the document carries `note` or it doesn't. You filter with boolean tag expressions (`note & !draft`). Tags answer "what is this document?": its type, classification, the shape of artifact it represents. They are immutable once applied; removing one erases the document's identity as that kind of artifact and breaks queries that rely on the classification.

A property is a named axis holding a value — `severity` is the axis, `high` is the value. The value can be lifecycle state (`document.status` moving from `open` to `closed`), an ordered grade (`document.severity: high|med|low`), or a descriptive category (`document.issue-type: doc|code`). State is one kind of value a property carries, not what defines it; what defines a property is the named axis.

The deciding question between the two: do you need the axis name? If you will ask "what is the severity?" or want exactly one value on a known dimension, use a property. If you only need "is it tagged `doc`?", use a tag.

Two anti-patterns fall out. State-as-tag — a `resolved`, `closed`, or `draft` tag forces lifecycle churn through the identity axis; use a `document.status` property instead. Axis-duplication — a `document.type: <kind>` property duplicates signal a type tag already carries; let the tag answer it.

### Edges

An edge is a labeled link from this document to another. Express edges in the bare `edges` list; each entry is one wikilink target string, optionally led by a `stereotype::` prefix that types the link:

```yaml
edges: [refines::circle, contrast::square]
```

- **Target.** A page name — strict ASCII filename characters `[A-Za-z0-9._-]`, so the `.md` extension is just dots in a name. Optionally namespace-qualify it: `lib/shapes:circle`, a colon dividing the directory path from the page. There are no subpages — `/` lives only in a namespace, so a directory path always needs the colon (`docs/hoplite:term`, never `docs/hoplite/term`). A section is `#`, a block is `#^`, and an open loop is the ghost namespace `ghost:<slug>`.
- **Stereotype.** Lead the target with `stereotype::` to type the edge — `refines::circle`. A bare target with no `::` is an untyped edge. The `::` is the stereotype separator; the single `:` stays the namespace separator, so the two never collide: `refines::lib/shapes:circle`.
- **No rendering.** Display text (`|`) and embedding (`!`) are inline-only; a frontmatter edge is data, never rendered.
- **Equivalence.** `edges: [refines::circle]` and an in-body `[[refines::circle]]` express the same edge — identical target string, structured versus inline.

The full grammar — every target form, the inline wikilink surface, and worked examples — is the locked spec at `docs/hoplite/expressing-edges.md`.

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

The same document with a nested `document:` block and an `edges` list — bare fields stay flat above it:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
tags: [graph-db, note]
created: 2026-05-25
document:
  status: draft
  priority: high
edges: [supports::sqlite-hybrid]
---
```

"""

_EDGE_GUIDANCE = """\
An edge target is a page name `[A-Za-z0-9._-]`, optionally namespace-qualified with a \
colon (`docs/hoplite:term`) and led by a `stereotype::` prefix. There are no subpages, so a \
directory path needs the colon — `docs/hoplite/term` is invalid. Display text (`|`) and \
embedding (`!`) are inline-only. The full grammar is the locked spec at docs/hoplite/expressing-edges.md.
"""

ADVISORY_TEMPLATE = """\
[frontmatter-check] {path} — {issue}.

{guidance}
"""


def _document_issue(path: Path) -> tuple[str, str] | None:
    """Return ``(kind, issue)`` for the first/aggregated problem, or ``None``.

    ``kind`` selects the advisory's guidance: ``"frontmatter"`` for a structural
    fault (fence, mandatory key), ``"edge"`` for a retired key or malformed edge
    target. Order: opening fence, closing fence, mandatory keys, retired `edge.`
    key — each returns immediately — then every malformed edge target, frontmatter
    `edges` entries and in-body `[[wikilink]]`s alike, collected into one advisory.
    Value types and YAML correctness are the indexer's job.
    """
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return None  # can't read; not our concern

    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return ("frontmatter", "missing opening --- fence")

    closing_idx = next(
        (i for i, line in enumerate(lines[1:], start=1) if line == "---"),
        None,
    )
    if closing_idx is None:
        return ("frontmatter", "missing closing --- fence")

    fm_lines = lines[1:closing_idx]

    keys: set[str] = set()
    nested_class: str | None = None  # set while inside a `document:` block
    for line in fm_lines:
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
        return ("frontmatter", f"missing mandatory fields: {missing}")

    retired = sorted(k for k in keys if k == "edge" or k.startswith("edge."))
    if retired:
        return (
            "edge",
            f"retired edge key(s) {retired}: express edges as one bare `edges` list, "
            "each entry a `stereotype::target` string — e.g. `edges: [blocked_by::foo]`",
        )

    problems: list[str] = []
    for target in frontmatter_edge_targets(fm_lines):
        msg = validate_target(target)
        if msg is not None:
            problems.append(f"edges: {msg}")

    offset = closing_idx + 1  # body line 1 == file line closing_idx + 2
    body = "\n".join(lines[closing_idx + 1 :])
    for target, body_line in inline_wikilinks(body):
        msg = validate_target(target, inline=True)
        if msg is not None:
            problems.append(f"line {body_line + offset}: {msg}")

    if problems:
        return ("edge", "malformed edge target(s):\n" + "\n".join(f"  - {p}" for p in problems))

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

    result = _document_issue(path)
    if result is None:
        return 0

    kind, issue = result
    guidance = _EDGE_GUIDANCE if kind == "edge" else _FRONTMATTER_GUIDANCE
    advisory = ADVISORY_TEMPLATE.format(
        path=file_path,
        issue=issue,
        guidance=guidance,
    )
    # Write UTF-8 bytes directly: the guidance carries em-dashes and other
    # non-ASCII, and a Windows interpreter's text-mode stderr defaults to a
    # locale codec (cp1252), which Claude Code then misreads as UTF-8 (mojibake).
    try:
        sys.stderr.buffer.write(advisory.encode("utf-8"))
        sys.stderr.buffer.flush()
    except (AttributeError, ValueError):
        sys.stderr.write(advisory)
    return 2


if __name__ == "__main__":
    sys.exit(main())
