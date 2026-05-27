## Frontmatter

Every document in the Hoplite corpus, docs/, opens with a YAML frontmatter block. Hoplite indexes documents through this block; a document with missing or malformed frontmatter generates a warning at reindex (in `WriteResult.warnings`) and stays out of the graph until you fix it.

Four mandatory fields:

- `title` (string) — short, human-readable name.
- `summary` (string) — one-line lede. `where` and `relatives` return it so callers can scan candidates without opening the file.
- `tags` (list of strings) — tag slugs the document carries. Use kebab-case lowercase (`graph-db`, not `Graph DB` or `graph_db`); the indexer casefolds for lookup, but consistent authoring keeps the corpus tidy. Empty list `tags: []` is fine.
- `created` (ISO date string, `YYYY-MM-DD`) — creation date. Stays stable across edits.

Optional fields:

- `aliases` (list of strings) — alternate paths that resolve to this document. Omit the key when there are no aliases; add it on rename so wikilinks pointing at the old name still resolve.

Every frontmatter field becomes a property on the document — Hoplite accepts and stores any field beyond the mandatory four. Examples: `document.status: draft`, `document.priority: high`, `document.due: 2026-06-01`. External tools like Obsidian or Dataview read them too.

### Tags classify; properties carry state

A tag answers "what is this document?" — its type, classification, the shape of artifact it represents. Tags are immutable once applied. Removing one erases the document's identity as that kind of artifact and breaks queries that rely on the classification.

A property answers "what state is this document in?" Fields that change as the lifecycle progresses (`document.status` moving from `open` to `closed`, `document.priority` re-triaged). State changes update the value, not the tag set.

State-as-tag is the anti-pattern — a `resolved`, `closed`, or `draft` tag conflates identity and state, because rewriting the tag set to track lifecycle churns the identity axis. Use a `document.status` property instead. The reverse also holds: do not invent a `document.type: <kind>` property to duplicate signal the type tag already carries.

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
