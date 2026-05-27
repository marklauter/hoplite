## Frontmatter

Every document in the Hoplite corpus, docs/, opens with a YAML frontmatter block. Hoplite indexes documents through this block; a document with missing or malformed frontmatter generates a warning at reindex (in `WriteResult.warnings`) and stays out of the graph until you fix it.

Four mandatory fields:

- `title` (string) — short, human-readable name.
- `summary` (string) — one-line lede. `where` and `relatives` return it so callers can scan candidates without opening the file.
- `tags` (list of strings) — tag slugs the document carries. Use kebab-case lowercase (`graph-db`, not `Graph DB` or `graph_db`); the indexer casefolds for lookup, but consistent authoring keeps the corpus tidy. Empty list `tags: []` is fine.
- `created` (ISO date string, `YYYY-MM-DD`) — creation date. Stays stable across edits.

Optional fields:

- `aliases` (list of strings) — alternate paths that resolve to this document. Omit the key when there are no aliases; add it on rename so wikilinks pointing at the old name still resolve.

Every frontmatter field becomes a property on the document — Hoplite accepts and stores any field beyond the mandatory four. Examples: `status: draft`, `priority: high`, `due: 2026-06-01`. External tools like Obsidian or Dataview read them too.

Canonical example:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
tags: [graph-db, note]
created: 2026-05-25
status: draft
---
```
