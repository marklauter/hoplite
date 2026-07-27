"""The Hoplite `catalog` MCP server.

Two tools today: ``contents``, a per-directory frontmatter listing over the corpus, and
``vocabulary``, a count of the frontmatter keys in use. The graph tools designed in
``docs/specs/hoplite-tool-api.md`` are not built yet.
"""

from hoplite_catalog.contents import (
    Directory,
    DirectoryNode,
    Document,
    Entry,
    ForeignDirectory,
    Property,
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
from hoplite_catalog.vocabulary import KeyUse, render_vocabulary, tally

__all__ = [
    "Directory",
    "DirectoryNode",
    "Document",
    "Entry",
    "ForeignDirectory",
    "KeyUse",
    "Property",
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
