"""Edge-target grammar for the Hoplite corpus — validation and extraction.

Stdlib only, so the ``check-frontmatter`` hook (which runs under whatever ``python``
is on PATH, not the project venv) can import it as a sibling. This module is the
executable form of the locked spec at ``docs/hoplite/expressing-edges.md``.

A *target* is the document a wikilink points to: a slug, an optional folder-path
prefix, and an optional ``#section`` / ``#^block`` anchor. There are no colons — the
folder path is the namespace. In frontmatter an *edge* is a property whose value is a
wikilink, and the key is the stereotype; the special keys (title, summary, aliases,
tags) are read by meaning, never as edges.
"""

from __future__ import annotations

import re

__all__ = [
    "TARGET_RE",
    "frontmatter_wikilink_targets",
    "inline_edges",
    "inline_wikilinks",
    "validate_target",
]

# Character classes — see docs/hoplite/expressing-edges.md ### Grammar.
_SEG = r"[A-Za-z0-9._-]+"      # one path segment (slug or folder)
_HEADING = r"[^#^|\[\]]+"      # a section label — heading text, spaces allowed
_BLOCKID = r"[A-Za-z0-9-]+"    # an Obsidian block id
_ANCHOR = rf"(?:\#\^{_BLOCKID}|(?:\#{_HEADING})+)"
_PATH = rf"{_SEG}(?:/{_SEG})*"

# A target is a page path (optionally anchored) or a same-page anchor. No colons:
# `/` is the only separator, so the folder path is the whole namespace mechanism.
TARGET_RE = re.compile(
    rf"""
    ^
    (?:
        {_PATH}        # page path — the folder is the namespace
        {_ANCHOR}?     # optional anchor
      |
        {_ANCHOR}      # OR a same-page anchor (#section / #^block)
    )
    $
    """,
    re.VERBOSE,
)

# Keys Hoplite reads by their defined meaning, never as edges — a wikilink in one is
# not an edge target. See docs/hoplite/frontmatter.md.
SPECIAL_KEYS = frozenset({"title", "summary", "aliases", "tags"})


def validate_target(target: str, *, inline: bool = False) -> str | None:
    """Return a diagnostic if ``target`` violates the edge grammar, else ``None``.

    ``TARGET_RE`` is the gate: a target is valid iff it matches. The branch below runs
    only when the gate fails, to name why, so the verdict and the explanation can never
    disagree. ``inline`` strips the free-form ``|display`` text before gating (it is
    body-only); a frontmatter target keeps the ``|`` so the gate rejects it.
    """
    t = target.strip().strip("\"'").strip()
    if inline:
        t = t.split("|", 1)[0].strip()  # display text is body-only; gate the link

    if TARGET_RE.match(t):
        return None

    if not t:
        return "empty edge target"
    if "::" in t:
        return (
            f"`{target}`: a stereotype is the property key, not part of the target — "
            'write `cites: "[[target]]"`, not `[[cites::target]]`'
        )
    if ":" in t:
        return (
            f"`{target}`: targets have no colons — the folder path is the namespace "
            "(`docs/hoplite/term`, not `docs/hoplite:term`)"
        )
    if "|" in t:
        return f"`{target}`: display text `|` is body-only; a frontmatter edge is data"
    if "!" in t:
        return f"`{target}`: embedding `!` is body-only"
    return f"`{target}`: does not match the edge-target grammar (docs/hoplite/expressing-edges.md)"


_BRACKET_RE = re.compile(r"!?\[\[([^\]]+)\]\]")


def _value_wikilinks(text: str) -> list[tuple[str, bool]]:
    """Each ``[[target]]`` in a frontmatter value as ``(target, quoted)``.

    ``quoted`` is True when the link is wrapped in matching quotes — the form Obsidian
    indexes, and the only valid YAML for a ``[[ ]]`` value.
    """
    out: list[tuple[str, bool]] = []
    for m in _BRACKET_RE.finditer(text):
        target = m.group(1).strip()
        before = text[m.start() - 1] if m.start() > 0 else ""
        after = text[m.end()] if m.end() < len(text) else ""
        quoted = before == after and before in ("'", '"')
        out.append((target, quoted))
    return out


