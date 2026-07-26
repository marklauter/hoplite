"""The Hoplite `catalog` MCP server.

One tool today: ``contents``, a frontmatter listing over a subtree of the corpus. The
graph tools designed in ``docs/specs/hoplite-tool-api.md`` are not built yet.
"""

from hoplite_catalog.contents import Entry, collect, render, resolve_under, slice_frontmatter

__all__ = ["Entry", "collect", "render", "resolve_under", "slice_frontmatter"]
