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

import os.path
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

__all__ = [
    "FENCE",
    "Entry",
    "collect",
    "corpus_path",
    "is_excluded",
    "normalize_exclusions",
    "project",
    "read_entry",
    "render",
    "resolve_exclusions",
    "resolve_under",
    "slice_frontmatter",
]

FENCE: Final = "---"

# A root-level mapping key: unindented, up to the first colon. Indented lines and `-`
# list items are continuations of the key above them.
_ROOT_KEY_RE: Final = re.compile(r"^([A-Za-z0-9_.\-]+)\s*:")


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
    """Normalize ``under`` against the corpus root, rejecting anything outside it.

    Normalization is lexical — ``normpath`` collapses ``.`` and ``..`` without touching
    the filesystem — so a symlinked target keeps the path the corpus links to.
    ``Path.resolve`` would follow the link and make ``docs/specs/frontmatter.md`` come
    back as ``plugins/hoplite-skills/references/frontmatter.md``, which is the same defect
    ``read_entry`` avoids. A path is a link address here; where the bytes live is not this
    module's business.

    Containment is checked twice, because reporting and reading are different questions.
    The lexical check stops ``..`` traversal. The resolved check stops a symlinked folder
    inside the corpus from pointing out of it: reads follow symlinks, so without it
    ``docs/external -> /somewhere/else`` would be read and reported under ``docs/``, which
    is a listing that lies about what the corpus contains. The two real symlinks in
    ``docs/specs/`` resolve to ``plugins/hoplite-skills/references/``, inside the root, so
    they pass.

    Raises ``ValueError`` when the path escapes the root or names nothing. Both are
    caller errors the agent could have prevented, and per the error model in
    ``docs/specs/hoplite-tool-api.md`` those throw rather than riding back as an empty
    result — a silent empty listing reads as "the folder is empty", not "you typo'd".
    """
    resolved_root = root.resolve()
    target = Path(os.path.normpath(resolved_root / under))
    if not _contains(resolved_root, target):
        raise ValueError(f"{under!r} is outside the corpus root")
    if not target.exists():
        raise ValueError(f"{under!r} does not exist")
    if not _contains(resolved_root, target.resolve()):
        raise ValueError(f"{under!r} resolves outside the corpus root")
    return target


def _contains(root: Path, path: Path) -> bool:
    """True when ``path`` is ``root`` or sits beneath it."""
    return path == root or root in path.parents


def normalize_exclusions(folders: Iterable[str]) -> frozenset[str]:
    """Clean ``exclude`` entries into the form ``is_excluded`` matches.

    A trailing slash, a leading slash, a ``./`` prefix, or Windows separators would each
    otherwise match nothing and silently return the full listing the caller was trimming.
    Entries that clean to nothing are dropped, so ``exclude: [""]`` excludes nothing
    rather than everything.
    """
    cleaned = (
        os.path.normpath(folder.replace("\\", "/")).replace("\\", "/").strip("/")
        for folder in folders
    )
    return frozenset(folder for folder in cleaned if folder not in ("", "."))


def resolve_exclusions(root: Path, paths: Iterable[str]) -> frozenset[str]:
    """Normalize ``exclude`` entries and require each to name something real in the corpus.

    Normalization alone cannot catch a wrong address. ``exclude: ["journal"]`` — the path
    written relative to ``under`` instead of the root — and ``exclude: ["docs/journals"]``
    both clean up fine, match nothing, and return the full listing the caller was
    trimming. That is the silent-empty failure ``resolve_under`` refuses for ``under``.

    Validation is against the corpus, not against what the listing yields: an entry naming
    a real path outside the current ``under`` is a no-op, not a mistake, and a caller
    passing one standing exclusion list across several calls should not be punished for it.

    A single document is as excludable as a folder. Restricting this to folders would make
    the only remedy for one bad link — a symlink out of the corpus at ``docs/leak.md`` —
    excluding ``docs`` entirely, which costs the whole listing to route around one file.

    Containment is checked lexically here and the entry is never resolved, because the
    document a caller most needs to exclude is precisely the one whose target is elsewhere.
    Existence uses ``lexists``, which sees the link itself: ``Path.exists`` follows it, so a
    dangling link would be refused here while ``collect`` refuses the listing and names that
    same entry as the remedy — the tool would have no callable form at all.
    """
    resolved_root = root.resolve()
    excluded = normalize_exclusions(paths)
    for path in sorted(excluded):
        target = Path(os.path.normpath(resolved_root / path))
        if not _contains(resolved_root, target) or not os.path.lexists(target):
            raise ValueError(f"{path!r} is not a path in the corpus")
    return excluded


def read_entry(root: Path, path: Path) -> Entry:
    """Read one document and slice its frontmatter. The I/O edge of this module.

    ``utf-8-sig`` strips a byte-order mark, which would otherwise sit in front of the
    opening fence and hide it. Text mode translates CRLF, so a file Obsidian wrote on
    Windows slices the same as one written on Linux.

    The emitted path is where the corpus links to the document, not where the bytes live.
    ``path`` is deliberately not resolved: ``docs/specs/frontmatter.md`` is a symlink into
    ``plugins/hoplite-skills/references/``, and resolving it would report a path no
    wikilink in the corpus uses. Only ``root`` is resolved, to give ``relative_to`` a
    normalized base.
    """
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    return Entry(path=corpus_path(root, path), frontmatter=slice_frontmatter(lines))