def frontmatter_wikilink_targets(fm_lines: list[str]) -> list[tuple[str, bool, int]]:
    """Every wikilink in a non-special frontmatter property value.

    ``fm_lines`` is the block between the ``---`` fences. Returns ``(target, quoted,
    line_index)`` per ``[[wikilink]]``, ``line_index`` 0-based within ``fm_lines``. A
    wikilink under a special key (title, summary, aliases, tags) is skipped — those are
    read by meaning, not as edges. Handles scalar, flow-list, and block-list values.
    """
    out: list[tuple[str, bool, int]] = []
    key_is_edge = False  # inside a non-special top-level key's value (and its block list)
    for idx, line in enumerate(fm_lines):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace():  # continuation or block-list item under the current key
            if key_is_edge:
                out.extend((t, q, idx) for t, q in _value_wikilinks(line))
            continue
        if ":" not in line:
            key_is_edge = False
            continue
        key, _, value = line.partition(":")
        key_is_edge = key.strip() not in SPECIAL_KEYS
        if key_is_edge:
            out.extend((t, q, idx) for t, q in _value_wikilinks(value))
    return out


_FENCE_RE = re.compile(r"```[\s\S]*?```")
_INLINE_CODE_RE = re.compile(r"`+[^`\n]+?`+")


def _mask_code(body: str) -> str:
    """Blank code-span and code-fence content, preserving newlines for line counts."""

    def to_spaces(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return _INLINE_CODE_RE.sub(to_spaces, _FENCE_RE.sub(to_spaces, body))


def inline_wikilinks(body: str) -> list[tuple[str, int]]:
    """Each unique ``[[target]]`` in ``body`` as ``(target, line)``, code masked.

    Backticked sample wikilinks and fenced blocks are masked, mirroring the corpus
    convention for showing syntax without materializing an edge. A leading ``!`` embed
    marker is not part of the target. Line numbers are 1-based.
    """
    masked = _mask_code(body)
    seen: set[str] = set()
    out: list[tuple[str, int]] = []
    for m in _BRACKET_RE.finditer(masked):
        target = m.group(1).strip()
        if not target or target in seen:
            continue
        seen.add(target)
        line = masked.count("\n", 0, m.start()) + 1
        out.append((target, line))
    return out


# Inline predicate forms, beside a wikilink — see expressing-edges.md ### Inline predicates.
_TRAILING_STEREOTYPE_RE = re.compile(
    r"[^\S\n]*(?:<!--\s*([A-Za-z0-9._-]+)\s*-->|%%\s*([A-Za-z0-9._-]+)\s*%%)"
)
_LEADING_FIELD_RE = re.compile(r"\[\s*([A-Za-z0-9._-]+)\s*::\s*$")


def inline_edges(body: str) -> list[tuple[str, str | None, int]]:
    """Each in-body ``[[target]]`` as ``(target, stereotype | None, line)``.

    A bare ``[[target]]`` is untyped (``stereotype`` is None). Three forms attach a
    stereotype beside the link, all read here; the HTML comment is the emit default::

        [[target]]<!--refines-->    HTML comment
        [[target]]%%refines%%        Obsidian comment
        [refines:: [[target]]]       Dataview inline field

    A comment must sit on the same line as the link — only horizontal whitespace may
    separate them; the bracket-delimited Dataview field may span lines. Code spans and
    fences are masked. Occurrences are returned in document order (no dedup; the indexer
    collapses per edge). Line numbers are 1-based.
    """
    masked = _mask_code(body)
    out: list[tuple[str, str | None, int]] = []
    for m in _BRACKET_RE.finditer(masked):
        target = m.group(1).strip()
        if not target:
            continue
        stereotype: str | None = None
        trail = _TRAILING_STEREOTYPE_RE.match(masked, m.end())
        if trail:
            stereotype = trail.group(1) or trail.group(2)
        else:
            lead = _LEADING_FIELD_RE.search(masked, 0, m.start())
            if lead and masked[m.end() :].lstrip().startswith("]"):
                stereotype = lead.group(1)
        line = masked.count("\n", 0, m.start()) + 1
        out.append((target, stereotype, line))
    return out
