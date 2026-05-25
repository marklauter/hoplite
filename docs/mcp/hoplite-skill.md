# Hoplite skill

[Contract] The SKILL.md body the agent loads when invoked. The skill is named `hoplite` — invoked as `/hoplite` in Claude Code.

## Status

This is the drafted SKILL.md body ready to ship day one. When the implementation lands, this content becomes the actual skill file at the plugin's skill location and loads when the agent invokes `/hoplite` or when the host auto-loads it on first interaction with a Hoplite corpus.

The contract references entities and tools from [data-model.md](data-model.md) and [tool-api.md](tool-api.md). It declares the protocol the agent follows when working with the graph.

---

# Hoplite

Hoplite is a dataview over a vault of markdown notes. The vault is a directory of `.md` files with YAML frontmatter — Obsidian-compatible. Hoplite indexes the vault in memory at startup and serves four query tools so you can find, traverse, and reason about the notes. You read the notes themselves through your built-in `Read` tool, and you write new notes through your built-in `Write` and `Edit` tools.

Hoplite is the index; your file tools are the content surface. The protocol below covers both halves.

## Tools

- `hoplite_match_nodes(predicate, k=5)` — search. Returns up to `k` `Hit` records (path, summary, tags, score) ranked by relevance. `predicate` is `{text?, tagged?}` — at least one required. `text` is BM25-scored over body and summary. `tagged` is a tag expression like `notes`, `notes & mcp`, or `(notes | journal) & !draft`.
- `hoplite_traverse_nodes(from_, predicate=None, depth=1)` — breadth-first walk from a starting document. Returns `TraversalHit` records (path, summary, tags, distance, via_edges) from layers 1 through `depth`. The origin is not included. Predicate fields (all optional): `edge_types` (filter by edge kind — `member`, `mentions`, `related`), `min_confidence`, `direction` (`out`/`in`/`both`), `tagged` (tag expression filter on reached documents).
- `hoplite_reindex()` — rebuild the in-memory graph from the current state of the corpus. Call this after you've written or edited `.md` files so your changes become visible to subsequent queries.
- `hoplite_dump_index(path=None)` — debug. Snapshots the in-memory graph to a SQLite file (default `.hoplite/index.db`). Then you can `Bash sqlite3 .hoplite/index.db` for arbitrary SQL exploration. Useful when a query doesn't return what you expected.

There is no CRUD tool. You write notes by writing `.md` files directly with `Write` / `Edit`; you delete them by removing the file with `Bash rm`. After any batch of writes, call `hoplite_reindex` so the graph picks up the changes.

## Reading protocol

The typical flow is search → read → traverse:

1. `hoplite_match_nodes({text: "phrase describing what you want"})` — returns candidate documents.
2. Inspect the hits — each carries summary and tags so you can pick without fetching the body.
3. `Read` the document at the chosen path to get the full body.
4. If you need related context, `hoplite_traverse_nodes(from_=path, depth=1)` returns the immediate neighbors; bigger `depth` widens the walk.
5. `Read` more documents as needed.

You can also enter directly by path if you already know it — `Read` it and then `hoplite_traverse_nodes` to find its neighbors.

`hoplite_dump_index` is your escape hatch when search isn't returning what you expect. Dump the index, query the SQLite file with `Bash sqlite3 ... "SELECT ..."`, and diagnose.

## Writing protocol

To create a new note, `Write` a `.md` file under the corpus root with a YAML frontmatter block at the top, then call `hoplite_reindex`.

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
- `tags` — list of tag slugs. Use kebab-case (`graph-db`, not `Graph DB` or `graph_db`) so case-insensitive lookup works as you'd expect. Empty list (`tags: []`) is fine.
- `created` — ISO date string (`YYYY-MM-DD`).
- `aliases` — list of strings. Empty by default. On rename, add the old path to `aliases` so wikilinks pointing at the old name still resolve.

User-defined keys pass through unchanged — `status: draft`, `priority: high`, anything you want. Hoplite stores them but doesn't act on them; they're available for your queries and for external tools like Obsidian.

Body content goes after the closing `---` fence. The body has no required shape — it's just markdown. To link to another document, use `[[path/to/target.md]]` or `[[alias-name]]` — wikilinks resolve case-insensitively, and the indexer emits a `:mentions` edge for each one. A wikilink to a path that doesn't exist materializes a ghost document (queryable as your "open loops" backlog of notes you've mentioned but not yet written).

To modify an existing note, `Edit` or `Write` the file in place and call `hoplite_reindex`. To delete, `Bash rm path/to/note.md` and call `hoplite_reindex`. The corpus is the source of truth; Hoplite picks up whatever's on disk.

## Picking a filename

Filenames are presentation, not identity — agents and users can rename freely as long as wikilinks get aliases. Reasonable defaults: kebab-case, descriptive, optionally prefixed by a directory (`notes/foo.md`, `journal/2026-05-25-design-call.md`). The skill doesn't enforce a slug rule; the convention is human readability, not a canonical form.

## Edges

Three edge kinds materialize. You don't author them directly; the indexer derives them from frontmatter and body:

- `member` — tag → document. One per `(tag, doc)` pair from `tags` in frontmatter.
- `mentions` — document → document. One per `[[wikilink]]` in body text. Wikilinks to nonexistent targets create ghost documents.
- `related` — document ↔ document, symmetric. Emitted by MinHash similarity above threshold.

Use `hoplite_traverse_nodes` with `edge_types: ["related"]` to find documents Hoplite considers topically related to a starting point. `edge_types: ["mentions"]` follows the explicit wikilink graph. Default (no `edge_types`) follows all three.

## Vocabulary

- **Document** — a markdown file in the corpus. Identified by relative path.
- **Tag** — a free-form annotation, a graph node that contains documents as members.
- **Ghost document** — a wikilink target that doesn't yet exist on disk. First-class graph entity with `resolved = false`; gets promoted in place when you actually write the file.
- **Edge** — a typed connection between nodes. Three kinds: `member`, `mentions`, `related`.
- **Hit** — a search result from `hoplite_match_nodes`. A role, not a type.
- **TraversalHit** — a result from `hoplite_traverse_nodes`. Carries `distance` and `via_edges`.
- **Wikilink** — `[[path-or-alias]]` syntax in body text. The indexer parses these and emits `:mentions` edges.
- **Reindex** — rebuild the in-memory graph from current corpus state. Call after writing or editing `.md` files.
