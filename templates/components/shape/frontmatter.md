## Frontmatter

Every document in the Hoplite corpus, docs/, opens with a YAML frontmatter block. Hoplite indexes documents through this block; a document with missing or malformed frontmatter generates a warning at reindex (in `WriteResult.warnings`) and stays out of the graph until you fix it.

Keys carry a class prefix that declares which side of the property graph they affect: `document.` for node properties, `edge.` for edge stereotypes. `title` and `summary` are the exception — they are first-class, FTS-indexed fields, not properties, so they stay **bare**.

Four mandatory fields:

- `title` (string, bare) — short, human-readable name.
- `summary` (string, bare) — one-line lede. `where` and `relatives` return it so callers can scan candidates without opening the file.
- `document.tags` (list of strings) — tag slugs the document carries. Use kebab-case lowercase (`graph-db`, not `Graph DB` or `graph_db`); the indexer casefolds for lookup, but consistent authoring keeps the corpus tidy. Empty list `document.tags: []` is fine.
- `document.created` (ISO date string, `YYYY-MM-DD`) — creation date. Stays stable across edits.

Optional fields:

- `document.aliases` (list of strings) — alternate paths that resolve to this document. Omit the key when there are no aliases; add it on rename so wikilinks pointing at the old name still resolve.

Beyond the mandatory fields, any `document.<key>` becomes a node property and any `edge.<stereotype>: [paths]` becomes a stereotyped `mentions` edge — Hoplite accepts and stores them. Examples: `document.status: draft`, `document.priority: high`, `document.due: 2026-06-01`, `edge.blocked_by: [docs/notes/foo.md]`. External tools like Obsidian or Dataview read them too. Only `title` and `summary` are bare; everything else is prefixed.

### Dotted or nested — same shape

The class prefix can be written two ways, and Hoplite normalizes both to the same dotted keys before indexing:

- **Dotted** — `document.tags: [...]`. The prefix is part of the key.
- **Nested** — a `document:` mapping with the keys indented under it. Easier to read when a document carries several properties.

A file can mix the two — a nested `document:` block alongside dotted `edge.<stereotype>` lines, for instance. `title` and `summary` stay bare in both forms. The mandatory-field, list-type, and class-prefix rules above apply to the normalized keys regardless of how they were authored, so the corpus uses nested for `document` properties by convention while the rules read in dotted terms.

### Tags classify; properties carry state

A tag answers "what is this document?" — its type, classification, the shape of artifact it represents. Tags are immutable once applied. Removing one erases the document's identity as that kind of artifact and breaks queries that rely on the classification.

A property answers "what state is this document in?" Fields that change as the lifecycle progresses (`document.status` moving from `open` to `closed`, `document.priority` re-triaged). State changes update the value, not the tag set.

State-as-tag is the anti-pattern — a `resolved`, `closed`, or `draft` tag conflates identity and state, because rewriting `document.tags` to track lifecycle churns the identity axis. Use a `document.status` property instead. The reverse also holds: do not invent a `document.type: <kind>` property to duplicate signal the type tag already carries.

Canonical example — dotted form:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
document.tags: [graph-db, note]
document.created: 2026-05-25
document.status: draft
---
```

The same document in nested form (the corpus convention), with an `edge.<stereotype>` line shown dotted alongside the nested `document:` block:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
document:
  tags: [graph-db, note]
  created: 2026-05-25
  status: draft
edge.supports: [docs/notes/sqlite-hybrid.md]
---
```
