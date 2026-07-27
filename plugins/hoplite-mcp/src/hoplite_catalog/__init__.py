"""The Hoplite `catalog` MCP server.

One tool today: ``contents``, a frontmatter listing over a subtree of the corpus. The
graph tools designed in ``docs/specs/hoplite-tool-api.md`` are not built yet.
"""

from hoplite_catalog.contents import (
    Entry,
    collect,
    corpus_path,
    is_excluded,
    normalize_exclusions,
    project,
    read_entry,
    render,
    resolve_exclusions,
    resolve_under,
    slice_frontmatter,
)

__all__ = [
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
