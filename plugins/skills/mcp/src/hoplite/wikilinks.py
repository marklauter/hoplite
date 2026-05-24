"""Wiki-link extraction from a markdown body.

Pure, I/O-free module the write flow calls when deriving `:mentions`
edges (see docs/mcp/behavior.md#wiki-link-resolution-and-broken-link-behavior).
Contract: body-in / list-of-ids-out. No SQLite, no resolution, no
validation — those live downstream.

Contract
--------
- Matches the pattern ``[[id]]`` with the regex ``\\[\\[([^\\]]+)\\]\\]``.
- Returns ids in their order of first appearance.
- Dedupes — repeated occurrences of the same id collapse to one entry.
  The downstream edge table dedupes on ``(type, to)`` as well; doing it
  here keeps callers honest.
- Trims leading and trailing whitespace from each captured id before
  deduplication, so ``[[ foo ]]`` and ``[[foo]]`` resolve to the same
  id. Captures that are empty after trimming are skipped entirely.

Edge cases
----------
- Empty body and bodies with no ``[[...]]`` references both return ``[]``.
- ``[[]]`` and ``[[   ]]`` produce no entries.
- Links inside fenced code blocks are extracted. The indexer parses
  every ``[[...]]`` in a body and emits a ``:mentions`` edge regardless
  of context; a future revision can opt into code-fence skipping, but
  day one is uniform.

Non-responsibilities
--------------------
- ID well-formedness against the slug rule is the validator's job
  (Phase 1 item 2, ``ids.py``).
- Resolving an id to a node is the write flow's job; broken links drop
  silently per docs/mcp/behavior.md.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = ["extract"]


_WIKILINK_RE: Final = re.compile(r"\[\[([^\]]+)\]\]")


def extract(body: str) -> list[str]:
    """Return unique ``[[id]]`` references in document order."""
    seen: set[str] = set()
    result: list[str] = []
    for match in _WIKILINK_RE.finditer(body):
        candidate = match.group(1).strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        result.append(candidate)
    return result
