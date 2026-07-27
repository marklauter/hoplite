"""Walk one directory of the corpus and read the documents in it.

Everything here is about a filesystem. What a document's frontmatter says is
``documents``' business, and this module only hands it the lines it read — the two share
the records and nothing else, which is what the layering contract now asserts rather than
leaves to convention.

Directories recurse, documents do not. The report leads with the directory subtree to
full depth — names and per-directory document counts, which cost about 50 tokens for the
whole of ``docs/`` — then the non-markdown files in the requested directory, then the
documents in that directory alone. The caller pays for the directory it asked for rather
than for the corpus, and it sees the skeleton first, so it knows what asking will cost.

Every directory is read once per call. Two passes need the same listing — the link
resolution that decides which of two names for one directory gets descended, then the walk
itself — and a memo holds what each returned for as long as the call lasts. See
``_Listings``.
"""

from __future__ import annotations

import os.path
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import final

from hoplite_catalog.corpus import Corpus
from hoplite_catalog.documents import Document, Entry, Unreadable, slice_frontmatter
from hoplite_catalog.refusals import (
    Missing,
    NotMarkdown,
    OutsideRoot,
    ResolvesOutside,
    Unaddressable,
)

__all__ = [
    "Directory",
    "DirectoryNode",
    "File",
    "FileNode",
    "ForeignDirectory",
    "ForeignFile",
    "Report",
    "UnlistableDirectory",
    "UnreadableFile",
    "collect",
    "markdown_in",
    "other_files",
    "read_entry",
    "resolve_under",
    "subdirectories",
    "survey",
    "walk",
]


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


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Report:
    """What one ``contents`` call found: the subtree, the other files, the documents.

    The three come from one ``survey`` rather than three calls, which is what lets them
    share a single read of each directory — and what stops them disagreeing about which
    directories exist.

    Keyword-only: three tuple fields, so positionally a transposed pair type-checks and
    renders a plausible wrong report.
    """

    tree: tuple[DirectoryNode, ...]
    others: tuple[FileNode, ...]
    documents: tuple[Document, ...]


def resolve_under(corpus: Corpus, under: str) -> Path | Unaddressable:
    """Normalize ``under`` against the corpus root, or say why it cannot be addressed.

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

    A path that escapes the root, names nothing, or names a file that is not a ``.md``
    document comes back as a value rather than raising: all three are things the agent
    could have gotten right, so they are outcomes of this function and not failures of it.
    The host turns each into an error result carrying the reason — see ``refusals``.
    """
    target = Path(os.path.normpath(corpus.root / under))
    if not corpus.contains(target):
        return OutsideRoot(under)
    if not corpus.exists(target):
        return Missing(under)
    if not corpus.contains_target(target):
        return ResolvesOutside(under)
    if corpus.is_file(target) and target.suffix != ".md":
        return NotMarkdown(under)
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


@final
class _Listings:
    """The directories one call has already read, so none is read twice.

    Two passes need the same listings. ``_unlinked_directories`` partitions every directory
    in the subtree to decide which of two names for one of them gets descended, and then
    ``_walk`` partitions all of them again; the report's other-files and documents groups
    made a third and fourth read of the directory asked for. On this repository's ``docs/``
    — eight directories — one ``contents`` call made 18 ``entries`` calls and 366
    ``is_directory`` calls. It is now one ``entries`` call per directory, which is what the
    single-pass ``_partition`` was for before the second pass gave it back.

    The memo is the one mutable thing in the walk, and it is scoped to a call by
    construction: each public entry point makes one, hands it down, and drops it on the way
    out, so a listing can never outlive the call that read it and no caller can hold one.
    Keyed on the path as it was reached, never on what it resolves to, because
    ``docs/mirror`` and ``docs/glossary`` are two directories to a report that lists both.

    A failed read is not remembered. It is rare, it is one line in the report either way,
    and caching it would mean deciding how long a permission error stays true.

    Not a frozen dataclass, unlike everything else here: it is a memo and it mutates, and
    dressing it as a record would say the opposite of what it is.
    """

    __slots__ = ("_read", "corpus")

    def __init__(self, corpus: Corpus) -> None:
        self.corpus = corpus
        self._read: dict[Path, _Listing] = {}

    def of(self, directory: Path) -> _Listing:
        """``directory`` split into its three groups, read at most once. Raises ``OSError``."""
        listing = self._read.get(directory)
        if listing is None:
            listing = _partition(self.corpus, directory)
            self._read[directory] = listing
        return listing


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


