## Frontmatter

Every document in the Hoplite corpus, docs/, opens with a YAML frontmatter block. Hoplite indexes documents through this block; a document with missing or malformed frontmatter generates a warning at reindex (in `WriteResult.warnings`) and stays out of the graph until you fix it.

Every key beyond `title` and `summary` creates one of two things. A **node property** is a fact stored on the document's own graph node — a key with one or more values (`tags`, `created`, `status`). An **edge stereotype** is a labeled link from this document to another — a typed `mentions` edge carrying a name like `blocked_by` or `supports`.

`document` and `edge` are namespaces — they declare which of the two a key creates: `document.` for node properties, `edge.` for edge stereotypes. `title` and `summary` are the exception — they are first-class, FTS-indexed fields, not properties, so they stay **bare**.

Four mandatory fields:

- `title` (string, bare) — short, human-readable name.
- `summary` (string, bare) — one-line lede. `where` and `relatives` return it so callers can scan candidates without opening the file.
- `document.tags` (list of strings) — tag slugs the document carries. Use kebab-case lowercase (`graph-db`, not `Graph DB` or `graph_db`); the indexer casefolds for lookup, but consistent authoring keeps the corpus tidy. Empty list `document.tags: []` is fine.
- `document.created` (ISO date string, `YYYY-MM-DD`) — creation date. Stays stable across edits.

Optional fields:

- `document.aliases` (list of strings) — alternate paths that resolve to this document. Omit the key when there are no aliases; add it on rename so wikilinks pointing at the old name still resolve.

Beyond the mandatory fields, any `document.<key>` becomes a node property and any `edge.<stereotype>: [paths]` becomes a stereotyped `mentions` edge — Hoplite accepts and stores them. Examples: `document.status: draft`, `document.priority: high`, `document.due: 2026-06-01`, `edge.blocked_by: [docs/notes/foo.md]`. External tools like Obsidian or Dataview read them too. Only `title` and `summary` are bare; everything else is prefixed.

### Namespace spelling and list spelling

A key carries spelling freedom on two independent axes — the namespace on the left, the list value on the right.

The **namespace** (`document`, `edge`) can be written two ways, and Hoplite normalizes both to the same key before indexing:

- **Dotted** — `document.tags: [...]`. The namespace is part of the key.
- **Nested** — a `document:` mapping with its keys indented underneath. Reads cleaner when a document carries several properties.

YAML treats these as different structures — `document.tags` is one key with a dot in its name; the nested form is a mapping under `document`. Hoplite's parser flattens the mapping to the dotted key, so the two are equivalent by Hoplite's rule, not YAML's. Neither is preferred. A file can mix them — a nested `document:` block alongside dotted `edge.<stereotype>` lines. `title` and `summary` stay bare in both forms.

A **list value** accepts any valid YAML sequence — flow or block are identical here, because YAML itself parses them to the same list:

```yaml
document.tags: [note, design]
```

```yaml
document.tags:
  - note
  - design
```

`document.tags`, `document.aliases`, and every `edge.<stereotype>` must be sequences. Any other `document.<key>` may be a bare scalar — `document.status: draft` stores as a single-value property, the same as `document.status: [draft]`.

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
