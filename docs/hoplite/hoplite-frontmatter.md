---
title: Frontmatter
summary: "Hoplite's frontmatter standard: flat Obsidian Properties. Four special keys (all optional); every other key is open vocabulary, where a wikilink value is an edge and anything else is a node property."
tags: [hoplite, frontmatter, spec]
created: 2026-05-29
status: locked
---

# Frontmatter

Every document opens with a YAML frontmatter block. These are Obsidian [Properties](https://obsidian.md/help/properties), and Hoplite reads the same keys Obsidian does. This page sets Hoplite's standard on top of them, so the corpus keeps a fixed contract as Obsidian's docs change.

Keys are a flat, open vocabulary — no `document.` or `edge.` prefix. A few keys are special; the rest are yours to coin. A key's value decides what it is:

- A scalar or list of scalars is a node property — a fact on the document, like `status: draft`.
- A wikilink is an edge to another document, and the key is the stereotype, like `cites: ["[[shape]]"]`. For the wikilink grammar, see [[docs/hoplite/expressing-edges.md]].

Frontmatter is optional. A document without it is still valid; Hoplite derives what it needs.

## Special keys

Four keys have defined meaning. All are optional.

- `title` — a short, human-readable name, indexed for search. Defaults to the slug with dashes as spaces, like `property-graphs` → "property graphs". Set it to override.
- `summary` — a one-line lede, indexed for search and returned by every query so a caller can scan a hit without opening the file. Defaults to a body excerpt. Set it to override.
- `aliases` — the permalink mechanism. Alternate names the wikilink resolver matches, so `[[old-name]]` keeps resolving after a rename.
- `tags` — category slugs, kebab-case, like `[note, design]`. Obsidian's tag pane and the `tagged` filter read them.

A special key is read by its defined meaning, so a wikilink in one is not an edge. Every other key follows the value rule above.

There is no `updated` key. Git history is the modification record, and a hand-maintained date goes stale the moment someone forgets to update it.

## Tags and properties

Use a tag for identity and a property for state. A tag answers "what is this document?" — its type, shape, and domain — and stays fixed. A property like `status` answers "what state is it in?" and changes over time. Keep state out of tags: a `draft` tag churns the identity axis, so a closed `todo` drops out of a `tagged: todo` query. Full principle: [[docs/notes/tags-classify-properties-carry-state.md]].

## Edges

An edge is a property whose value is a wikilink, and the key is the stereotype — `supports`, `contradicts`, `supersedes`. The vocabulary is open, like tags: a new stereotype is a doc change, not a schema migration. For the grammar and seed vocabulary, see [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]].

## Obsidian and Dataview

A corpus file opens and renders in Obsidian unchanged:

- Body `[[wikilinks]]` resolve as native links.
- Every property shows in the Properties panel.
- `tags` drive the native tag pane.
- Links in properties join the graph and backlinks.

Dataview reads every key, so a query can filter on `status` or list `tags`. The flat vocabulary is what buys this: there is no namespace for Obsidian to misread.

## Sample

```yaml
---
title: Property graphs
summary: Notes on the property-graph model and SQLite tradeoffs.
tags: [graph-db, note]
created: 2026-05-25
status: draft
cites: ["[[sqlite-hybrid]]"]
---
```

## Malformed frontmatter

Nothing is required, so little is fatal.

- Unparseable YAML — Hoplite can't read the block, so it warns and indexes the document without properties, using the slug-derived title and a body-excerpt summary.
- A single bad property, like a dangling `-` or a non-list where a list belongs — Hoplite drops that property and warns.

Warnings surface in `WriteResult.warnings`, so the agent is notified while the file stays indexed. Implementation: `plugins/hoplite/mcp/src/hoplite/frontmatter.py`.

## See also

- [[docs/hoplite/expressing-edges.md]] — the edge and wikilink grammar.
- [[docs/notes/tags-classify-properties-carry-state.md]] — identity versus state.
- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] — the edge-stereotype model.
- [[docs/hoplite/hoplite-architecture.md]] — the system this feeds.
