"""The Hoplite `catalog` MCP server.

Two tools today: ``contents``, a per-directory frontmatter listing over the corpus, and
``vocabulary``, a count of the frontmatter keys in use. The graph tools designed in
``docs/specs/hoplite-tool-api.md`` are not built yet.

``Files`` is the filesystem port every walking function takes as its first argument, and
``RealFiles`` is the only adapter shipped. ``server`` is not re-exported here: it is the
composition root and an entry point, so importing this package must not pull the host in.
"""

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
    corpus_path,
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
from hoplite_catalog.files import Files, RealFiles
from hoplite_catalog.vocabulary import KeyUse, render_vocabulary, tally

__all__ = [
    "FENCE",
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
    "corpus_path",
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
