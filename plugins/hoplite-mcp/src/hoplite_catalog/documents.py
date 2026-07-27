"""The document as the listing reports it, and the frontmatter slice it is built from.

Text in, records out. Nothing here knows a filesystem exists — no ``Corpus``, no ``Files``,
no path that is not already a string the corpus addresses — which is what an
`import-linter` contract now says rather than what the module happened to do. The walk
next door is entirely about a filesystem and shares nothing with this but the records it
hands back.

``contents`` is a listing, not a parse. It finds the opening ``---``, finds the closing
``---``, and emits the lines between them verbatim. There is no YAML parser here, so keys
keep their authored order, quoting, and spacing; malformed frontmatter passes through as
written instead of being rejected; and a property whose value is a wikilink is
self-identifying as an edge without this module having to say so.

The frontmatter standard lives in ``plugins/hoplite-skills/references/frontmatter.md``.
This module does not implement it — it hands the block to the caller untouched. In
particular the spec's derived defaults (slug-derived ``title``, body-excerpt ``summary``)
are not applied: a document with no block contributes its path alone.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Final, final

__all__ = [
    "FENCE",
    "Document",
    "Entry",
    "Property",
    "Unreadable",
    "group_properties",
    "slice_frontmatter",
]

FENCE: Final = "---"

# A root-level mapping key: unindented, up to the first colon. Indented lines and `-`
# list items are continuations of the key above them.
_ROOT_KEY_RE: Final = re.compile(r"^([A-Za-z0-9_.\-]+)\s*:")


@final
@dataclass(frozen=True, slots=True)
class Property:
    """One frontmatter key with the lines it owns — its own line and its continuations."""

    key: str
    lines: tuple[str, ...]


@final
@dataclass(frozen=True, slots=True)
class Entry:
    """One markdown document: its corpus-relative path and its frontmatter as written.

    ``frontmatter`` is ``None`` when the document has no block, and an empty tuple when it
    has an empty one. Keeping those apart is what lets the listing round-trip: an empty
    block renders back as an empty block, not as a document without one.

    ``properties`` is that block grouped by root key, derived once here rather than on
    every ask. It was a method, and a single ``contents`` call asked it four times per
    document — the projection, the two guards on it, the key tally, and the render — so
    each block was scanned four times. It is not a second source of truth: one scanner
    produces it, from ``frontmatter``, and ``replace`` recomputes it.
    """

    path: str
    frontmatter: tuple[str, ...] | None
    # Derived, so it is neither passed in nor compared: two entries with the same block
    # cannot disagree about it, and a test comparing whole records reads the block alone.
    properties: tuple[Property, ...] = field(init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        # `object.__setattr__` is how a frozen dataclass fills a derived field. The
        # computation is pure — no clock, no filesystem — so it is the same answer the
        # method returned, decided once.
        object.__setattr__(self, "properties", group_properties(self.frontmatter or ()))

    def projected(self, keys: frozenset[str] | None) -> Entry:
        """Keep only the properties named in ``keys``. ``None`` keeps everything.

        Projecting to nothing leaves an empty block, not ``None``. The two are the one
        distinction this record is built to carry, and collapsing them made a document
        whose keys all missed indistinguishable from one that never had a block.
        """
        if keys is None or self.frontmatter is None:
            return self
        kept = [line for prop in self.properties if prop.key in keys for line in prop.lines]
        return replace(self, frontmatter=tuple(kept))


@final
@dataclass(frozen=True, slots=True)
class Unreadable:
    """A markdown document the listing could not open, and why.

    It renders like any other document — the path, then lines under it — with the reason
    standing where the frontmatter would be. That is the same answer the listing already
    gives for a PDF: when properties cannot be had, the path is still reported, because a
    document a caller can see on disk must not go missing from the listing.

    Reporting beats refusing. A stray link used to fail the whole call, so one unreadable
    file made its directory unlistable, and through the recursive key count it took the
    whole subtree with it.

    ``reason`` never carries a host path. Where a link points is a filesystem path the
    corpus does not otherwise expose, and it adds nothing a caller can act on.

    No properties: nothing was read, which keeps the reason out of the key vocabulary.
    """

    path: str
    reason: str
    properties: tuple[Property, ...] = field(default=(), init=False, compare=False, repr=False)

    def projected(self, keys: frozenset[str] | None) -> Unreadable:
        """Unchanged. ``keys`` selects frontmatter, and there is none to select from."""
        return self


# What the documents group lists: one that was read, or one that could not be.
type Document = Entry | Unreadable


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


def group_properties(lines: Sequence[str]) -> tuple[Property, ...]:
    """Group frontmatter lines by the root key each belongs to.

    Still a line scan, no parser. A property whose value spans lines — a block list under
    ``disjoint-with:`` — carries its indented continuation lines along, because they belong
    to the last root key seen. A malformed root line that is not ``key: value`` rides with
    the key above it for the same reason. Lines before the first key belong to no property
    and are dropped.

    An unindented ``#`` line is a YAML comment and belongs to no key, so it is dropped
    rather than riding with the key above it. A ``#`` line inside a block scalar is data,
    not a comment, but block-scalar content is indented and so never reaches this test.

    Both the projection and the key vocabulary read the grouping from here. A second
    scanner would be a second answer to "where does this value end", and the block list is
    exactly where a naive one goes wrong: a scanner reading only the ``key:`` line sees an
    empty value.
    """
    groups: list[tuple[str, list[str]]] = []
    for line in lines:
        at_root = bool(line[:1]) and not line[0].isspace()
        if at_root and line.startswith("#"):
            continue
        match = _ROOT_KEY_RE.match(line) if at_root else None
        if match is not None:
            groups.append((match.group(1), [line]))
        elif groups:
            groups[-1][1].append(line)
    return tuple(Property(key=key, lines=tuple(owned)) for key, owned in groups)
