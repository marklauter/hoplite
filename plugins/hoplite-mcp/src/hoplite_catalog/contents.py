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
from typing import Final, assert_never, final

__all__ = [
    "FENCE",
    "Directory",
    "DirectoryNode",
    "Document",
    "Entry",
    "ForeignDirectory",
    "Property",
    "UnlistableDirectory",
    "Unreadable",
    "collect",
    "corpus_path",
    "group_properties",
    "markdown_in",
    "other_files",
    "read_entry",
    "render",
    "render_report",
    "resolve_under",
    "slice_frontmatter",
    "subdirectories",
    "walk",
]

FENCE: Final = "---"

# A root-level mapping key: unindented, up to the first colon. Indented lines and `-`
# list items are continuations of the key above them.
_ROOT_KEY_RE: Final = re.compile(r"^([A-Za-z0-9_.\-]+)\s*:")

# Headings carry a `#` so they cannot be mistaken for content. A blank line separates the
# groups and also separates two documents inside the last one, so the heading is the only
# boundary marker — and an unprefixed word on its own line above a path reads as a path.
#
# A frontmatter key can never collide: `_ROOT_KEY_RE` admits alphanumerics, underscore,
# dot, and dash. A path can, but only at the corpus root. Paths are corpus-relative, so one
# inside a folder leads with that folder; a file at the root leads with its own name, and
# `#hash.md` there emits a line starting with `#`. Left as is: the collision needs a
# root-level file named for a heading, and prefixing every root path with `./` to close it
# would put noise on every line of every listing to buy nothing else.
_TREE_HEADING: Final = "# directories (documents directly in each)"
_OTHER_HEADING: Final = "# other files"
_DOCUMENT_HEADING: Final = "# documents"
_NONE: Final = "none"
# One wording, used by every group that can report something it will not follow.
_OUTSIDE: Final = "links outside the corpus"
_UNLISTABLE: Final = "cannot be listed"


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

    def block(self) -> str:
        """The path, then one line per property.

        Emitted through ``properties`` rather than from the raw block, so a document
        renders the same whether or not ``keys`` was supplied — one scanner decides what a
        property owns, and the projection cannot keep a line the plain listing drops. What
        that costs is anything owned by no key: a comment, and a stray line above the first
        key. Neither is addressable, and a comment is the one that matters, since the report
        marks its groups with a leading ``#`` and a comment emitted verbatim forges one.

        Blank lines inside a block are dropped, so a stray one cannot split a document
        into two records once ``render`` joins blocks with a blank line.
        """
        lines = (line for prop in self.properties() for line in prop.lines if line.strip())
        return "\n".join([self.path, *lines])


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

    def block(self) -> str:
        return f"{self.path}\n{self.reason}"


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


type DirectoryNode = Directory | ForeignDirectory | UnlistableDirectory

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


def subdirectories(directory: Path) -> tuple[Path, ...]:
    """The child directories a walk descends into, ordered by path.

    Hidden directories are skipped. A leading dot is the filesystem's own marker for
    "not content", and it is what keeps the subtree bounded without a list of names to
    maintain: ``.git`` and ``.venv`` are each thousands of directories, and neither holds
    anything a corpus addresses. A caller naming a hidden directory outright still gets
    it — the rule is about what a walk wanders into, not about what may be asked for.
    """
    return tuple(
        sorted(
            path for path in directory.iterdir() if path.is_dir() and not path.name.startswith(".")
        )
    )


def markdown_in(directory: Path) -> tuple[Path, ...]:
    """The markdown documents directly in ``directory``, ordered by path.

    One definition of "document", used by the listing, by the subtree counts, and — by
    subtraction — by ``other_files``. Sharing it is what keeps a file from falling
    between the two groups: anything this does not match is reported as an other file.

    Directories are excluded, because a directory can be named ``notes.md`` and Obsidian
    corpora do produce them. Left in, one would be counted as a document in the subtree
    while also appearing there as a directory, and handed to ``read_entry``, where the
    read fails and takes the whole call with it.

    The test is ``not is_dir()``, not ``is_file()``. A symlink dangling inside the corpus
    is neither a file nor a directory, and ``is_file()`` would drop it silently — the one
    outcome this module refuses, since a document a caller can see on disk must never go
    missing from the listing. It stays in, and ``collect`` refuses it out loud.
    """
    return tuple(sorted(path for path in directory.glob("*.md") if not path.is_dir()))


