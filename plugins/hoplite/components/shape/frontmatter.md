## Frontmatter — the YAML envelope at the top of every document

Every document in the Hoplite vault, docs/, opens with a YAML frontmatter block delimited by `---` fences. Hoplite indexes documents through this block; a document with missing or malformed frontmatter generates a warning at reindex and stays out of the graph until fixed.

Five mandatory fields:

- `title` (string) — short, human-readable name.
- `summary` (string) — one-line lede. Returned by `hoplite_match_nodes` and `hoplite_traverse_nodes` so callers can scan candidates without opening the file.
- `tags` (list of strings) — tag slugs the document carries. Use kebab-case lowercase (`graph-db`, not `Graph DB` or `graph_db`); the indexer casefolds for lookup, but consistent authoring keeps the corpus tidy. Empty list `tags: []` is fine.
- `created` (ISO date string, `YYYY-MM-DD`) — creation date. Stays stable across edits.
- `aliases` (list of strings) — alternate paths that resolve to this document. Empty by default. On rename, add the old path so wikilinks pointing at the old name still resolve.

User-defined fields beyond those five pass through unchanged. Examples: `status: draft`, `priority: high`, `due: 2026-06-01`. Hoplite reads and stores them but doesn't act on them — they're available for your queries and for external tools like Obsidian or Dataview.

Canonical example:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
tags: [graph-db, note]
created: 2026-05-25
aliases: []
status: draft
---
```

The closing `---` fence ends the frontmatter. What follows has no required line-position shape — plain markdown, anything goes. Wikilinks anywhere in a document use `[[path/to/target.md]]` or `[[alias]]`; resolution is case-insensitive, and the indexer emits one `mentions` edge per `(source, target)` pair (multiple wikilinks to the same target collapse to one edge). A wikilink to a target that doesn't yet exist materializes a ghost document — queryable as your "open loops" backlog of documents you've mentioned but not yet written.

After writing or editing a document, call `hoplite_reindex()` so the knowledge graph picks up the change. The indexer validates each document's frontmatter and surfaces any parse failures in the `WriteResult.warnings` list. A document with a malformed or incomplete frontmatter block doesn't enter the graph until the YAML is fixed and reindex runs again.

`updated` is intentionally absent from the mandatory set — modification time derives from git history, not from frontmatter or filesystem mtime. Mtime lies after git checkouts and file copies; git is the source of truth for change history. Don't add an `updated` field expecting Hoplite to read it; it'd pass through as a user-defined property and be ignored.

### Defects to avoid

- Frontmatter missing or YAML unparseable — the indexer skips the document. Reopen, fix the YAML, re-reindex.
- One of the five mandatory fields absent — same outcome. Check the warning to see which.
- `tags` or `aliases` not a list (e.g., `tags: graph-db` instead of `tags: [graph-db]`) — the indexer skips the document.
- Title or summary that restate each other verbatim — the summary should extend the title, not duplicate it.
- Tags authored in mixed casing across files (`GraphDB` in one, `graphdb` in another). The indexer casefolds, so lookups still work, but the `Tag.text` displayed in tooling reflects whichever casing the first document used. Pick a convention.