def corpus_path(root: Path, path: Path) -> str:
    """The document's path as the corpus addresses it — root-relative, forward slashes."""
    return path.absolute().relative_to(root.resolve()).as_posix()


def is_excluded(path: str, exclude: frozenset[str]) -> bool:
    """True when a corpus path sits at or under one of the excluded folders.

    Matching is on whole path segments, so excluding ``docs/journal`` leaves
    ``docs/journals-are-not-notes.md`` alone. A plain string prefix would not.
    """
    return any(path == folder or path.startswith(f"{folder}/") for folder in exclude)


def collect(root: Path, under: Path, exclude: frozenset[str] = frozenset()) -> tuple[Entry, ...]:
    """Read every ``.md`` document at or under ``under``, ordered by path.

    Excluded folders are skipped before the read, so their bytes are never touched.

    Every document is checked for containment here, at the read, not only where ``under``
    was resolved. A symlinked *file* inside the corpus is walked and read like any other,
    so ``docs/leak.md -> ../outside/secret.md`` would otherwise be reported as
    ``docs/leak.md`` with foreign frontmatter attached — a listing that lies about what the
    corpus contains. Such a link raises rather than being dropped: silently omitting a
    document a caller can see on disk is the other way to lie. Exclusions are applied
    first, so naming that one document in ``exclude`` is enough to get past it.

    A document that cannot be read — a link dangling *inside* the corpus, a permission
    failure — is refused the same way, since the read is where the corpus path is still in
    hand. Letting the ``OSError`` propagate would report neither: its message carries an
    absolute host path and names no remedy.

    Every refusal here names the corpus path and nothing else, plus an ``exclude`` entry the
    tool accepts. Where a link points is a host filesystem path the corpus does not
    otherwise expose, and it adds nothing a caller can act on.

    A symlinked *folder* never reaches this loop, because ``rglob`` does not recurse into
    one. It is therefore absent from the listing rather than refused.

    Ordering is by the emitted path string, so two calls over an unchanged corpus return
    identical output — the listing stays diffable and cacheable.
    """
    resolved_root = root.resolve()
    paths = [under] if under.is_file() else sorted(under.rglob("*.md"))

    entries: list[Entry] = []
    for path in paths:
        relative = corpus_path(root, path)
        if is_excluded(relative, exclude):
            continue
        if not _contains(resolved_root, path.resolve()):
            raise ValueError(
                f"{relative} is a link to a target outside the corpus root; "
                f"remove the link, or pass exclude: [{relative!r}] to skip it"
            )
        try:
            entries.append(read_entry(root, path))
        except OSError as exc:
            # A dangling link pointing *inside* the corpus passes the check above and then
            # fails here. Translated rather than propagated for two reasons: the OSError
            # string carries an absolute host path, and it names no remedy, though
            # excluding the document is one. Every refusal names a remedy the tool accepts.
            raise ValueError(
                f"{relative} cannot be read ({exc.strerror or type(exc).__name__}); "
                f"fix it, or pass exclude: [{relative!r}] to skip it"
            ) from exc
    return tuple(sorted(entries, key=lambda entry: entry.path))


def project(entry: Entry, keys: frozenset[str] | None) -> Entry:
    """Keep only the frontmatter properties named in ``keys``.

    ``None`` keeps everything, which is the default: ``summary`` is what makes a listing
    worth reading, so a caller has to ask to lose it. An empty set keeps nothing, leaving
    the path alone. Projecting a document down to no properties drops its fences too — the
    output is a listing at that point, not a copy of the file, so an empty block would be
    noise.

    Still a line scan, no parser. A property whose value spans lines — a block list under
    ``disjoint-with:`` — carries its indented continuation lines along, because they belong
    to the last root key seen. A malformed root line that is not ``key: value`` rides with
    the key above it for the same reason.
    """
    if keys is None or entry.frontmatter is None:
        return entry

    kept: list[str] = []
    current: str | None = None
    for line in entry.frontmatter:
        at_root = bool(line[:1]) and not line[0].isspace()
        match = _ROOT_KEY_RE.match(line) if at_root else None
        if match is not None:
            current = match.group(1)
        if current in keys:
            kept.append(line)
    return replace(entry, frontmatter=tuple(kept) or None)


def render(entries: Iterable[Entry]) -> str:
    """Render the listing: a path per document, then its properties, one per line.

    A blank line separates documents. No ``---`` fences — they delimit a block for a
    parser, and only an agent reads this. Blank lines inside a block are dropped, so a
    stray one cannot split a document into two records.
    """
    blocks = [
        "\n".join([entry.path, *(line for line in entry.frontmatter or () if line.strip())])
        for entry in entries
    ]
    return "\n\n".join(blocks)
