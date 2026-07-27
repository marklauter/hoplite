"""Walk one directory of the corpus and slice the frontmatter out of its documents.

``contents`` is a listing, not a parse. It finds the opening ``---``, finds the closing
``---``, and emits the lines between them verbatim. There is no YAML parser here, so
keys keep their authored order, quoting, and spacing; malformed frontmatter passes
through as written instead of being rejected; and a property whose value is a wikilink
is self-identifying as an edge without this module having to say so.

Directories recurse, documents do not. The report leads with the directory subtree to
full depth — names and per-directory document counts, which cost about 50 tokens for the
whole of ``docs/`` — then the non-markdown files in the requested directory, then the
documents in that directory alone. The caller pays for the directory it asked for rather
than for the corpus, and it sees the skeleton first, so it knows what asking will cost.

The frontmatter standard lives in ``plugins/hoplite-skills/references/frontmatter.md``.
This module does not implement it — it hands the block to the caller untouched. In
particular the spec's derived defaults (slug-derived ``title``, body-excerpt
``summary``) are not applied: a document with no block contributes its path alone.
"""

from __future__ import annotations

import os.path
import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, final

from hoplite_catalog.corpus import Corpus
from hoplite_catalog.errors import CallerError

__all__ = [
    "FENCE",
    "Directory",
    "DirectoryNode",
    "Document",
    "Entry",
    "File",
    "FileNode",
    "ForeignDirectory",
    "ForeignFile",
    "Property",
    "UnlistableDirectory",
    "Unreadable",
    "UnreadableFile",
    "collect",
    "group_properties",
    "markdown_in",
    "other_files",
    "read_entry",
    "resolve_under",
    "slice_frontmatter",
    "subdirectories",
    "walk",
]

FENCE: Final = "---"

# A root-level mapping key: unindented, up to the first colon. Indented lines and `-`
# list items are continuations of the key above them.
_ROOT_KEY_RE: Final = re.compile(r"^([A-Za-z0-9_.\-]+)\s*:")


