---
title: The document graph is a property graph over an addressable corpus
summary: The model canon for Hoplite — nodes, edges, properties, edge stereotypes, and reserved words. Frontmatter and inline wikilinks express this model and schema.sql stores it; this document defines it. When a surface and this document disagree, this document wins.
document:
  tags: [hoplite, graph, design, spec]
  created: 2026-05-29
---

# Buliding a knowledge graph over an addressable corpus: order from chaos

Hoplite models a markdown corpus as a property graph: documents are nodes, references between them are edges, and authored metadata hangs off both as properties. This document is the model canon — what the graph *is*. The surfaces that touch it derive from here: frontmatter ([[docs/hoplite/hoplite-frontmatter.md]]) and inline wikilinks are how an author *expresses* the graph; `schema.sql` is how it is *stored*. When a surface and this document disagree, this document wins.

## The model

The graph has two element types — nodes and edges — and the description that hangs off each.

- A node is an addressable resource: a document in the corpus.
- An edge is a directed relationship from one node to another.
- A property is a typed key/value fact attached to a node.
- A stereotype is an open-vocabulary label attached to an edge.

Description never connects things, and edges never carry identity. A node's tags say what it is; an edge's stereotype says what kind of link it is. That split — structure in nodes and edges, description hanging off both — is the spine of the model. The description takes a different shape on each side: a node carries an open key/value property vocabulary, an edge carries a set of stereotype labels. The symmetry is that both are described; it is not that they are described identically.

## Nodes

A node is identified by its `uri`: a medium-agnostic, case-insensitive locator. For a corpus document the uri is its repo-relative path (`docs/notes/foo.md`); `[[Docs/Foo.md]]` and `[[docs/foo.md]]` reach the same node because the uri collates case-insensitively.

Three node variants, distinguished by whether the uri resolves to a real resource:

- Document node — a real `.md` file on disk. `resolved = true`. Carries content fingerprints: an exact hash for change detection and a similarity sketch for near-duplicate detection.
- Ghost node — a wikilink target with no backing file, authored as `[[ghost/<slug>]]` for an intentional open loop. `resolved = false`, no content. A synthetic `ghost` tag makes the corpus's unwritten references enumerable.
- URL node — an external `http(s)` reference, keyed by the verbatim URL. `resolved = false`, terminal, a synthetic `url` tag.

## Edges

An edge is directed from `src` to `dst` and carries a `kind` and a `confidence`. Kind is a closed enum of two, and the two are *provenance* — who asserted the edge, not what it means:

- `declared` — the author asserted it, by writing a `[[wikilink]]` in body text. `confidence` is `1.0`.
- `discovered` — the engine inferred it from a shared or proximate feature (content similarity, co-citation, temporal proximity, and the rest). `confidence` is the graded strength of the inference.

Two things that look like kinds are not. A relationship's *meaning* — citation, refutation, endorsement — is an open-vocabulary stereotype on the edge, stored in `edge_stereotype`, never a new kind (see [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]]); a bare edge with no stereotype is simply a link. And the destination's *nature* — document, ghost, or URL — is a fact about the node, not the edge: a markdown link to an external site is a `declared` edge whose `dst` is a URL node, stereotyped `cites` only when the author means citation.

At most one edge connects a given ordered pair — `UNIQUE(src, dst)`, across both kinds. The two-pass build inserts `declared` edges first and `discovered` second, so a declared edge wins the slot over a discovered collision — declared beats discovered.

The enum is closed and stays closed; provenance is binary. Richer relationships are stereotypes, never kinds.

## Properties

Properties decompose entity-attribute-value: one row per (node, key, value). They are authored metadata on a document — `tags`, `status`, `created`, and the open vocabulary beyond. List-valued attributes fan out one row per element. Properties are a node affordance; an edge's description is its stereotype set (see [Edge stereotypes](#edge-stereotypes)), not a key/value bag.

The vocabulary is open — any property key is accepted and stored, with no schema change per new key — except for the reserved words below. Values are stored as text. `tags` values are casefolded for case-insensitive lookup; other values are stored verbatim.

The key vocabulary is interned: `property_key` is the corpus's property namespace made readable — the substrate Survey reads to hand an agent the keys it can filter on before it composes a predicate. A key is stored once and referenced by integer from every property row that carries it.

