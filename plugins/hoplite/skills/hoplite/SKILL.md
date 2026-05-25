---
name: hoplite
description: Use when querying the markdown knowledge graph — searching by text or tag, traversing wikilink/related neighborhoods, reindexing after writes, or dumping the index for SQL debugging. Also use when authoring new documents that need to land in the corpus with valid frontmatter.
---

# Hoplite

Hoplite is a dataview over a vault of markdown documents. The vault is a directory of `.md` files with YAML frontmatter — Obsidian-compatible. Hoplite indexes the vault in memory at startup and serves four query tools so you can find, traverse, and reason about the documents. You read the documents themselves through your built-in `Read` tool, and you write new documents through your built-in `Write` and `Edit` tools.

Hoplite is the index; your file tools are the content surface. The protocol below covers both halves.

## Tools

- `hoplite_match_nodes(predicate, k=5)` — search. Returns up to `k` `Hit` records (path, summary, tags, score) ranked by relevance. `predicate` is `{text?, tagged?}` — at least one required. `text` is BM25-scored over body and summary. `tagged` is a tag expression like `notes`, `notes & mcp`, or `(notes | journal) & !draft`.
- `hoplite_traverse_nodes(from_, predicate=None, depth=1)` — breadth-first walk from a starting document. Returns `TraversalHit` records (path, summary, tags, distance, via_edges) for nodes at distance 1 through `depth` from the origin. Predicate fields (all optional): `edge_types` (filter by edge kind — `member`, `mentions`, `related`), `min_confidence`, `direction` (`out`/`in`/`both`), `tagged` (tag expression filter on reached documents).
- `hoplite_reindex()` — rebuild the in-memory graph from the current state of the corpus. Call this after you've written or edited `.md` files so your changes become visible to subsequent queries.
- `hoplite_dump_index(path=None)` — debug. Snapshots the in-memory graph to a SQLite file (default `.hoplite/index.db`). Then you can `Bash sqlite3 .hoplite/index.db` for arbitrary SQL exploration. Useful when a query surprises you.

You write documents by writing `.md` files directly with `Write` / `Edit`; you delete them by removing the file with `Bash rm`. After any batch of writes, call `hoplite_reindex` so the graph picks up the changes.

## Reading protocol

The typical flow is search → read → traverse:

1. `hoplite_match_nodes({text: "phrase describing what you want"})` — returns candidate documents.
2. Inspect the hits — each carries summary and tags so you can pick without fetching the body.
3. `Read` the document at the chosen path to get the full body.
4. If you need related context, `hoplite_traverse_nodes(from_=path, depth=1)` returns the immediate neighbors; bigger `depth` widens the walk.
5. `Read` more documents as needed.

You can also enter directly by path if you already know it — `Read` it and then `hoplite_traverse_nodes` to find its neighbors.

`hoplite_dump_index` is your escape hatch when search surprises you. Dump the index, query the SQLite file with `Bash sqlite3 ... "SELECT ..."`, and diagnose.

## Writing protocol

To create a new document, `Write` a `.md` file under the corpus root with a YAML frontmatter block at the top, then call `hoplite_reindex`.

Frontmatter shape — five mandatory fields, plus any user-defined keys you want:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
tags: [graph-db, notes]
created: 2026-05-25
aliases: []
---
```

Mandatory:

- `title` — short, human-readable name.
- `summary` — one-line lede. Shows up in `Hit.summary` and `TraversalHit.summary` so other queries can scan it without reading the body.
- `tags` — list of tag slugs. Use kebab-case (`graph-db`, `mcp-server`) so case-insensitive lookup works as you'd expect. An empty list (`tags: []`) is valid.
- `created` — ISO date string (`YYYY-MM-DD`).
- `aliases` — list of strings. Empty by default. On rename, add the old path to `aliases` so wikilinks pointing at the old name still resolve.

User-defined keys pass through unchanged — `status: draft`, `priority: high`, anything you want. Hoplite preserves them as-is for your queries and for external tools like Obsidian.

Body content goes after the closing `---` fence as free-form markdown. To link to another document, use `[[path/to/target.md]]` or `[[alias-name]]` — wikilinks resolve case-insensitively, and the indexer emits a `mentions` edge for each one. An unresolved wikilink materializes a ghost document (queryable as your "open loops" backlog of documents you've mentioned and have yet to write).

To modify an existing document, `Edit` or `Write` the file in place and call `hoplite_reindex`. To delete, `Bash rm path/to/doc.md` and call `hoplite_reindex`. The corpus is the source of truth; Hoplite picks up whatever's on disk.

## Picking a filename

Filenames are presentation, identity lives in the path plus aliases. Agents and users rename freely; aliases preserve incoming wikilinks. Reasonable defaults: kebab-case, descriptive, optionally prefixed by a directory (`notes/foo.md`, `journal/2026-05-25-design-call.md`). The convention is human readability.

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
