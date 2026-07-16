---
title: Properties subsume first-class columns
summary: "One domain concept — property — covers all frontmatter (title, summary, tags, created included); the schema's first-class columns are storage optimization, not a domain distinction."
tags: [note, schema, glossary]
created: 2026-06-21
status: evolving
---

# Properties subsume first-class columns

Everything an author writes in frontmatter is a property: a key with a value (key/value) or a set of values (key/bag). There is no domain-level distinction between "model-defined" attributes and "open-vocabulary" ones. That split is purely a storage optimization.

- title is a property whose value defaults to the slug (the filename, dashes as spaces), so it need not be written in frontmatter. It is a property nonetheless.
- summary, created, and any author-coined key are plain key/value properties. `created` is optional (a user preference).
- tags is an array property, key/bag. Any key may carry a bag, so key/value and key/bag are one model with two value shapes.

## Domain relations (glossary)

- `property is-a feature`: a property is asserted metadata about the document (a metadata feature).
- `document has-a property`: properties belong to the document, not the bare node. A ghost (a node with no file) has no frontmatter, so no properties. Contrast `edge has-a confidence`, which every edge carries. Confidence is universal to the storage element; properties are not.

## Implication for the schema

In [[docs/specs/schema]], the `document` facet's first-class columns (title, summary, created) and the `node_property` EAV table are two storage strategies for one concept. `content_hash`/`minhash` stay derived: they are intrinsic facts, computed, not author-written properties. Open question: do first-class columns survive at all, or does everything store as `node_property` (key/value) plus an array form (key/bag)?

## Where the concept is scattered today

- [[docs/specs/schema]]: the "every defined attribute earns a first-class home" comment and the `document` facet columns.
- [[docs/specs/hoplite-frontmatter]]: lists title, summary, tags, and properties as separate things.
- [[docs/glossary/property]] and [[docs/glossary/feature]]: the domain terms.

## See also

- [[docs/notes/stereotypes-are-open-vocab-edge-properties]]: holds the prior "title and summary are first-class fields, not properties" model that this note unifies away.
- [[docs/decisions/uris-are-a-tool-layer-projection-over-relational-storage]]: why first-class columns are a storage choice. The relational schema is the model-of-record, projected to uris at the tool boundary.