def _unlinked_directories(listings: _Listings, under: Path) -> frozenset[Path]:
    """The resolved paths of the directories reachable from ``under`` without crossing a link.

    Which of two names for one directory gets descended is decided from this rather than by
    sort order. The link loses to the path that reaches the same directory without following
    one, so the walk descends the path a wikilink addresses.

    Only the descent needs it. Both names are still listed either way — see ``walk``.
    """
    corpus = listings.corpus
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
                for child in listings.of(directory).directories
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


def _walk(listings: _Listings, under: Path) -> Iterator[_Visit]:
    """Every directory at or under ``under``, with its node and the documents in it.

    The one traversal both the subtree and the recursive listing read, so they cannot
    disagree about which directories exist, nor about what is in them. ``walk`` keeps the
    nodes; ``collect`` keeps the documents of the directories that were descended, which
    are exactly the ones not already listed under another name.
    """
    corpus = listings.corpus
    unlinked = _unlinked_directories(listings, under)
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
            listing = listings.of(directory)
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
    return tuple(visit.node for visit in _walk(_Listings(corpus), under))


def survey(corpus: Corpus, under: Path) -> Report:
    """The whole of one ``contents`` call: the subtree, the other files, the documents.

    One memo across the three, so the directory asked for is read once for all of them and
    every directory below it once for the subtree. Calling ``walk``, ``other_files``, and
    ``collect`` in turn reads the same directory three times and answers the same.

    A directory that cannot be read has no groups to report; the subtree names it
    ``cannot be listed``, which is where the caller learns why the rest is empty.
    """
    listings = _Listings(corpus)
    tree = tuple(visit.node for visit in _walk(listings, under))
    try:
        listing = listings.of(under)
    except OSError:
        return Report(tree=tree, others=(), documents=())
    return Report(
        tree=tree,
        others=tuple(_file_node(corpus, path) for path in listing.others),
        documents=_read_all(corpus, listing.documents),
    )


def collect(corpus: Corpus, under: Path, *, recurse: bool = False) -> tuple[Document, ...]:
    """Read the ``.md`` documents in ``under``, ordered by path.

    ``recurse`` is off for the listing, which reports one directory at a time, and on for
    a report over the whole subtree, like the frontmatter key vocabulary. Either way a
    single file as ``under`` collects that file.

    Under ``recurse`` the documents come from the same walk the subtree is built from, not
    from ``rglob``. ``rglob`` never follows a directory symlink, so the subtree would
    advertise ``docs/mirror/ 3`` while the key count saw none of those three. Reading from
    the walk keeps one answer to "which directories are there, and what is in them", and it
    inherits the walk's two rules for free: hidden directories are skipped, and a directory
    whose target was already listed under another name is not read a second time.

    A recursive read reports one document once, however many paths reach it — see
    ``_distinct``. The one-directory listing does not de-duplicate: two names in one
    directory are two entries a caller can see on disk, and both belong in the group.
    """
    listings = _Listings(corpus)
    if corpus.is_file(under):
        paths: tuple[Path, ...] = (under,)
    elif recurse:
        paths = _distinct(
            corpus,
            (path for visit in _walk(listings, under) for path in visit.documents or ()),
        )
    else:
        # The subtree names an unreadable directory; here it simply holds no documents.
        try:
            paths = listings.of(under).documents
        except OSError:
            paths = ()
    return _read_all(corpus, paths)


def _read_all(corpus: Corpus, paths: Sequence[Path]) -> tuple[Document, ...]:
    """Read every path, ordered by the path the report emits.

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

    Ordering is by the emitted path string, so two calls over an unchanged corpus return
    identical output — the listing stays diffable and cacheable.
    """
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
    apart from another, and ``_read_all`` reports it as ``Unreadable`` a few lines later —
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
    latter let one latin-1 file escape the read loop and fail the whole call — the outcome
    ``Unreadable`` exists to prevent, and under the recursive key count it took the entire
    subtree. A binary file named as ``under`` reaches the same read, since that path skips
    the ``*.md`` filter.
    """
    if isinstance(exc, UnicodeDecodeError):
        return "cannot be read (not UTF-8 text)"
    return f"cannot be read ({exc.strerror or type(exc).__name__})"
