"""Edge-target grammar for the Hoplite corpus — validation and extraction.

Dependency-free (stdlib only) so the ``check-frontmatter`` hook, which runs under
whatever ``python`` is on PATH rather than the project venv, can import it as a
sibling. The grammar enforced here is the locked spec at
``docs/hoplite/expressing-edges.md``; this module is its executable form.

An edge *target* is the string inside ``[[ ]]`` (inline) or one ``edges:`` entry
(frontmatter). Both share the target grammar; the surfaces differ only in
rendering — inline permits display text (``name|shown``) and an embed marker
(``![[name]]``), a frontmatter edge permits neither.
"""

from __future__ import annotations

import re

__all__ = ["TARGET_RE", "frontmatter_edge_targets", "inline_wikilinks", "validate_target"]

# A name — the character set of a page, a stereotype, and an anchor label. Strict
# ASCII filename characters; the structural delimiters (`/ : # | ! [ ]`) are absent
# by construction, so a name never collides with the grammar.
_NAME = r"[A-Za-z0-9._-]+"
# A namespace — name characters plus the path separator `/`, which is an ordinary
# character here, not a parsed separator: `docs//x` and `docs/` are accepted.
_NS = r"[A-Za-z0-9._/-]+"
# An anchor — a single `#^block`, or one-or-more `#section` headings.
_ANCHOR = rf"(?:\#\^{_NAME}|(?:\#{_NAME})+)"

# The edge-target grammar — the link portion, after any inline `|display` is
# stripped. There are no subpages: `/` lives only inside a namespace, so a
# slash-bearing target without a `:` has no parseable page and is rejected.
# See docs/hoplite/expressing-edges.md.
TARGET_RE = re.compile(
    rf"""
    ^
    (?:
        (?:{_NAME}::)?      # optional  stereotype::
        (?:{_NS}:)?         # optional  namespace:    ('/' is an ordinary char here)
        {_NAME}             # page — one filename, no '/'
        {_ANCHOR}?          # optional  anchor
      |
        {_ANCHOR}           # OR a same-page anchor (#section / #^block)
    )
    $
    """,
    re.VERBOSE,
)


def validate_target(target: str, *, inline: bool = False) -> str | None:
    """Return a diagnostic if ``target`` violates the edge grammar, else ``None``.

    The regex is the gate: a target is valid iff it matches ``TARGET_RE``. The `.md`
    extension is optional — an ordinary segment to the grammar — so there is no
    semantic rule outside it. The branch below runs only when the gate fails, purely
    to name *why*, so the verdict and the explanation can never disagree. ``inline``
    strips the free-form display text (``name|shown``) before gating; a frontmatter
    edge keeps the ``|`` so the gate rejects it.
    """
    t = target.strip().strip("\"'").strip()
    if inline:
        t = t.split("|", 1)[0].strip()  # display text is free-form; gate the link

    if TARGET_RE.match(t):  # gate — the grammar is the whole verdict
        return None

    # Diagnose the gate failure: name the specific mistake, else fall back.
    if not t:
        return "empty edge target"
    if "|" in t:
        return f"`{target}`: display text `|` is inline-only; a frontmatter edge carries no rendering"
    if "!" in t:
        return f"`{target}`: `!` marks the embed site, not the target"
    if t.startswith("::"):
        return f"`{target}`: empty stereotype before `::`"
    if t.count("::") > 1:
        return f"`{target}`: more than one `::` stereotype separator"
    if t.endswith("::"):
        return f"`{target}`: empty target after `::`"
    return f"`{target}`: does not match the edge-target grammar"


def frontmatter_edge_targets(fm_lines: list[str]) -> list[str]:
    """Every ``edges:`` list entry — flow or block — as raw target strings.

    ``fm_lines`` is the frontmatter block (the lines between the ``---`` fences).
    Captures a flow list (``edges: [a, b]``), a block list (``- a`` items), or a
    lone scalar where a list belongs (so the grammar check still flags it).
    """
    targets: list[str] = []
    i, n = 0, len(fm_lines)
    while i < n:
        line = fm_lines[i]
        if line[:1].isspace() or line.split(":", 1)[0].strip() != "edges":
            i += 1
            continue
        value = line.split(":", 1)[1].strip() if ":" in line else ""
        if value.startswith("[") and value.endswith("]"):
            targets.extend(p.strip() for p in value[1:-1].split(",") if p.strip())
            i += 1
            continue
        if value:  # a scalar where a list belongs — capture it for the grammar check
            targets.append(value)
            i += 1
            continue
        # Block list: indented `- item` lines until the block closes.
        j = i + 1
        while j < n:
            item = fm_lines[j]
            if not item.strip():
                j += 1
                continue
            if not item[:1].isspace():
                break
            stripped = item.strip()
            if stripped == "-":
                targets.append("")
            elif stripped.startswith("- "):
                targets.append(stripped[2:].strip())
            else:
                break
            j += 1
        i = j
    return targets


_WIKILINK_RE = re.compile(r"!?\[\[([^\]]+)\]\]")
_FENCE_RE = re.compile(r"```[\s\S]*?```")
_INLINE_CODE_RE = re.compile(r"`+[^`\n]+?`+")


def _mask_code(body: str) -> str:
    """Blank code-span and code-fence content, preserving newlines for line counts."""

    def to_spaces(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return _INLINE_CODE_RE.sub(to_spaces, _FENCE_RE.sub(to_spaces, body))


def inline_wikilinks(body: str) -> list[tuple[str, int]]:
    """Each unique ``[[target]]`` in ``body`` as ``(target, line)``, code spans skipped.

    Backticked sample wikilinks are masked, mirroring the convention the corpus
    uses to show syntax without materializing an edge. Line numbers are 1-indexed.
    """
    masked = _mask_code(body)
    seen: set[str] = set()
    out: list[tuple[str, int]] = []
    for match in _WIKILINK_RE.finditer(masked):
        target = match.group(1).strip()
        if not target or target in seen:
            continue
        seen.add(target)
        line = masked.count("\n", 0, match.start()) + 1
        out.append((target, line))
    return out
