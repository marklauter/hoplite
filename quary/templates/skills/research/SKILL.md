---
name: research
description: Use for lexical matching, ranked FTS, and traversal over the graph of the repo's markdown corpus — tag filtering, property graph filtering, traversing declared and discovered neighborhoods.
---

# Research

Reach for hoplite when the question is "what does this corpus know about X" or "what sits next to this document" — anything that wants semantic queries, ranking, knowledge graph traversal, or property graph filtering. Uses MinHash semantic edges and BM25 for semantic matching.

## When to reach for hoplite

Included:

- Topical search. "Where do we discuss caching?" — `where({"text": "caching"})` finds documents *about* the topic.
- Tag filtering. "Show me open todos in the mcp domain." — `where({"tagged": "todo & mcp"})`.
- Neighborhood exploration. "What sits next to this note?" — `relatives({"from_": "<path>"})`.
- External-reference inventory. "Where does this doc reach the outside world?" — `relatives({from_: <path>, edge_types: ["declared"]})`, then keep the `url`-tagged destinations.

Excluded:

- Literal-string search across the codebase or non-corpus files. Hoplite indexes `docs/` only — use Grep and Glob.
- Reading a known document by path — use Read.
- Mutating documents. Hoplite is read-only; writes go through Write and Edit, then `refresh()` to apply diffs to the graph.

{{components/hoplite/mcp-reference.md}}
