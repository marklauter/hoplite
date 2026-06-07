---
title: Mapping documents through intrinsic, asserted, and inferred relationships
summary: <todo - summarize when the content is locked in>
tags: [hoplite, graph, spec]
created: 2026-05-29
---

# Mapping documents through intrinsic, asserted, and inferred relationships

graph - a closure of nodes and edges.

Document features may be intrinsic, asserted, or inferred. Attributes such as identity, topic, category, location in space-time, and fingerprints are intrinsic. 

Documents may also carry author-delcared properties that form a schema over the corpus that distinquish it from another. For example, an oranization's ADR catalog exposes a different property graph than an issues catalog. Native attributes and author-defined properties form a map of related documents over many dimensions. The relationships may be explicit author-defined references to other documents, or they may be implicit such as sharing a topic, category, property, or semantic meaning.

## The document

A document's structure falls out of what a document naturally is. Each facet answers a different question about it:

- **Location** — the `uri`: where the document is addressed, a medium-agnostic, case-insensitive locator.
- **Identity** — the `title`, and `aliases`: what the document is called, and the alternate names that still resolve to it across a rename.
- **Content** — the `summary` over the body: the authored gist a reader scans before opening the work.
- **Temporal** — `created`: when the document came to be.
- **Category** — `tags`: what kind of thing the document is, its classification.
- **Properties** — user-defined attributes: the open key/values an author coins beyond the natural facets, recording state and qualities no fixed schema anticipates.

Category and properties divide cleanly: a tag classifies (what is this?), a property carries state (what condition is it in?). Conflating them — a `draft` tag instead of a `status` property — churns the document's identity every time its lifecycle moves ([[docs/notes/tags-classify-properties-carry-state.md]]).

### Variants

Not every node is a resolved file. Three variants:

- **Document** — a resolved file in the corpus, carrying every facet.
- **Ghost** — an open loop: a reference to a work not yet written, placed deliberately as `[[ghost/<slug>]]` so the intention stays visible.
- **URL** — an external reference: a link to a work the corpus points to but does not hold.

A document carries every facet; a ghost or url carries only location and identity — there is no content to summarize until a work exists to read.

## Relationships

A document points to others, and each relationship carries two facts beyond its direction:

- **Origination** — who asserted it. The author **declared** it by drawing a link, or the engine **discovered** it by inferring a nearness the author never wrote.
- **Category** — what kind of link it is: a stereotype — `cites`, `supports`, `supersedes`, `contradicts`, `not-related`. An open vocabulary, coined like tags.

A declared relationship is a link the author drew and stands behind, asserted with full confidence. A discovered one is inferred from **proximity** — documents near each other in meaning (a shared topic, a rare shared term), in time (created close together), or in structure (citing the same source) — and graded by how improbable that nearness is, so a rare shared feature counts for more than a common one. Where both assert the same pair, the declared relationship wins: the author's word outranks the engine's guess. How proximity is measured is the engine's concern, not this document's.

Every relationship reads both ways — the backlink, who-points-here, comes free. Whether it reads as symmetric is the stereotype's call: `supersedes` runs one direction, a `related` tie both.

## Vocabulary

A vocabulary organizes the corpus. A fixed scheme imposes a closed set of terms up front; Hoplite's vocabulary is open — the tags, property keys, and stereotypes the corpus coins as it grows.

That coined vocabulary is the representational schema over the corpus — the map of how the corpus describes itself. An agent reads it to learn which categories, properties, and link-meanings are in use before composing a query. The vocabulary is never imposed up front; it accretes from what authors actually write, so it always reflects the corpus as it is. That is what makes the map meaningful rather than generic — the corpus supplies its own terms.

## Storage

The model is realized as a relational schema in SQLite — tables for nodes, their document facet, the relationships, and the interned vocabularies, with a text index for content search. The tables, columns, indexes, and their rationale live in [`schema.sql`](../../plugins/hoplite/mcp/src/hoplite/schema.sql); this document stays at the level of the model the schema serves.
