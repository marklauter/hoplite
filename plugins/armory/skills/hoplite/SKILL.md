---
name: hoplite
description: Use when querying the markdown knowledge graph — searching by text or tag, traversing wikilink/related neighborhoods, reindexing after writes, or dumping the index for SQL debugging. Also use when authoring new documents that need to land in the corpus with valid frontmatter.
---

# Hoplite

Hoplite is a graph over the markdown vault at `docs/`. Each `.md` file is a document; YAML frontmatter at the top of each file feeds the index. Hoplite builds the graph in memory at MCP server startup and serves four tools so you can search, traverse, reindex, and dump for debugging.

Hoplite is the index; your built-in `Read`, `Write`, `Edit`, and `Bash rm` tools are the content surface. To add a document, write a `.md` file under `docs/` and call `hoplite_reindex`. To delete one, remove the file and call `hoplite_reindex`.

## Tools

- `hoplite_match_nodes(predicate, k=5)` — search. Returns up to `k` `Hit` records (path, summary, tags, score) ranked by relevance. `predicate` is `{text?, tagged?}` — at least one required. `text` is BM25-scored over body and summary. `tagged` is a tag expression like `notes`, `notes & mcp`, or `(notes | journal) & !draft`.
- `hoplite_traverse_nodes(from_, predicate=None, depth=1)` — breadth-first walk from a starting document. Returns `TraversalHit` records (path, summary, tags, distance, via_edges) for nodes at distance 1 through `depth` from the origin. Predicate fields (all optional): `edge_types` (filter by edge kind — `member`, `mentions`, `related`), `min_confidence`, `direction` (`out`/`in`/`both`), `tagged` (tag expression filter on reached documents).
- `hoplite_reindex()` — rebuild the in-memory graph from the current state of the corpus. Call after writes so subsequent queries see the changes.
- `hoplite_dump_index(path=None)` — debug. Snapshots the in-memory graph to a SQLite file (default `.hoplite/index.db`). Then you can `Bash sqlite3 .hoplite/index.db` for arbitrary SQL exploration. Useful when a query surprises you.

## Edges

Three edge kinds materialize. The indexer derives them from frontmatter and body:

- `member` — tag → document. One per `(tag, doc)` pair from `tags` in frontmatter.
- `mentions` — document → document. One per `[[wikilink]]` in body text. Unresolved wikilinks create ghost documents.
- `related` — document ↔ document, symmetric. Emitted by MinHash similarity above threshold.

Use `hoplite_traverse_nodes` with `edge_types: ["related"]` to find documents Hoplite considers topically related to a starting point. `edge_types: ["mentions"]` follows the explicit wikilink graph. Omitting `edge_types` follows all three.

## Vocabulary

- **Document** — a markdown file in the corpus. Identified by relative path.
- **Tag** — a free-form annotation, a graph node that contains documents as members.
- **Ghost document** — a wikilink target that exists in the graph alone, with `resolved = false`. Promoted in place when the file lands on disk.
- **Edge** — a typed connection between nodes. Three kinds: `member`, `mentions`, `related`.
- **Hit** — a search result from `hoplite_match_nodes`. A semantic role.
- **TraversalHit** — a result from `hoplite_traverse_nodes`. Carries `distance` and `via_edges`.
- **Wikilink** — `[[path-or-alias]]` syntax in body text. The indexer parses these and emits `mentions` edges.
- **Reindex** — rebuild the in-memory graph from current corpus state. Call after writing or editing `.md` files.

!`cat ${CLAUDE_PLUGIN_ROOT}/components/hoplite/frontmatter.md`