def other_files(root: Path, directory: Path) -> tuple[str, ...]:
    """The non-markdown files directly in ``directory``, as corpus paths, ordered.

    They cannot carry frontmatter, but hiding them makes the listing lie about what the
    directory holds. They are reported as paths alone, in their own labelled group: a
    bare path already means "markdown document with no frontmatter", so an unlabelled
    PDF path would be indistinguishable from one.

    ``not is_dir()`` matches ``markdown_in``, so the two partition everything the report
    shows: a visible entry is a subdirectory, a document, or an other file, never both and
    never neither. ``is_file()`` would leave a dangling link in none of the three.

    Hidden files are skipped, the same rule ``subdirectories`` applies to hidden
    directories. A leading dot is the filesystem's marker for "not content", and it does
    not stop meaning that because the entry is a file: with the corpus root as the default,
    listing it would put ``.env``, ``.gitignore``, and ``.mcp.json`` in a corpus report
    while ``.git/`` was correctly absent from the tree beside it. A hidden ``.md`` file is
    left alone — it is a document, and a wikilink can address it.

    A directory that cannot be read yields nothing here rather than raising. The subtree
    already names it ``cannot be listed``, so the caller learns it from the group built to
    say so, and one unreadable directory does not cost them the report.

    Containment is checked here as it is at every other site that emits a path. A bare
    ``docs/leak.pdf`` asserts the file is in the corpus, and for a link out of it that is
    false — only the name would leak, never the bytes, but the listing would still be
    claiming something untrue. It is marked with the same wording a foreign directory
    carries, on the same line, because this group is one line per file.
    """
    resolved_root = root.resolve()
    try:
        documents = set(markdown_in(directory))
        others = sorted(
            path
            for path in directory.iterdir()
            if not path.is_dir() and not path.name.startswith(".") and path not in documents
        )
    except OSError:
        return ()
    return tuple(
        corpus_path(root, path)
        if _contains(resolved_root, path.resolve())
        else f"{corpus_path(root, path)} {_OUTSIDE}"
        for path in others
    )


def _walk(root: Path, under: Path) -> Iterator[tuple[Path, DirectoryNode, bool]]:
    """Every directory at or under ``under``, with its node and whether it was descended.

    The one traversal both the subtree and the recursive listing read, so they cannot
    disagree about which directories exist. ``walk`` keeps the nodes; ``collect`` keeps the
    paths it descended into, which are exactly the directories whose documents have not
    already been listed under another name.
    """
    resolved_root = root.resolve()
    visited: set[Path] = set()
    stack: list[tuple[Path, int]] = [(under, 0)]

    while stack:
        directory, depth = stack.pop()
        path = corpus_path(root, directory)
        resolved = directory.resolve()

        if not _contains(resolved_root, resolved):
            yield directory, ForeignDirectory(path=path, depth=depth), False
            continue

        # Both calls sit inside the try because both fail lazily: `iterdir` and `glob`
        # raise mid-iteration, not at the call, so the failure surfaces inside the
        # comprehension that consumes them.
        try:
            documents = len(markdown_in(directory))
            children = subdirectories(directory)
        except OSError:
            yield directory, UnlistableDirectory(path=path, depth=depth), False
            continue

        node = Directory(path=path, depth=depth, documents=documents)
        if resolved in visited:
            yield directory, node, False
            continue

        visited.add(resolved)
        yield directory, node, True
        stack.extend((child, depth + 1) for child in reversed(children))


