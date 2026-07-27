"""The Hoplite `catalog` MCP server.

Two tools today: ``contents``, a per-directory frontmatter listing over the corpus, and
``vocabulary``, a count of the frontmatter keys in use. The graph tools designed in
``docs/specs/hoplite-tool-api.md`` are not built yet.

``Files`` is the filesystem port and ``RealFiles`` is the only adapter shipped. ``Corpus``
pairs a port with a resolved root and is what every walking function takes as its first
argument. ``server`` is not re-exported here: it is the composition root and an entry
point, so importing this package must not pull the host in.
"""

from hoplite_catalog.adapters import RealFiles
from hoplite_catalog.contents import (
    FENCE,
    Directory,
    DirectoryNode,
    Document,
    Entry,
    ForeignDirectory,
    Property,
    UnlistableDirectory,
    Unreadable,
    collect,
    group_properties,
    markdown_in,
    other_files,
    read_entry,
    render,
    render_report,
    resolve_under,
    slice_frontmatter,
    subdirectories,
    walk,
)
from hoplite_catalog.corpus import Corpus
from hoplite_catalog.errors import CallerError
from hoplite_catalog.ports import Files
from hoplite_catalog.vocabulary import KeyUse, render_vocabulary, tally

__all__ = [
    "FENCE",
    "CallerError",
    "Corpus",
    "Directory",
    "DirectoryNode",
    "Document",
    "Entry",
    "Files",
    "ForeignDirectory",
    "KeyUse",
    "Property",
    "RealFiles",
    "UnlistableDirectory",
    "Unreadable",
    "collect",
    "group_properties",
    "markdown_in",
    "other_files",
    "read_entry",
    "render",
    "render_report",
    "render_vocabulary",
    "resolve_under",
    "slice_frontmatter",
    "subdirectories",
    "tally",
    "walk",
]
