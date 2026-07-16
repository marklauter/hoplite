---
title: Mapping documents through intrinsic, asserted, and inferred relationships
summary: <todo - summarize when the content is locked in>
tags: [spec, graph]
created: 2026-05-29
status: evolving
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

A tag classifies the document (what is this?); other properties record state (what condition is it in?). Both are properties — `tags` is a list property, special only by wiki convention.

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

# from hoplite.md vision document

Prose lifted verbatim from the `hoplite.md` vision draft when the vision doc was cut back to problem-plus-solution. Mining stock, not yet locked; integrate into the sections above when the model settles. The channel enumeration here is engine-measurement detail this doc currently punts ("How proximity is measured is the engine's concern"); decide whether it lands here or in a future discovery/engine spec.

## Discover — inferring latent, emergent structure

Beyond what the author declared, the corpus holds relationships no one wrote down — implicit kinship that emerges from shared features. A declared edge is asserted and treated as fact; a latent signal is implied, present only as a pattern the engine recovers by inference.

Every inferred relationship is graded by the improbability of the coincidence — a rare shared feature, or a narrow shared window. Two documents sharing a common word carry no signal; two sharing a rare term carry a strong one. That grading is why discovered relationships can be ranked.

The signals resolve into three channels, each an independent feature space.

Content and metadata measures what the documents mean. The content comparison is lexical today — shared vocabulary and overlapping phrases — surfacing a kinship the author missed and, at its extreme, gathering near-duplicates into one neighborhood instead of N strangers; but lexical overlap couples documents that share words and misses those that share meaning without them. Semantic comparison is the aspiration — coupling the caching note to the memoization note though they name nothing in common — and it lives as a ghost, [[ghost/semantic-similarity]], until the engine reads meaning from the prose rather than its surface. The metadata needs no such inference: a shared tag relates documents by kind even when their topics diverge, and documents created close in time share the intent of whatever was underway, tracing an arc — genesis, build, refactor — that no one declared and that falls out of time.

Structure measures topology, not content: two documents pointed to by the same third, pointing to the same third, citing the same external source, or naming the same rare entity couple through the shared connector — a rare connector strongly, a hub weakly. History measures provenance from the commit graph: documents changed in the same commit couple, often more strongly than their content suggests, as do documents edited in the same session or by the same author.

Latent signal buys recall at the cost of precision — it finds the connection the author missed, and sometimes one that isn't there. The threshold is the knob. Provenance ranks above score: every discovered tie is graded, but a declared edge carries full confidence and outranks any discovered one for the same pair. The author's word beats the engine's guess.
