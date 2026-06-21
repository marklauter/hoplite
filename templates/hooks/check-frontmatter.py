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

{{components/shape/frontmatter.md}}
"""

_EDGE_GUIDANCE = """\
An edge target is a name or `namespace:page` — no `.md` extension — optionally led \
by a `stereotype::` prefix. Display text (`|`) and embedding (`!`) are inline-only. \
The full grammar and examples are the locked spec at docs/hoplite/expressing-edges.md.
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