@final
@dataclass(frozen=True, slots=True)
class Entry:
    """One markdown document: its corpus-relative path and its frontmatter as written.

    ``frontmatter`` is ``None`` when the document has no block, and an empty tuple when
    it has an empty one. Keeping those apart is what lets the listing round-trip: an
    empty block renders back as an empty block, not as a document without one.
    """

    path: str
    frontmatter: tuple[str, ...] | None

    def properties(self) -> tuple[Property, ...]:
        """The frontmatter grouped by root key."""
        return group_properties(self.frontmatter or ())

    def projected(self, keys: frozenset[str] | None) -> Entry:
        """Keep only the properties named in ``keys``. ``None`` keeps everything."""
        if keys is None or self.frontmatter is None:
            return self
        kept = [line for prop in self.properties() if prop.key in keys for line in prop.lines]
        return replace(self, frontmatter=tuple(kept) or None)


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
    """

    path: str
    reason: str

    def properties(self) -> tuple[Property, ...]:
        """No properties: nothing was read. Keeps the reason out of the key vocabulary."""
        return ()

    def projected(self, keys: frozenset[str] | None) -> Unreadable:
        """Unchanged. ``keys`` selects frontmatter, and there is none to select from."""
        return self


@final
@dataclass(frozen=True, slots=True)
class Property:
    """One frontmatter key with the lines it owns — its own line and its continuations."""

    key: str
    lines: tuple[str, ...]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Directory:
    """A directory in the subtree, with the count of documents directly in it.

    ``documents`` is direct, not cumulative: it is the number a caller gets by asking for
    this directory, which is the number they are budgeting against.

    Keyword-only because ``depth`` and ``documents`` are both ``int``: positionally, a
    transposed pair type-checks and renders a plausible wrong tree.
    """

    path: str
    depth: int
    documents: int


@final
@dataclass(frozen=True, slots=True)
class ForeignDirectory:
    """A directory inside the corpus whose target is outside it.

    Reported rather than dropped or walked. Dropping it makes the listing lie about what
    the directory holds; walking it reports foreign files under a corpus path. Naming it
    here means a caller learns the directory is unlistable from the subtree, instead of
    from a refusal on the second call.
    """

    path: str
    depth: int


@final
@dataclass(frozen=True, slots=True)
class UnlistableDirectory:
    """A directory inside the corpus the process could not read.

    Named for the same reason a document that cannot be opened is named: the alternative
    was one unreadable directory failing the whole call, which under the recursive key
    count is the whole corpus for one bad folder. The raw ``OSError`` also carries an
    absolute host path, which nothing else in this module emits.

    The reason is not carried. A directory yields one line in a subtree of them, and
    ``errno`` distinctions — denied, gone since the parent was read, too many links — do
    not change what the caller does next.
    """

    path: str
    depth: int


@final
@dataclass(frozen=True, slots=True)
class File:
    """A non-markdown file directly in the requested directory.

    It cannot carry frontmatter, but hiding it makes the listing lie about what the
    directory holds. It is reported as a path alone, in its own labelled group: a bare path
    in the documents group already means "markdown document with no frontmatter", so an
    unlabelled PDF path would be indistinguishable from one.
    """

    path: str


@final
@dataclass(frozen=True, slots=True)
class ForeignFile:
    """A file inside the corpus whose target is outside it.

    The same answer ``ForeignDirectory`` gives, for the same reason: the name is reported
    and the file is never opened.
    """

    path: str


@final
@dataclass(frozen=True, slots=True)
class UnreadableFile:
    """A file whose target could not be reached at all — a symlink loop, a share that went
    away. Named rather than dropped, and rather than failing the directory for one entry."""

    path: str


type DirectoryNode = Directory | ForeignDirectory | UnlistableDirectory

# What the other-files group lists: a file, one that leaves the corpus, or one that could
# not be reached. Every visible non-markdown entry is exactly one of the three.
type FileNode = File | ForeignFile | UnreadableFile

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


def resolve_under(corpus: Corpus, under: str) -> Path:
    """Normalize ``under`` against the corpus root, rejecting anything outside it.

    Normalization is lexical — ``normpath`` collapses ``.`` and ``..`` without touching
    the filesystem — so a symlinked target keeps the path the corpus links to.
    ``Path.resolve`` would follow the link and make ``docs/specs/frontmatter.md`` come
    back as ``plugins/hoplite-skills/references/frontmatter.md``, which is the same defect
    ``Corpus.path_of`` avoids. A path is a link address here; where the bytes live is not
    this module's business.

    Containment is checked twice, because reporting and reading are different questions.
    The lexical check stops ``..`` traversal. The resolved check stops a symlinked folder
    inside the corpus from pointing out of it: reads follow symlinks, so without it
    ``docs/external -> /somewhere/else`` would be read and reported under ``docs/``, which
    is a listing that lies about what the corpus contains. The two real symlinks in
    ``docs/specs/`` resolve to ``plugins/hoplite-skills/references/``, inside the root, so
    they pass.

    Raises ``CallerError`` when the path escapes the root, names nothing, or names a file
    that is not a ``.md`` document. All three are things the agent could have gotten right,
    and the host turns them into an error result carrying the message — see ``errors``.
    """
    target = Path(os.path.normpath(corpus.root / under))
    if not corpus.contains(target):
        raise CallerError(f"{under!r} is outside the corpus root")
    if not corpus.exists(target):
        raise CallerError(f"{under!r} does not exist")
    if not corpus.contains_target(target):
        raise CallerError(f"{under!r} resolves outside the corpus root")
    if corpus.is_file(target) and target.suffix != ".md":
        # A file named directly is the one path into `collect` that skips `markdown_in`,
        # and with it both the suffix test and the hidden-file skip. Without this, any file
        # in the working directory opening with `---` has that block emitted — a `.env`
        # someone wrote YAML into, a lockfile, a certificate. The listing reports a
        # non-markdown file by path and never opens it, and asking for one by name must not
        # be the exception to that.
        raise CallerError(f"{under!r} is not a markdown document")
    return target


def read_entry(corpus: Corpus, path: Path) -> Entry:
    """Read one document and slice its frontmatter.

    How bytes become text — the byte-order mark, the newline translation — is the adapter's
    decision and lives in ``RealFiles.read_text``. Which path the document is reported
    under is ``Corpus.path_of``.
    """
    lines = corpus.read_text(path).splitlines()
    return Entry(path=corpus.path_of(path), frontmatter=slice_frontmatter(lines))


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _Listing:
    """One directory read, split into the three groups the report shows.

    The split is the structure rather than a claim three docstrings make separately: every
    visible entry lands in exactly one of these, because one pass assigns it.

    Keyword-only because all three fields are ``tuple[Path, ...]``, so positionally a
    transposed pair type-checks and renders a plausible wrong report.
    """

    directories: tuple[Path, ...]
    documents: tuple[Path, ...]
    others: tuple[Path, ...]


def _partition(corpus: Corpus, directory: Path) -> _Listing:
    """Read ``directory`` once and split what is in it. Raises ``OSError`` at the call.

    One ``entries`` call and one ``is_directory`` per entry. The walk used to ask twice per
    directory — once for the document count, once for the children — and the other-files
    group a third time, all to classify the same names against the same tests.

    Hidden entries are skipped, except a hidden ``.md``: a leading dot is the filesystem's
    marker for "not content", which keeps the subtree bounded without a list of names to
    maintain, but a document is addressable by a wikilink whatever it is called. A caller
    naming a hidden directory outright still gets it — the rule is about what a walk
    wanders into, not about what may be asked for.

    A directory named ``notes.md`` is a directory, not a document. Classified the other way
    it would be counted in the subtree and also listed there as a directory, then handed to
    ``read_entry``, where the read fails.

    The test is ``is_directory``, not ``is_file``. A symlink dangling inside the corpus is
    neither, and keying on ``is_file`` would drop it from all three groups — the one outcome
    this module refuses, since a document a caller can see on disk must never go missing.
    It lands in ``documents`` on its suffix, and ``collect`` refuses it out loud.

    The suffix is matched exactly, where ``glob("*.md")`` matched it case-insensitively on
    Windows and case-sensitively everywhere else. One corpus now lists the same documents on
    every platform; a ``README.MD`` moves to the other-files group rather than vanishing.
    """
    entries = tuple((path, corpus.is_directory(path)) for path in corpus.entries(directory))
    return _Listing(
        directories=tuple(
            sorted(path for path, is_dir in entries if is_dir and not path.name.startswith("."))
        ),
        documents=tuple(
            sorted(path for path, is_dir in entries if not is_dir and _is_markdown(path))
        ),
        others=tuple(
            sorted(
                path
                for path, is_dir in entries
                if not is_dir and not _is_markdown(path) and not path.name.startswith(".")
            )
        ),
    )


def _is_markdown(path: Path) -> bool:
    return path.suffix == ".md"


def subdirectories(corpus: Corpus, directory: Path) -> tuple[Path, ...]:
    """The child directories a walk descends into, ordered by path. See ``_partition``."""
    return _partition(corpus, directory).directories


def markdown_in(corpus: Corpus, directory: Path) -> tuple[Path, ...]:
    """The markdown documents directly in ``directory``, ordered by path.

    One definition of "document", used by the listing and by the subtree counts. It comes
    from the same pass that decides the other two groups, so a file cannot fall between
    them — see ``_partition``.
    """
    return _partition(corpus, directory).documents


def other_files(corpus: Corpus, directory: Path) -> tuple[FileNode, ...]:
    """The non-markdown files directly in ``directory``, ordered by path.

    Which entries land here is decided by ``_partition``, in the same pass that decides
    the other two groups. Hidden files are skipped there, the same rule hidden directories
    get: with the corpus root as the default, listing them would put ``.env``,
    ``.gitignore``, and ``.mcp.json`` in a corpus report while ``.git/`` was correctly
    absent from the tree beside it.

    A directory that cannot be read yields nothing here rather than raising. The subtree
    already names it ``cannot be listed``, so the caller learns it from the group built to
    say so, and one unreadable directory does not cost them the report.

    Containment is checked here as it is at every other site that emits a path. A bare
    ``docs/leak.pdf`` asserts the file is in the corpus, and for a link out of it that is
    false — only the name would leak, never the bytes, but the listing would still be
    claiming something untrue. Which of the three records that produces is this module's
    answer; how each one reads is ``rendering``'s.
    """
    try:
        others = _partition(corpus, directory).others
    except OSError:
        return ()
    return tuple(_file_node(corpus, path) for path in others)


def _file_node(corpus: Corpus, path: Path) -> FileNode:
    """Classify one other file: listed, leaving the corpus, or unreachable.

    A resolve that fails — a symlink loop, a share that went away — marks that one file
    rather than raising. This group already refuses to fail a directory for one bad entry,
    and an ``OSError`` escaping here unwound past ``collect``'s per-document handler and cost
    the caller the whole report. What cannot be answered is reported as what it is.
    """
    relative = corpus.path_of(path)
    try:
        contained = corpus.contains_target(path)
    except OSError:
        return UnreadableFile(path=relative)
    return File(path=relative) if contained else ForeignFile(path=relative)


def _unlinked_directories(corpus: Corpus, under: Path) -> frozenset[Path]:
    """The resolved paths of the directories reachable from ``under`` without crossing a link.

    Which of two names for one directory gets descended is decided from this rather than by
    sort order. The link loses to the path that reaches the same directory without following
    one, so the walk descends the path a wikilink addresses.

    Only the descent needs it. Both names are still listed either way — see ``walk``.
    """
    unlinked: set[Path] = set()
    stack = [under]

    while stack:
        directory = stack.pop()
        try:
            resolved = corpus.resolve(directory)
            if resolved in unlinked or not corpus.contains(resolved):
                continue
            unlinked.add(resolved)
            stack.extend(
                child
                for child in _partition(corpus, directory).directories
                if not corpus.is_symlink(child)
            )
        except OSError:
            # A directory that cannot be read reaches nothing, so it contributes nothing.
            # `_walk` is where that gets reported, as an `UnlistableDirectory`.
            continue
    return frozenset(unlinked)


@final
@dataclass(frozen=True, slots=True)
class _Visit:
    """One directory the walk reached: its node, and its documents when it was descended.

    ``documents`` is ``None`` for every directory the walk did not go into — one outside
    the corpus, one it could not read, and one whose target another name already stands
    for. That is exactly the set whose documents must not be read a second time, so the
    distinction the recursive listing needs is the same one the walk already made.

    Carrying the paths rather than a flag is what stops the directory from being read
    twice. ``collect`` used to re-derive them with its own ``markdown_in`` call, which
    partitioned every directory in the subtree a second time and left the second read
    unguarded where the first one was not.
    """

    node: DirectoryNode
    documents: tuple[Path, ...] | None


def _walk(corpus: Corpus, under: Path) -> Iterator[_Visit]:
    """Every directory at or under ``under``, with its node and the documents in it.

    The one traversal both the subtree and the recursive listing read, so they cannot
    disagree about which directories exist, nor about what is in them. ``walk`` keeps the
    nodes; ``collect`` keeps the documents of the directories that were descended, which
    are exactly the ones not already listed under another name.
    """
    unlinked = _unlinked_directories(corpus, under)
    visited: set[Path] = set()
    stack: list[tuple[Path, int]] = [(under, 0)]

    while stack:
        directory, depth = stack.pop()
        path = corpus.path_of(directory)

        try:
            # `resolve` follows links, so it fails the ways a read does — the port says any
            # method may raise `OSError`, and every other site that resolves guards it. A
            # directory that cannot be resolved is unlistable for the same reason a denied
            # one is, so it shares the handler rather than escaping to fail the whole walk.
            resolved = corpus.resolve(directory)
            if not corpus.contains(resolved):
                yield _Visit(ForeignDirectory(path=path, depth=depth), None)
                continue
            listing = _partition(corpus, directory)
        except OSError:
            yield _Visit(UnlistableDirectory(path=path, depth=depth), None)
            continue

        # A link whose target another path reaches without one. The other path is the one
        # to descend, whichever of the two the stack happens to reach first. `under` is
        # exempt: a caller who names the link is asking for what is under it, and no other
        # path in this walk stands for it.
        shadowed = directory != under and corpus.is_symlink(directory) and resolved in unlinked

        node = Directory(path=path, depth=depth, documents=len(listing.documents))
        if shadowed or resolved in visited:
            yield _Visit(node, None)
            continue

        visited.add(resolved)
        yield _Visit(node, listing.documents)
        stack.extend((child, depth + 1) for child in reversed(listing.directories))


def walk(corpus: Corpus, under: Path) -> tuple[DirectoryNode, ...]:
    """The directory subtree at ``under``, to full depth, in pre-order.

    Only directories recurse, and hidden ones are skipped — see ``subdirectories``, which
    is what keeps the subtree bounded when the corpus root is a repository. The walk is at
    ``stat`` level — no file outside the requested directory is opened — so the cost of the
    subtree is the directory count, not the document count.

    Containment is checked at every directory, not only at ``under``. A symlinked
    directory pointing out of the corpus is reported as a ``ForeignDirectory`` and not
    descended into; without the check it would show as walkable and fail only when the
    caller asked for it. A directory the process cannot read is named the same way, as an
    ``UnlistableDirectory``: every directory that exists appears on exactly one line,
    whether or not the walk could go into it.

    A symlinked directory resolving *inside* the corpus is a directory the caller can see
    on disk, so it is emitted like any other, with the count of documents reachable
    through the link. What is governed is the descent, not the emission:
    ``docs/mirror -> docs/glossary`` is listed, and its children are not walked a second
    time under a second name. Dropping the node instead hides a directory that exists, the
    same lie ``ForeignDirectory`` exists to prevent.

    Which of the two names is descended is decided by ``_unlinked_directories``, not by
    which one the traversal reaches first. The link loses whenever another path reaches the
    same directory without crossing one, so the walk descends the path the corpus addresses:
    with ``docs/aaa -> docs/glossary``, the real ``docs/glossary`` is walked and ``docs/aaa``
    is only named. Sort order used to decide it, which put ``docs/glossary/deep`` — and every
    document under it — out of the subtree and out of the recursive listing whenever the link
    sorted first. A link is still descended when no such path exists, since dropping it then
    would hide documents nothing else reaches.

    That is also what stops a link back to an ancestor from looping forever: the ancestor is
    reached without a link, so the loop is entered once, named, and not descended.
    """
    return tuple(visit.node for visit in _walk(corpus, under))


def collect(corpus: Corpus, under: Path, *, recurse: bool = False) -> tuple[Document, ...]:
    """Read the ``.md`` documents in ``under``, ordered by path.

    ``recurse`` is off for the listing, which reports one directory at a time, and on for
    a report over the whole subtree, like the frontmatter key vocabulary. Either way a
    single file as ``under`` collects that file.

    A document that cannot be contributed comes back as ``Unreadable`` rather than raising.
    Two things put it there, and neither is the caller's doing:

    Containment is checked here, at the read, not only where ``under`` was resolved. A
    symlinked *file* inside the corpus is walked like any other, so
    ``docs/leak.md -> ../outside/secret.md`` would otherwise be reported as ``docs/leak.md``
    with foreign frontmatter attached — a listing that lies about what the corpus contains.
    It is named and not opened.

    A read that fails — a link dangling *inside* the corpus, a permission failure, a file
    that is not UTF-8 text — is named the same way. The exception is not allowed to
    propagate: an ``OSError`` message carries an absolute host path and names the document
    by where its bytes were meant to live rather than by the path the corpus addresses it
    with, and either one escaping fails the whole call for one bad file.

    The containment check sits inside the same guard, because following a link to ask where
    it points is itself a read and fails the same ways — a symlink loop, a share that went
    away. Outside it, one such file unwound past this handler and cost the caller the whole
    report, which under ``recurse`` is the whole subtree.

    Under ``recurse`` the documents come from the same walk the subtree is built from, not
    from ``rglob``. ``rglob`` never follows a directory symlink, so the subtree would
    advertise ``docs/mirror/ 3`` while the key count saw none of those three. Reading from
    the walk keeps one answer to "which directories are there, and what is in them", and it
    inherits the walk's two rules for free: hidden directories are skipped, and a directory
    whose target was already listed under another name is not read a second time.

    A recursive read reports one document once, however many paths reach it — see
    ``_distinct``. The one-directory listing does not de-duplicate: two names in one
    directory are two entries a caller can see on disk, and both belong in the group.

    Ordering is by the emitted path string, so two calls over an unchanged corpus return
    identical output — the listing stays diffable and cacheable.
    """
    if corpus.is_file(under):
        paths: tuple[Path, ...] = (under,)
    elif recurse:
        paths = _distinct(
            corpus,
            (path for visit in _walk(corpus, under) for path in visit.documents or ()),
        )
    else:
        # The subtree names an unreadable directory; here it simply holds no documents.
        try:
            paths = markdown_in(corpus, under)
        except OSError:
            paths = ()

    documents: list[Document] = []
    for path in paths:
        relative = corpus.path_of(path)
        try:
            if not corpus.contains_target(path):
                documents.append(
                    Unreadable(path=relative, reason="links to a target outside the corpus")
                )
                continue
            documents.append(read_entry(corpus, path))
        except (OSError, UnicodeDecodeError) as exc:
            documents.append(Unreadable(path=relative, reason=_read_failure(exc)))
    return tuple(sorted(documents, key=lambda document: document.path))


def _distinct(corpus: Corpus, paths: Iterable[Path]) -> tuple[Path, ...]:
    """One path per document, keyed on what each resolves to, ordered by path.

    The walk de-duplicates directories, and that is all it can do: it compares the targets
    of the directories it descends, so two names for one *file* are invisible to it.
    ``docs/specs/frontmatter.md`` is a symlink to
    ``plugins/hoplite-skills/references/frontmatter.md`` and both directories are real, so a
    recursive read reached the same document twice and the key vocabulary counted every
    property on it twice — ``requires: 2`` for one document carrying it.

    The first path in sort order wins, which is the shallower, corpus-addressed one often
    enough to be the useful default and is deterministic in every case. Which name survives
    does not change a key count; that it is one name is the whole point.

    A path that cannot be resolved is kept rather than dropped. Nothing here can tell it
    apart from another, and ``collect`` reports it as ``Unreadable`` a few lines later —
    the alternative is a document going missing over a failure that has its own line in
    the report.
    """
    seen: set[Path] = set()
    kept: list[Path] = []
    for path in sorted(paths):
        try:
            resolved = corpus.resolve(path)
        except OSError:
            kept.append(path)
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        kept.append(path)
    return tuple(kept)


def _read_failure(exc: OSError | UnicodeDecodeError) -> str:
    """Why a read failed, in terms the caller can act on and with no host path in it.

    ``UnicodeDecodeError`` is a ``ValueError``, not an ``OSError``, so catching only the
    latter let one latin-1 file escape ``collect`` and fail the whole call — the outcome
    ``Unreadable`` exists to prevent, and under the recursive key count it took the entire
    subtree. A binary file named as ``under`` reaches the same read, since that path skips
    the ``*.md`` filter.
    """
    if isinstance(exc, UnicodeDecodeError):
        return "cannot be read (not UTF-8 text)"
    return f"cannot be read ({exc.strerror or type(exc).__name__})"


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
