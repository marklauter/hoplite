"""Wiki-link extraction from a markdown body.

Pure, I/O-free module the walker calls when deriving `mentions` edges (see
docs/hoplite/architecture.md#wikilinks-and-ghost-documents). Contract: body-in / (target, line, column) tuples out.
No resolution, no validation — those live downstream in the walker.

Contract
--------
- Matches the pattern ``[[target]]`` with the regex ``\\[\\[([^\\]]+)\\]\\]``.
- Returns ``(target, line, column)`` tuples in document order. Line and
  column are 1-indexed; column points at the opening ``[[``.
- Dedupes — repeated occurrences of the same target collapse to one entry,
  with the line/column reflecting the first occurrence. Edge tables key on
  ``(src, dst, kind)`` per docs/hoplite/architecture.md#edges, so per-target uniqueness
  matches the consumer's expectation.
- Trims leading and trailing whitespace from each captured target before
  deduplication, so ``[[ foo ]]`` and ``[[foo]]`` resolve to the same
  target. Captures empty after trimming are skipped entirely.

Edge cases
----------
- Empty body and bodies with no ``[[...]]`` references return ``[]``.
- ``[[]]`` and ``[[   ]]`` produce no entries.
- Links inside fenced code blocks are extracted. The walker emits a
  ``mentions`` edge regardless of fence context; day-one behavior is
  uniform across the body.

Non-responsibilities
--------------------
- Resolving a target to a Document (real or ghost) is the walker's job.
- Validation of target text (path shape, alias lookup) lives in the walker.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = ["extract"]


_WIKILINK_RE: Final = re.compile(r"\[\[([^\]]+)\]\]")


def extract(body: str) -> list[tuple[str, int, int]]:
    """Return unique ``[[target]]`` references as ``(target, line, column)``."""
    seen: set[str] = set()
    result: list[tuple[str, int, int]] = []
    for match in _WIKILINK_RE.finditer(body):
        candidate = match.group(1).strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        start = match.start()
        line = body.count("\n", 0, start) + 1
        line_start = body.rfind("\n", 0, start) + 1
        column = start - line_start + 1
        result.append((candidate, line, column))
    return result
