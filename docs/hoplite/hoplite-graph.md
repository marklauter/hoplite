---
title: The document graph is a property graph over an addressable corpus
summary: The model canon for Hoplite — nodes, edges, properties, edge stereotypes, and reserved words. Frontmatter and inline wikilinks express this model and schema.sql stores it; this document defines it. When a surface and this document disagree, this document wins.
document:
  tags: [hoplite, graph, design, spec]
  created: 2026-05-29
---

# The document graph is a property graph over an addressable corpus

Hoplite models a markdown corpus as a property graph: documents are nodes, references between them are edges, and authored metadata hangs off both as properties. This document is the model canon — what the graph *is*. The surfaces that touch it derive from here: frontmatter ([[docs/hoplite/hoplite-frontmatter.md]]) and inline wikilinks are how an author *expresses* the graph; `schema.sql` is how it is *stored*. When a surface and this document disagree, this document wins.

## The model

The graph has two element types — nodes and edges — and one decoration — properties.

- A node is an addressable resource: a document in the corpus.
- An edge is a directed relationship from one node to another.
- A property is a typed key/value fact attached to a node or an edge.

Properties never connect things, and edges never carry identity. A node's tags say what it is; an edge's stereotype says what kind of link it is. That split — structure in nodes and edges, description in properties — is the spine of the model, and it repeats identically on both the node and edge sides.

## Nodes

A node is identified by its `uri`: a medium-agnostic, case-insensitive locator. For a corpus document the uri is its repo-relative path (`docs/notes/foo.md`); `[[Docs/Foo.md]]` and `[[docs/foo.md]]` reach the same node because the uri collates case-insensitively.

Three node variants, distinguished by whether the uri resolves to a real resource:

- Document node — a real `.md` file on disk. `resolved = true`. Carries content fingerprints: an exact hash for change detection and a similarity sketch for near-duplicate detection.
- Ghost node — a wikilink target with no backing file, authored as `[[ghost/<slug>]]` for an intentional open loop. `resolved = false`, no content. A synthetic `ghost` tag makes the corpus's unwritten references enumerable.
- URL node — an external `http(s)` reference, keyed by the verbatim URL. `resolved = false`, terminal, a synthetic `url` tag.

## Edges

An edge is directed from `src` to `dst` and carries a `kind` and a `confidence`. Kinds are a closed enum of three structural roles:

- `mentions` — document → document, materialized from a `[[wikilink]]` in body text. One edge per ordered pair, however many wikilinks point the same way.
- `cites` — document → URL node, from an inline `[text](https://…)` link.
- `related` — document ↔ document, symmetric, inferred from content similarity (MinHash Jaccard) above a threshold. Emitted as two directed rows.

`confidence` is first-class on the edge: `1.0` for authored edges (`mentions`, `cites`), the similarity score for inferred `related`. At most one edge connects a given ordered pair — `UNIQUE(src, dst)`, across all kinds — and the two-pass build inserts authored edges before inferred ones, so a hard edge always wins the slot over a `related` collision.

The kind enum is closed and stays closed. Richer relationships are expressed as stereotypes on a `mentions` edge, not as new kinds.

## Properties

Properties decompose entity-attribute-value: one row per (entity, key, value), the same shape on both sides of the graph. Node properties are authored metadata on a document; edge properties qualify a relationship, including stereotype labels. List-valued attributes fan out one row per element.

The vocabulary is open — any property key is accepted and stored, with no schema change per new key — except for the reserved words below. Values are stored as text. `tags` values are casefolded for case-insensitive lookup; other values are stored verbatim.

Tags classify; properties carry state. A tag answers "what is this?" — immutable identity, the document's type and shape and domain. A mutable property answers "what state is it in?" Conflating them (a `draft` or `closed` tag) churns identity when lifecycle moves. The full principle is in [[docs/notes/tags-classify-properties-carry-state.md]].

## Edge stereotypes

A stereotype is an open-vocabulary label on a `mentions` edge — `supports`, `contradicts`, `supersedes`, `not-related` — stored as an edge property, classifying what kind of mention the edge is without extending the closed kind enum. A new stereotype is a vocabulary-and-parser change, never a schema migration, the same way tags work; the parser does not reject unknown values. The full model, the authoring surfaces, and the seed vocabulary are in [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]].

## Reserved words

Most property keys are open vocabulary. A few are reserved: keys with a defined meaning and validation across the graph, regardless of which surface authors them. A reserved word is specified here, in the model, not at the expression layer — frontmatter and wikilinks carry the value, this document says what it means and how it is validated.

- `created` — a creation timestamp. Prefers a full ISO date-time, and accepts a bare ISO date (`YYYY-MM-DD`) for backward compatibility with the corpus's authored dates. Optional; when absent, git history is the authoritative date.

The set is open and grows as keys earn defined semantics. Each reserved word names its type and validation rule here.

## Expressions of the graph

The model is authored and read through surfaces that map onto it:

- Frontmatter — node properties (`document.<key>`) and edge stereotypes (`edge.<stereotype>: [paths]`). The contract is [[docs/hoplite/hoplite-frontmatter.md]].
- Inline wikilinks — `[[docs/<path>.md]]` materializes a `mentions` edge, `[[ghost/<slug>]]` an open loop, and `[text](https://…)` a `cites` edge. The stereotyped form `[[stereotype:path]]` is designed but not yet wired.
- Queries — `where` (ranked FTS plus property filter) and `relatives` (edge traversal) read the graph back.

## Storage

The graph persists in SQLite. The tables, columns, indexes, and their rationale live in [`schema.sql`](../../plugins/hoplite/mcp/src/hoplite/schema.sql); this document does not restate the DDL. The mapping is direct: nodes to `node`, edges to `edge` (kinds interned in `edge_kind`), properties to `node_property` and `edge_property`, the text projection to `fts`.

## Open questions

- Frontmatter canon overlap. [[docs/hoplite/hoplite-frontmatter.md]] still defines model content — the two-destinations framing and the node-property and edge-stereotype definitions — that this canon now owns. Shrink the frontmatter doc to express-only (how frontmatter writes node properties and edge stereotypes) and defer the model here, preserving any idea this canon does not yet capture and stopping on any genuine contradiction.
- The reserved-word set is incomplete. Only `created` is named. Enumerate the rest and give each its type and validation rule, the way `created` has one.
- The implementation trails this canon. The parser, the handbook component, and the frontmatter hook still need to catch up to the model: drop `created` from the mandatory set everywhere it is still listed, and implement reserved-word validation (`created` as an ISO date-time that also accepts a bare ISO date). The model leads; the surfaces derive.

## See also

- [[docs/hoplite/hoplite-frontmatter.md]] — the frontmatter expression of this model.
- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] — edge stereotypes in full.
- [[docs/notes/tags-classify-properties-carry-state.md]] — identity versus state.
- [[docs/hoplite/hoplite-architecture.md]] — the system around the graph.