Surveying that vocabulary is the read graph's `match` shape turned on the schema — find and walk, the same two moves. Find reads the keys: a small list from `property_key`. Walk descends a key to its values — the distinct `value` rows under one `keyid`, served by the reverse index. The keys are the nodes of a vocabulary graph, `key → value` the edge, the values the reachable set. Whether a key carries a vocabulary or a free scalar resolves in the walk, never in a declaration: a key that reaches a handful of values is categorical — `tags`, `status`; one that reaches thousands of near-unique values is scalar — a timestamp, a score. Values need no interning of their own, and the schema needs no categorical flag; the `(keyid, value)` index carries the walk, and the agent reads the distinction off its result. The rule that falls out: intern the find namespace, not the walk values — `property_key` interns node keys, `stereotype` interns edge labels, while walk-reached node values stay inline. The edge side has a single description dimension and nothing beneath it, so its survey is the find alone — a direct read of the interned `stereotype` table, the edge-side counterpart to `property_key`, with no walk to follow.

Tags classify; properties carry state. A tag answers "what is this?" — immutable identity, the document's type and shape and domain. A mutable property answers "what state is it in?" Conflating them (a `draft` or `closed` tag) churns identity when lifecycle moves. The full principle is in [[docs/notes/tags-classify-properties-carry-state.md]].

## Edge stereotypes

A stereotype is an open-vocabulary label on a `declared` edge — `supports`, `contradicts`, `supersedes`, `not-related` — interned in `stereotype` and linked to its edges through `edge_stereotype`, classifying what kind of link the edge is without extending the closed kind enum. It is a label, not a key/value property: an edge's description is a set of stereotypes, not the open key/value vocabulary a node carries, so the labels live in their own interned vocabulary and a junction table rather than an EAV bag. That vocabulary is the edge-side survey namespace — the counterpart to `property_key`. A new stereotype is a vocabulary-and-parser change, never a schema migration, the same way tags work; the parser does not reject unknown values. The full model, the authoring surfaces, and the seed vocabulary are in [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]].

## Reserved words

Most property keys are open vocabulary. A few are reserved: keys with a defined meaning and validation across the graph, regardless of which surface authors them. A reserved word is specified here, in the model, not at the expression layer — frontmatter and wikilinks carry the value, this document says what it means and how it is validated.

- `created` — a creation timestamp. Prefers a full ISO date-time, and accepts a bare ISO date (`YYYY-MM-DD`) for backward compatibility with the corpus's authored dates. Optional; when absent, git history is the authoritative date.

The set is open and grows as keys earn defined semantics. Each reserved word names its type and validation rule here.

## Expressions of the graph

The model is authored and read through surfaces that map onto it:

- Frontmatter — node properties (`document.<key>`) and edge stereotypes (`edge.<stereotype>: [paths]`). The contract is [[docs/hoplite/hoplite-frontmatter.md]].
- Inline wikilinks — `[[docs/<path>.md]]` materializes a `declared` edge, `[[ghost/<slug>]]` an open loop, and `[text](https://…)` a `declared` edge to a URL node. The stereotyped form `[[stereotype:path]]` is designed but not yet wired.
- Queries — `where` (ranked FTS plus property filter) and `relatives` (edge traversal) read the graph back.

## Storage

The graph persists in SQLite. The tables, columns, indexes, and their rationale live in [`schema.sql`](../../plugins/hoplite/mcp/src/hoplite/schema.sql); this document does not restate the DDL. The mapping is direct: nodes to `node`, edges to `edge` (kinds interned in `edge_kind`), node properties to `node_property` (keys interned in `property_key`), edge stereotypes to `edge_stereotype` (labels interned in `stereotype`), the text projection to `fts`.

## Open questions

- Frontmatter canon overlap. [[docs/hoplite/hoplite-frontmatter.md]] still defines model content — the two-destinations framing and the node-property and edge-stereotype definitions — that this canon now owns. Shrink the frontmatter doc to express-only (how frontmatter writes node properties and edge stereotypes) and defer the model here, preserving any idea this canon does not yet capture and stopping on any genuine contradiction.
- The reserved-word set is incomplete. Only `created` is named. Enumerate the rest and give each its type and validation rule, the way `created` has one.
- The implementation trails this canon. The parser, the handbook component, and the frontmatter hook still need to catch up to the model: drop `created` from the mandatory set everywhere it is still listed, and implement reserved-word validation (`created` as an ISO date-time that also accepts a bare ISO date). The model leads; the surfaces derive.

## See also

- [[docs/hoplite/hoplite-frontmatter.md]] — the frontmatter expression of this model.
- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] — edge stereotypes in full.
- [[docs/notes/tags-classify-properties-carry-state.md]] — identity versus state.
- [[docs/hoplite/hoplite-architecture.md]] — the system around the graph.
