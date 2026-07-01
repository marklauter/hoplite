---
title: Hoplite is RDF at the source, a property graph at the index
summary: "The corpus is a triple store at the authoring surface (note = subject, stereotype/property-key = predicate, wikilink/value = object) and a property graph at the materialized index (edges are first-class rows that accrete confidence and origination). One triple abstraction, two physical shapes tuned to two object types; not collapsible to a single EAV table."
tags: [note, hoplite, schema, graph]
created: 2026-07-01
status: evolving
---

# Hoplite is RDF at the source, a property graph at the index

The RDF and property-graph framings are not rivals; they describe two layers of one model.

- **Authored source (markdown)** is RDF-shaped. A note is a subject; a frontmatter key or an inline stereotype is a predicate; a wikilink or a scalar is the object. It is propertyless at authoring only because markdown cannot express edge attributes inline — the stereotype is the sole carried semantics.
- **Materialized index (SQLite)** is a property graph. An edge becomes a first-class row with an identity, and that identity anchors attributes the author never wrote — `confidence`, origination (declared vs discovered), symmetry. A property-graph edge is a natively reified triple: `(src, stereotype, dst)` plus an id its own facts hang off.

The two layers reconcile because the index is a projection of the source, rebuildable at any time (`reindex`). Markdown stays canonical; the graph store is a materialized view, never the record.

## Two triple families, split by object type

The subject is always a node. The predicate and object split the store in two:

- **Edge** — `node — stereotype — node`. Object is a resource (a node FK). An RDF object property.
- **Node property** — `node — property key — literal`. Object is an interned value. An RDF datatype property. See [[docs/notes/properties-subsume-first-class-columns.md]].

Node identity is the stitch: the subject of a property triple and the endpoint of an edge triple are the same node id, so the two families are one graph.

## Why not one EAV table

Collapsing everything to a single `(s, p, o)` table is the seductive wrong turn — it re-imports the cost the design exists to avoid.

- **Edges carry engine-computed attributes** (`confidence`, origination). A bare triple cannot hold them without reification or a quad column, and discovered edges are ranked by confidence, so this is not optional.
- **The `walk` primitive needs covering indexes** on `src`/`dst` for `O(log n + k)` traversal — the property-graph choice made in [[docs/journal/2026-05-24-2134-genesis-property-graph-in-sqlite.md]]. EAV self-joins destroy it.
- **The object domains differ**: an edge object is a node FK walked by index; a property object is a literal filtered by the `(keyid, value)` reverse index. Different access paths, different vocabularies (`stereotype` vs `property_key`).

The schema is a deliberate hybrid across three axes — node identity and facets (columns), edges (property-graph rows), node properties and tags (interned EAV) — each with a different right answer. "Conservation of schema" holds: late binding is correct for the open property axis, not for edges or identity.

## See also

- [[docs/hoplite/hoplite-graph.md]] — the model the schema serves: nodes, relationships carrying origination and stereotype, the open accreting vocabulary.
- [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]] — vocabulary uris double as predicate atoms; vault-prefixed uris answer cross-repo identity without RDF IRIs.
- [[docs/notes/edge-stereotypes-are-glossary-governed.md]] — the governance that keeps the predicate vocabulary from rotting.
