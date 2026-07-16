"""External URL extraction from a markdown body.

Pure, I/O-free module the walker calls when deriving `cites` edges (see
docs/hoplite/hoplite-architecture.md#external-references). Contract: body-in /
(url, line, column) tuples out. No validation beyond the regex match.

Contract
--------
- Matches standard markdown links ``[text](url)`` where ``url`` starts with
  ``http://`` or ``https://``. Wikilinks (``[[...]]``) and autolinks
  (``<https://...>``) are not matched here — wikilinks live in
  ``hoplite.wikilinks``; autolinks are out of scope day one.
- Returns ``(url, line, column)`` tuples in document order. Line and
  column are 1-indexed; column points at the opening ``[``.
- Dedupes per-target — repeated mentions of the same URL collapse to one
  entry, with the line/column reflecting the first occurrence.
- URLs are stored verbatim. No canonicalization, no trailing-slash strip,
  no scheme/host case-folding. Same URL with different fragments produces
  different entries.
- Skips matches inside inline-code spans (``` `[text](url)` ```) and
  fenced code blocks. Authors mark samples with backticks; the extractor
  honors the convention.

Non-responsibilities
--------------------
- URL validation beyond the regex match — the walker registers whatever
  the body offered.
- Edge materialization — the walker turns these tuples into graph state.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = ["extract"]


_URL_RE: Final = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")

_FENCE_RE: Final = re.compile(r"```[\s\S]*?```")
_INLINE_CODE_RE: Final = re.compile(r"`+[^`\n]+?`+")


def _mask_code(body: str) -> str:
    """Replace code-span and code-fence content with spaces.

    Newlines stay so line numbers in the masked body match the original.
    """

    def _to_spaces(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    masked = _FENCE_RE.sub(_to_spaces, body)
    masked = _INLINE_CODE_RE.sub(_to_spaces, masked)
    return masked


def extract(body: str) -> list[tuple[str, int, int]]:
    """Return unique external URLs as ``(url, line, column)``."""
    masked = _mask_code(body)
    seen: set[str] = set()
    result: list[tuple[str, int, int]] = []
    for match in _URL_RE.finditer(masked):
        url = match.group(1).strip()
        if not url or url in seen:
            continue
        seen.add(url)
        start = match.start()
        line = masked.count("\n", 0, start) + 1
        line_start = masked.rfind("\n", 0, start) + 1
        column = start - line_start + 1
        result.append((url, line, column))
    return result
