---
title: Properties subsume first-class columns
summary: "One domain concept — property — covers all frontmatter; the schema's first-class columns (summary, tags, created) are storage optimization, not a domain distinction. title is the slug (node identity), not a property."
tags: [note, hoplite, schema, glossary]
created: 2026-06-21
document.status: evolving
---

# Properties subsume first-class columns

Everything an author writes in frontmatter is a **property** — a key with a value (key/value) or a set of values (key/bag). There is no domain-level distinction between "model-defined" attributes and "open-vocabulary" ones; that split is purely a storage optimization.

- **title** is *not* a property. It is the slug — the document's identity, derived from its path/`uri` on the node. It need not appear in frontmatter at all.
- **summary**, **created**, and any author-coined key are plain key/value properties. `created` is optional (a user preference).
- **tags** is an array property — key/**bag**. Any key may carry a bag, so key/value and key/bag are one model with two value shapes.

## Domain relations (glossary)

- `property is-a feature` — a property is asserted metadata about the document (a metadata feature).
- `document has-a property` — properties belong to the document, not the bare node: a ghost (a node with no file) has no frontmatter, so no properties. Contrast `edge has-a confidence`, which every edge carries — confidence is universal to the storage element; properties are not.

## Implication for the schema

In [[docs/hoplite:schema]], the `document` facet's first-class columns (title, summary, created) and the `node_property` EAV table are two storage strategies for one concept. `content_hash`/`minhash` stay derived (intrinsic facts, computed — not author-written properties). Open question: do first-class columns survive at all, or does everything store as `node_property` (key/value) plus an array form (key/bag)?

## Where the concept is scattered today

- [[docs/hoplite:schema]] — the "every defined attribute earns a first-class home" comment and the `document` facet columns.
- [[docs/hoplite:hoplite-frontmatter]] — lists title, summary, tags, and properties as separate things.
- [[docs/hoplite/glossary:property]] and [[docs/hoplite/glossary:feature]] — the domain terms.
