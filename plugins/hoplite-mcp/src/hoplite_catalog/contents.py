"""Slice the frontmatter out of every markdown document under a subtree.

``contents`` is a listing, not a parse. It finds the opening ``---``, finds the closing
``---``, and emits the lines between them verbatim. There is no YAML parser here, so
keys keep their authored order, quoting, and spacing; malformed frontmatter passes
through as written instead of being rejected; and a property whose value is a wikilink
is self-identifying as an edge without this module having to say so.

The frontmatter standard lives in ``plugins/hoplite-skills/references/frontmatter.md``.
This module does not implement it — it hands the block to the caller untouched. In
particular the spec's derived defaults (slug-derived ``title``, body-excerpt
``summary``) are not applied: a document with no block contributes its path alone.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

__all__ = [
    "FENCE",
    "Entry",
    "collect",
    "read_entry",
    "render",
    "resolve_under",
    "slice_frontmatter",
]

FENCE: Final = "---"


@dataclass(frozen=True, slots=True)
class Entry:
    """One markdown document: its corpus-relative path and its frontmatter as written.

    ``frontmatter`` is ``None`` when the document has no block, and an empty tuple when
    it has an empty one. Keeping those apart is what lets the listing round-trip: an
    empty block renders back as an empty block, not as a document without one.
    """

    path: str
    frontmatter: tuple[str, ...] | None


def slice_frontmatter(lines: Sequence[str]) -> tuple[str, ...] | None:
    """Return the lines between the fences, or ``None`` when the document has no block.

    The opening fence must be the first line; the closing fence is the next line that is
    a fence on its own. Both are matched after stripping surrounding whitespace, so a
    trailing space — invisible in an editor — doesn't cost a document its whole block.

    An unterminated block reads as no block. Emitting to the end of the file instead
    would pull the entire document body into the listing, which is the one outcome a
    listing must never produce. The ``check-frontmatter`` hook already flags the
    unclosed fence at write time.
    """
    if not lines or lines[0].strip() != FENCE:
        return None
    closing = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == FENCE),
        None,
    )
    return None if closing is None else tuple(lines[1:closing])


def resolve_under(root: Path, under: str) -> Path:
    """Resolve ``under`` against the corpus root, rejecting anything outside it.

    Raises ``ValueError`` when the path escapes the root or names nothing. Both are
    caller errors the agent could have prevented, and per the error model in
    ``docs/specs/hoplite-tool-api.md`` those throw rather than riding back as an empty
    result — a silent empty listing reads as "the folder is empty", not "you typo'd".
    """
    resolved_root = root.resolve()
    target = (resolved_root / under).resolve()
    if target != resolved_root and resolved_root not in target.parents:
        raise ValueError(f"{under!r} is outside the corpus root")
    if not target.exists():
        raise ValueError(f"{under!r} does not exist")
    return target


def read_entry(root: Path, path: Path) -> Entry:
    """Read one document and slice its frontmatter. The I/O edge of this module.

    ``utf-8-sig`` strips a byte-order mark, which would otherwise sit in front of the
    opening fence and hide it. Text mode translates CRLF, so a file Obsidian wrote on
    Windows slices the same as one written on Linux.
    """
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    return Entry(
        path=path.resolve().relative_to(root.resolve()).as_posix(),
        frontmatter=slice_frontmatter(lines),
    )


def collect(root: Path, under: Path) -> tuple[Entry, ...]:
    """Read every ``.md`` document at or under ``under``, ordered by path.

    Ordering is by the emitted path string, so two calls over an unchanged corpus return
    identical output — the listing stays diffable and cacheable.
    """
    paths = [under] if under.is_file() else sorted(under.rglob("*.md"))
    return tuple(sorted((read_entry(root, path) for path in paths), key=lambda e: e.path))


def render(entries: Iterable[Entry]) -> str:
    """Render the listing: a path line per document, then its block between fences.

    A document with no frontmatter is its path line alone. Blocks are reproduced line for
    line, so what comes back is what is on disk.
    """
    blocks = [
        entry.path
        if entry.frontmatter is None
        else "\n".join([entry.path, FENCE, *entry.frontmatter, FENCE])
        for entry in entries
    ]
    return "\n\n".join(blocks)
