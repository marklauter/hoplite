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
- Skips wikilinks inside inline-code spans (``` `[[X]]` ```) and fenced
  code blocks (``` ```...[[X]]...``` ```). Authors mark sample wikilinks
  with backticks; the extractor honors that convention to avoid ghosting
  illustrative syntax.

Edge cases
----------
- Empty body and bodies with no ``[[...]]`` references return ``[]``.
- ``[[]]`` and ``[[   ]]`` produce no entries.

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

# Fenced code block — three or more backticks, anything (including newlines),
# closing run of backticks. Non-greedy to handle adjacent blocks.
_FENCE_RE: Final = re.compile(r"```[\s\S]*?```")

# Inline code span — a run of backticks, content without newlines or backticks,
# closing run. Adequate for our corpus; no nested-backtick gymnastics.
_INLINE_CODE_RE: Final = re.compile(r"`+[^`\n]+?`+")


def _mask_code(body: str) -> str:
    """Replace code-span and code-fence content with spaces.

    Newlines stay so line numbers in the masked body match the original.
    Other characters become spaces so column offsets stay correct and the
    wikilink regex finds nothing inside masked regions.
    """

    def _to_spaces(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    masked = _FENCE_RE.sub(_to_spaces, body)
    masked = _INLINE_CODE_RE.sub(_to_spaces, masked)
    return masked


def extract(body: str) -> list[tuple[str, int, int]]:
    """Return unique ``[[target]]`` references as ``(target, line, column)``."""
    masked = _mask_code(body)
    seen: set[str] = set()
    result: list[tuple[str, int, int]] = []
    for match in _WIKILINK_RE.finditer(masked):
        candidate = match.group(1).strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        start = match.start()
        line = masked.count("\n", 0, start) + 1
        line_start = masked.rfind("\n", 0, start) + 1
        column = start - line_start + 1
        result.append((candidate, line, column))
    return result
