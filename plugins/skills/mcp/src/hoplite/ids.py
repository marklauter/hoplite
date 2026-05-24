"""Id validation, corpus-relative path resolution, and slug normalization.

Pure, I/O-free module the write flow calls before touching storage.
Owns every id-shape concern in one place; the agent-facing
``hoplite_slugify_text`` tool wraps ``slugify_text`` directly.

Contract
--------
- Ids are path expressions of the form ``<segment>(/<segment>)*.<ext>``.
  Each segment matches ``[a-z0-9-]+``; the final segment is segment
  text, a single dot, and a lowercase-alphanumeric extension.
  Examples: ``foo.md``, ``notes/skill-composition.md``,
  ``journal/2026-05-24-today-was-warm.md``,
  ``mcp/data-model.md``.
- ``validate_id`` raises ``ValueError`` on any id that fails the rule.
- ``resolve`` calls ``validate_id`` first, then joins the id under
  ``<corpus_root>/docs/``. The returned ``Path`` is always inside
  ``<corpus_root>/docs/`` — the regex excludes ``.`` from segments,
  so ``..`` cannot form, and ``/`` is the only segment separator.
  See docs/mcp/behavior.md#slug-and-id-rules.
- ``slugify_text`` normalizes a string to canonical kebab-case:
  lowercase; whitespace → ``-``; non-``[a-z0-9-]`` stripped;
  ``-+`` collapsed; leading and trailing hyphens trimmed.

Edge cases
----------
- ``slugify_text`` returns ``""`` for empty or whitespace-only input.
- Underscores (and every other non-``[a-z0-9-]`` non-whitespace
  character) are stripped without becoming hyphens — only whitespace
  converts to ``-``.
- Multi-dot extensions (``archive.tar.gz``) fail ``validate_id``: the
  extension slot accepts a single dot followed by ``[a-z0-9]+``.

Non-responsibilities
--------------------
- Composing segments into ids — the caller joins ``slugify_text``
  outputs with ``/`` and appends the extension.
- Filesystem existence checks, reads, or writes — those live in the
  write flow.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

__all__ = ["resolve", "slugify_text", "validate_id"]


# No `^`/`$` anchors — `$` matches before a trailing `\n` in default
# mode, which would let `"foo.md\n"` slip through. `fullmatch` ties
# the regex to the whole string without that quirk.
_ID_RE: Final = re.compile(r"([a-z0-9-]+/)*[a-z0-9-]+\.[a-z0-9]+")

_WS_RE: Final = re.compile(r"\s+")
_STRIP_RE: Final = re.compile(r"[^a-z0-9-]+")
_HYPHEN_RUN_RE: Final = re.compile(r"-+")


def slugify_text(s: str) -> str:
    """Lowercase; whitespace → `-`; non-`[a-z0-9-]` stripped; `-+` collapsed; edges trimmed."""
    lowered = s.lower()
    hyphenated = _WS_RE.sub("-", lowered)
    stripped = _STRIP_RE.sub("", hyphenated)
    collapsed = _HYPHEN_RUN_RE.sub("-", stripped)
    return collapsed.strip("-")


def validate_id(id_str: str) -> None:
    """Raise ``ValueError`` if ``id_str`` violates the id shape.

    Grammar: ``<segment>(/<segment>)*.<ext>`` where each segment
    matches ``[a-z0-9-]+`` and ``<ext>`` matches ``[a-z0-9]+``.
    See docs/mcp/behavior.md#slug-and-id-rules.
    """
    if not _ID_RE.fullmatch(id_str):
        raise ValueError(
            f"id does not match `<segment>(/<segment>)*.<ext>` rule: {id_str!r}",
        )


def resolve(id_str: str, corpus_root: Path) -> Path:
    """Resolve an id to its filesystem path under ``<corpus_root>/docs/``.

    Calls ``validate_id`` first; the returned path is always inside
    ``<corpus_root>/docs/`` — see the module docstring for the
    structural argument.
    """
    validate_id(id_str)
    return corpus_root.joinpath("docs", *id_str.split("/"))
