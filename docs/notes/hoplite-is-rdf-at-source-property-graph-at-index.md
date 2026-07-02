---
title: Hoplite is RDF at the source, weighted triples in a property-graph store at the index
summary: "The corpus is a triple store at the authoring surface (note = subject, predicate/property-key = predicate, wikilink/value = object). The index stores the same triples in a property-graph storage layout — edges are first-class rows walked by covering index, but carry no property bag: only an intrinsic confidence weight and interned predicate labels. One triple abstraction, shapes tuned to two object types; not collapsible to a single EAV table."
tags: [note, hoplite, schema, graph]
created: 2026-07-01
status: evolving
---

# Hoplite is RDF at the source, weighted triples in a property-graph store at the index

The RDF and property-graph framings are not rivals; they describe two layers of one model. Both layers are RDF-shaped — the difference is storage.

- **Authored source (markdown)** is triples. A note is a subject; a frontmatter key or an inline edge label is a [[docs/hoplite/glossary/predicate.md|predicate]]; a wikilink or a scalar is the object. A bare wikilink carries no attributes — its predicate (the default, when none is written) is the sole carried semantics.
- **Materialized index (SQLite)** stores the same triples in a property-graph *storage layout*. An edge is a first-class row — its own id, covering indexes, walked in `O(log n + k)`. But "first-class" is a storage fact, not a data one: an edge has no property bag (`schema.md`: "an edge has no open key/value vocabulary"). Its only attributes are an intrinsic `confidence` weight and a set of interned predicate labels (the `predicate` and `edge_predicate` tables). The edge row is a reification anchor — `(src, dst)` interns the subject-object pair and its weight, and each `edge_stereotype` row adds a predicate, one triple per predicate.

The two layers reconcile because the index is a projection of the source, rebuildable at any time (`reindex`). Markdown stays canonical; the graph store is a materialized view, never the record.

## Two triple families, split by object type

The subject is always a node. The predicate and object split the store in two:

- **Edge** — `node — predicate — node`. Object is a resource (a node FK). An RDF object property.
- **Node property** — `node — property key — literal`. Object is an interned value. An RDF datatype property. See [[docs/notes/properties-subsume-first-class-columns.md]].

Node identity is the stitch: the subject of a property triple and the endpoint of an edge triple are the same node id, so the two families are one graph.

## Why not one EAV table

Collapsing everything to a single `(s, p, o)` table is the seductive wrong turn — it re-imports the cost the design exists to avoid.

- **The `walk` primitive needs covering indexes** on `src`/`dst` for `O(log n + k)` traversal — the property-graph storage choice made in [[docs/journal/2026-05-24-2134-genesis-property-graph-in-sqlite.md]]. EAV self-joins destroy it.
- **Edges carry a weight and a predicate set.** `confidence` is a per-edge value discovered edges are ranked by; the interned labels are the predicates. A single-literal-object triple table has nowhere for the weight, and re-attaching the predicate set needs the edge identity — so the first-class edge row, the reification anchor, is not optional.
- **The object domains differ**: an edge object is a node FK walked by index; a property object is a literal filtered by the `(keyid, value)` reverse index. Different access paths, different vocabularies (`predicate` vs `property_key`).

The schema is a deliberate hybrid across three axes — node identity and facets (columns), edges (first-class rows carrying weighted, predicated triples), node properties and tags (interned EAV) — each with a different right answer. "Conservation of schema" holds: late binding is correct for the open property axis, not for edges or identity.

## See also

- [[docs/hoplite/hoplite-graph.md]] — the model the schema serves (wip: still describes edge origination, which the bare-graph rework dropped; the locked `edge` glossary and `schema.md` are the source of truth — an edge is `id, src, dst, confidence`, provenance unrecorded).
- [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]] — vocabulary uris double as condition atoms (that note's older term is "predicate atoms"); vault-prefixed uris answer cross-repo identity without RDF IRIs.
- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] — the open-vocabulary policy for predicates (recorded under the retired name), including the drift concern and the audit affordance as future work.
