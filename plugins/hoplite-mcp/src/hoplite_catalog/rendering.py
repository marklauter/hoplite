"""Turn what the walk found into the text an agent reads.

Only an agent reads this, so the shape is chosen for scanning rather than for parsing:
groups under ``#`` headings, one line per thing, no ``---`` fences. Nothing here touches a
filesystem, and nothing in ``contents`` or ``vocabulary`` decides wording — the walk
returns records that say *what* it found, and every string a caller sees is written here.

That split is what stops the two from drifting. The walk used to return the other-files
group already rendered, so it owned ``links outside the corpus`` while the subtree lines
owned the same phrase one function away, and a change to either could miss the other.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final, assert_never

from hoplite_catalog.contents import (
    Directory,
    DirectoryNode,
    Document,
    Entry,
    File,
    FileNode,
    ForeignDirectory,
    ForeignFile,
    UnlistableDirectory,
    Unreadable,
    UnreadableFile,
)
from hoplite_catalog.vocabulary import KeyUse

__all__ = ["render", "render_report", "render_vocabulary"]

# Headings carry a `#` so they cannot be mistaken for content. A blank line separates the
# groups and also separates two documents inside the last one, so the heading is the only
# boundary marker — and an unprefixed word on its own line above a path reads as a path.
#
# A frontmatter key can never collide: the key scanner admits alphanumerics, underscore,
# dot, and dash. A path can, but only at the corpus root. Paths are corpus-relative, so one
# inside a folder leads with that folder; a file at the root leads with its own name, and
# `#hash.md` there emits a line starting with `#`. Left as is: the collision needs a
# root-level file named for a heading, and prefixing every root path with `./` to close it
# would put noise on every line of every listing to buy nothing else.
_TREE_HEADING: Final = "# directories (documents directly in each)"
_OTHER_HEADING: Final = "# other files"
_DOCUMENT_HEADING: Final = "# documents"
_NONE: Final = "none"
# One wording, used by every group that can report something the walk would not follow.
_OUTSIDE: Final = "links outside the corpus"
_UNLISTABLE: Final = "cannot be listed"
_UNREADABLE: Final = "cannot be read"


def _render_document(document: Document) -> str:
    """One document: the path, then the lines under it.

    An ``Entry`` renders through ``properties`` rather than from the raw block, so it looks
    the same whether or not ``keys`` was supplied — one scanner decides what a property
    owns, and a projection cannot keep a line the plain listing drops. What that costs is
    anything owned by no key: a comment, and a stray line above the first key. Neither is
    addressable, and the comment is the one that matters, since the report marks its groups
    with a leading ``#`` and a comment emitted verbatim forges one.

    Blank lines inside a block are dropped, so a stray one cannot split a document into two
    records once ``render`` joins blocks with a blank line.

    An ``Unreadable`` puts its reason where the frontmatter would be. That is the same
    answer a PDF already gets: when properties cannot be had, the path is still reported,
    because a document a caller can see on disk must not go missing from the listing.
    """
    match document:
        case Entry():
            lines = (line for prop in document.properties() for line in prop.lines if line.strip())
            return "\n".join([document.path, *lines])
        case Unreadable(path=path, reason=reason):
            return f"{path}\n{reason}"
    # A third kind of document added without a line above fails the type check rather than
    # rendering as nothing: the match is exhaustive, so pyright narrows to `Never` here.
    assert_never(document)


def render(documents: Iterable[Document]) -> str:
    """Render the listing: a path per document, then its lines under it.

    A blank line separates documents. No ``---`` fences — they delimit a block for a
    parser, and only an agent reads this.
    """
    return "\n\n".join(_render_document(document) for document in documents)


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
    assert_never(node)


def _render_file(node: FileNode) -> str:
    """One other-files line: the corpus path, marked when the walk would not follow it.

    A bare path asserts the file is in the corpus, and for a link out of it that is false —
    only the name would leak, never the bytes, but the listing would still be claiming
    something untrue. It carries the same wording a foreign directory does, on the same
    line, because this group is one line per file.
    """
    match node:
        case File(path=path):
            return path
        case ForeignFile(path=path):
            return f"{path} {_OUTSIDE}"
        case UnreadableFile(path=path):
            return f"{path} {_UNREADABLE}"
    assert_never(node)


def render_report(
    tree: Iterable[DirectoryNode], others: Iterable[FileNode], documents: Iterable[Document]
) -> str:
    """Render the three parts of the report, each under its own heading.

    Every heading is emitted, with ``none`` under an empty one. A directory holding no
    documents is a real answer — ``docs/`` holds none in either corpus that exists today —
    so the shape of the report stays the same whether or not a part has anything in it.
    """
    sections = (
        "\n".join([_TREE_HEADING, *(_render_node(node) for node in tree)]),
        "\n".join([_OTHER_HEADING, *(tuple(_render_file(node) for node in others) or (_NONE,))]),
        "\n".join([_DOCUMENT_HEADING, render(documents) or _NONE]),
    )
    return "\n\n".join(sections)


def render_vocabulary(uses: Iterable[KeyUse]) -> str:
    """Render the tally: one ``key: documents`` line per key.

    The shape is frontmatter's own — a key, a colon, a value — because that is what the
    caller is about to write and read.
    """
    return "\n".join(f"{use.key}: {use.documents}" for use in uses)
