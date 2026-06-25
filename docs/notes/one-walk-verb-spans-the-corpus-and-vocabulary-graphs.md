---
title: One walk verb spans the corpus graph and the vocabulary graph
summary: "The interned vocabulary is itself a graph — namespaces joined to their values — surfaced by the `namespace` view as entity-rooted uri paths (`node/tag/note`, `edge/stereotype/cites`). Survey is match + walk over that graph, the same walk verb the corpus graph uses, bound to the EAV substrate. One uri grammar addresses everything: `node` and `edge` for corpus instances, node- and edge-rooted namespaces for vocabulary, with vertices as unary paths and edges as binary tuples."
tags: [note, hoplite, graph, design]
created: 2026-06-05
---

# One walk verb spans the corpus graph and the vocabulary graph

The interned vocabulary is a graph in its own right, addressed in the same uri form as a node. Survey reads it with the same `match` and `walk` verbs the corpus uses, and the addresses it returns feed back into corpus queries as predicates.

## Two graphs

[Inference] The model carries two graphs, and the read verbs are polymorphic over which one they traverse.

- Corpus graph — nodes joined by edges (`edge`, `edge_stereotype`, `node_tag`). The `walk` read-operation traverses it: node → edges → neighbor nodes.
- Vocabulary graph — namespaces joined to their values. `node/property/tags` is wrong now that tags is a label set; the live example is `node/property/status → {draft, final}`, an edge in this graph materialized from `node_property` through the `(keyid, value)` index.

## Namespace uris

[Decision] A vocabulary entry is addressed as a uri-style path rooted under its owning entity, the same segmented form as a node uri. The `namespace` view in [`schema.sql`](../../plugins/hoplite/mcp/src/hoplite/schema.sql) projects each interned entry as `node/…` or `edge/…`: `node/tag/note`, `node/property/status`, `edge/stereotype/cites`, `edge/kind/declared`. The walk extends a property-key path by one segment: `node/property/status` → `node/property/status/draft`.

## The address space

[Inference] Everything addressable sits under one of two entity roots, `node` or `edge`, and the kind of thing is the path. Tools dispatch on the prefix.

- `node/<uri>` — a corpus vertex (`node/docs/myfile.md`); the three variants (document, ghost, url) are the next segment, and a vault segment extends it for the cross-repo case (`node/<vault>/docs/myfile.md`).
- `node/tag/<label>`, `node/property/<key>` — the node-side vocabularies; `node/property/<key>/<value>` is the walked value.
- `edge(<src>, <dst>)` — a corpus edge: a binary relation, so it has no atomic path. Its identity is the ordered pair (the `unique (src, dst)` natural key, direction by order); the surrogate `edge.id` regenerates on every rebuild, so it cannot serve as a stable address. `kind`, `confidence`, and stereotypes are attributes of the pair, not part of its identity.
- `edge/stereotype/<label>`, `edge/kind/<kind>` — the edge-side vocabularies.

[Observation] `node_alias` stays out of this addressing surface — it is a resolution index (alias → node), not a thing to survey or filter by.

[Decision] The namespaced form is the addressing register only. Stored uris and authored wikilinks stay bare (`docs/myfile.md`, `[[docs/myfile.md]]`); the `node/…` and `edge(…)` forms are what the query, predicate, and survey layer speaks — the same way the `namespace` view projects paths the base tables never store.

## Survey is walk over the vocabulary graph

[Inference] Survey is `match` + `walk` applied to the vocabulary graph instead of the corpus graph. `walk` means the same thing in both: start at an address, follow its edges, return the reachable set. The property-value lookup is `walk` over a different substrate — `node_property`, not `edge` — which is why it rides the `survey` endpoint rather than the `walk` endpoint. One verb, two graphs.

## Terminal asymmetry

[Observation] `node/property/<key>` is the only walkable namespace — it has out-edges (its values) in the vocabulary graph. `node/tag/<label>`, `edge/stereotype/<label>`, and `edge/kind/<kind>` are leaves: a label set's label is itself the value, and the kind enum is closed, so there is nothing beneath to walk to. This falls out of the schema — EAV gives key→value depth, while the label-set and enum tables hold a single dimension.

## Vocabulary uris are also predicate atoms

[Inference] Every vocabulary address doubles as a filter input to the corpus graph. The terminal namespaces are exactly the predicates injected into corpus `match` and `walk`: `edge/stereotype/cites` and `edge/kind/declared` parameterize edge selection; `node/tag/note` parameterizes a tag filter; a walked value like `node/property/status/draft` parameterizes a property filter. A vocabulary uri is simultaneously a walk-target in the vocabulary graph and a filter-input to the corpus graph.

## The pipeline

[Inference] Survey the vocabulary graph — find namespaces, walk the `node/property_key` ones to their values — and the resulting uris become predicate atoms injected into corpus `match` and `walk`. The survey tool accepts a namespace uri, parses the key segment, and builds the clause (`where keyid = …`); the uri is the parameter, so no enumerate-all-values base table is needed. A categorical key returns a handful of values, a scalar key thousands of near-uniques — the agent reads which off the result.

## See also

- [[docs/hoplite/hoplite-graph.md]] — the structure, including the Vocabulary section.
- [[docs/hoplite/hoplite-affordances.md]] — survey, match, walk, projection as read-operations.
- [[docs/journal/2026-05-31-2134-property-keys-intern-into-vocabulary-tables-that-feed-survey.md]] — the interning decision that produced the vocabulary tables.