def walk(root: Path, under: Path) -> tuple[DirectoryNode, ...]:
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
    through the link. What the visited set governs is the descent, not the emission:
    ``docs/mirror -> docs/glossary`` is listed, and its children are not walked a second
    time under a second name. Dropping the node instead — which is what testing the set
    before emitting does — hides a directory that exists, the same lie ``ForeignDirectory``
    exists to prevent. It is also what stops a link back to an ancestor from looping
    forever: the loop is entered once, named, and not descended.
    """
    return tuple(node for _, node, _ in _walk(root, under))


def collect(root: Path, under: Path, *, recurse: bool = False) -> tuple[Document, ...]:
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

    Under ``recurse`` the directories come from the same walk the subtree is built from,
    not from ``rglob``. ``rglob`` never follows a directory symlink, so the subtree would
    advertise ``docs/mirror/ 3`` while the key count saw none of those three. Reading from
    the walk keeps one answer to "which directories are there", and it inherits the walk's
    two rules for free: hidden directories are skipped, and a directory whose target was
    already listed under another name is not read a second time.

    Ordering is by the emitted path string, so two calls over an unchanged corpus return
    identical output — the listing stays diffable and cacheable.
    """
    resolved_root = root.resolve()
    if under.is_file():
        paths: tuple[Path, ...] = (under,)
    elif recurse:
        paths = tuple(
            sorted(
                path
                for directory, _, descended in _walk(root, under)
                if descended
                for path in markdown_in(directory)
            )
        )
    else:
        # The subtree names an unreadable directory; here it simply holds no documents.
        try:
            paths = markdown_in(under)
        except OSError:
            paths = ()

    documents: list[Document] = []
    for path in paths:
        relative = corpus_path(root, path)
        if not _contains(resolved_root, path.resolve()):
            documents.append(
                Unreadable(path=relative, reason="links to a target outside the corpus")
            )
            continue
        try:
            documents.append(read_entry(root, path))
        except (OSError, UnicodeDecodeError) as exc:
            documents.append(Unreadable(path=relative, reason=_read_failure(exc)))
    return tuple(sorted(documents, key=lambda document: document.path))


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


def render(documents: Iterable[Document]) -> str:
    """Render the listing: a path per document, then its lines under it.

    A blank line separates documents. No ``---`` fences — they delimit a block for a
    parser, and only an agent reads this.
    """
    return "\n\n".join(document.block() for document in documents)


def _render_node(node: DirectoryNode) -> str:
    """One subtree line: indented name, then its document count.

    Names only below the root, because names are what make the subtree cheap enough to
    lead with. The root line carries the full corpus path, so the caller can read a child
    path off the indentation without a round trip.
    """
    indent = "  " * node.depth
    name = node.path.rsplit("/", 1)[-1] if node.depth else (node.path or ".")
    match node:
        case Directory(documents=documents):
            return f"{indent}{name}/ {documents}"
        case ForeignDirectory():
            return f"{indent}{name}/ {_OUTSIDE}"
        case UnlistableDirectory():
            return f"{indent}{name}/ {_UNLISTABLE}"
        case _:
            # A third kind of node added without a line here fails the type check rather
            # than rendering as nothing.
            assert_never(node)


def render_report(
    tree: Iterable[DirectoryNode], others: Iterable[str], documents: Iterable[Document]
) -> str:
    """Render the three parts of the report, each under its own heading.

    Every heading is emitted, with ``none`` under an empty one. A directory holding no
    documents is a real answer — ``docs/`` holds none in either corpus that exists today —
    so the shape of the report stays the same whether or not a part has anything in it.
    """
    sections = (
        "\n".join([_TREE_HEADING, *(_render_node(node) for node in tree)]),
        "\n".join([_OTHER_HEADING, *(tuple(others) or (_NONE,))]),
        "\n".join([_DOCUMENT_HEADING, render(documents) or _NONE]),
    )
    return "\n\n".join(sections)
