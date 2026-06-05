---
title: One walk verb spans the corpus graph and the vocabulary graph
summary: The interned vocabulary is itself a graph — namespaces joined to their values — addressed by uri-style paths (`source/value`). Survey is match + walk over that graph, the same walk verb the corpus graph uses, bound to the EAV substrate. Vocabulary uris double as predicate atoms injected into corpus match and walk. One uri grammar addresses everything — `node` and `edge` for corpus instances, `property_key`/`stereotype`/`edge_kind` for vocabulary — with vertices as unary paths and edges as binary tuples.
document:
  tags: [note, hoplite, graph, design]
  created: 2026-06-05
---

# One walk verb spans the corpus graph and the vocabulary graph

The interned vocabulary is a graph in its own right, addressed in the same uri form as a node. Survey reads it with the same `match` and `walk` verbs the corpus uses, and the addresses it returns feed straight back into corpus queries as predicates.

## Two graphs

[Inference] The model carries two graphs, and the read verbs are polymorphic over which one they traverse.

- Corpus graph — nodes joined by edges (`edge`, `edge_stereotype`). The `walk` read-operation traverses it: node → edges → neighbor nodes.
- Vocabulary graph — namespaces joined to their values. `property_key/tags → {note, design, …}` is an edge in this graph, materialized from `node_property` through the `(keyid, value)` index.

## Namespace uris

[Decision] A vocabulary entry is addressed as a uri-style path, the same segmented form as a node uri (`docs/…`, `ghost/…`, `https://…`). The `vocabulary` view in [`schema.sql`](../../plugins/hoplite/mcp/src/hoplite/schema.sql) projects each interned entry as `source/value` — `stereotype/cites`, `property_key/tags`, `edge_kind/declared` — so vocabulary entries and nodes share one addressing scheme. The walk extends the path by one segment: `property_key/tags` → `property_key/tags/note`.

## The address space — five namespaces

[Inference] Every addressable thing sits under a top-level namespace, and the kind of thing is the leading segment: `node`, `edge`, `property_key`, `stereotype`, `edge_kind`. Tools dispatch on that segment. Two populations share the grammar — `node` and `edge` address corpus instances; `property_key`, `stereotype`, and `edge_kind` address the schema vocabulary.

[Inference] Vertices are unary — one identity, one path uri. `node/docs/myfile.md` unifies the three node variants (document, ghost, url) under one prefix, with the variant as the next segment. A vault segment extends it for the cross-repo case: `node/<vault>/docs/myfile.md`.

[Inference] An edge is binary — a relation between two vertex uris, so it has no atomic path. Its identity is the ordered pair `(src, dst)` — the `unique (src, dst)` natural key, direction carried by order — represented as a tuple: `edge(node/docs/x.md, node/docs/a.md)`. The surrogate `edge.id` is storage-only and regenerates on every drop-and-recreate, so it cannot serve as a stable address. `kind`, `confidence`, and stereotypes are attributes of the pair, not part of its identity: one edge per ordered pair carries a set of stereotypes. This is graph theory showing through — vertices are atoms, edges are pairs of vertices, so the namespace grammar is a vertex grammar and an edge is a relation expressed over two of them.

[Decision] The namespaced form is the addressing register only. Stored uris and authored wikilinks stay bare (`docs/myfile.md`, `[[docs/myfile.md]]`); the `node/…` and `edge(…)` forms are what the query, predicate, and survey layer speaks — the same way the `vocabulary` view projects `source/value` without the base tables storing the prefix.

## Survey is walk over the vocabulary graph

[Inference] Survey is `match` + `walk` applied to the vocabulary graph instead of the corpus graph. `walk` means the same thing in both: start at an address, follow its edges, return the reachable set. The property-value lookup is `walk` over a different substrate — `node_property`, not `edge` — which is why it rides the `survey` endpoint rather than the `walk` endpoint. One verb, two graphs.

## Terminal asymmetry

[Observation] In the vocabulary graph, `property_key/<key>` has out-edges (its values) and walks; `stereotype/<label>` and `edge_kind/<kind>` are leaves — nothing beneath to walk to. This falls out of the schema: EAV gives key→value depth, while the `stereotype` and `edge_kind` tables hold a single dimension. From the survey point of view those two are terminal, so their survey is the find alone.

## Vocabulary uris are also predicate atoms

[Inference] Every vocabulary address doubles as a filter input to the corpus graph. The leaves that cannot be walked in the vocabulary graph are exactly the predicates injected into corpus `match` and `walk`: `stereotype/cites` and `edge_kind/declared` parameterize edge selection; a walked value like `property_key/tags/note` parameterizes a property filter in `match`. A vocabulary uri is simultaneously a walk-target in the vocabulary graph and a filter-input to the corpus graph.

## The pipeline

[Inference] Survey the vocabulary graph — find namespaces, walk the `property_key` ones to their values — and the resulting uris become predicate atoms injected into corpus `match` and `walk`. The survey tool accepts a namespace uri, parses the key segment, and builds the clause (`where keyid = …`); the uri is the parameter, so no enumerate-all-values view is needed. A categorical key returns a handful of values, a scalar key thousands of near-uniques — the agent reads which off the result.

## See also

- [[docs/hoplite/hoplite-graph.md]] — the structure, including the Vocabulary section.
- [[docs/hoplite/hoplite-affordances.md]] — survey, match, walk, projection as read-operations.
- [[docs/journal/2026-05-31-2134-property-keys-intern-into-vocabulary-tables-that-feed-survey.md]] — the interning decision that produced the vocabulary tables.
