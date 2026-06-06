---
title: Hoplite glossary
summary: Definitions for the Hoplite domain terms — nodes, edges, properties, stereotypes, the vocabulary and address model, the read affordances, and indexing. The short form of each term; the canonical model lives in the linked spec docs.
tags: [hoplite, glossary, reference]
created: 2026-06-05
---

# Hoplite glossary

The Hoplite domain terms in short form, alphabetical. Each entry is the quick definition; the full model lives in the docs under [See also](#see-also).

## Terms

- **backlink** — the inbound view of an edge. Every edge has a tail and a head, so who-points-here comes free, with no separate storage.
- **BM25** — the ranking function over the FTS index; scores documents by topical relevance to a text query.
- **confidence** — an edge's weight. `1.0` for a declared edge, the graded strength of the inference for a discovered edge.
- **content_hash** — a node's exact byte fingerprint, for change detection. Resolved documents only.
- **corpus** — the directory of markdown files Hoplite indexes; the only persistent source of truth.
- **corpus graph** — the graph of nodes joined by edges, traversed by the walk read-operation. Contrast vocabulary graph.
- **declare** — the write affordance that asserts a relationship: a wikilink or markdown link in body text, or an edge stereotype in frontmatter. Produces a declared edge.
- **declared** — an edge kind: author-asserted, confidence `1.0`. One of the two provenance values. Contrast discovered.
- **describe** — the write affordance that annotates structure: title, summary, and properties on a document, stereotypes on an edge.
- **discover** — the engine inferring latent edges from shared features (minhash similarity and the rest). Produces discovered edges; part of indexing.
- **discovered** — an edge kind: engine-inferred, graded confidence. Contrast declared.
- **document** — a node variant: a real `.md` file on disk, `resolved = true`, carrying content fingerprints. Also the generic term for a corpus file.
- **drop-and-recreate** — the rebuild model: the graph is rebuilt whole from the corpus, never incrementally. The dominant cost is the bulk load.
- **edge** — a directed relationship between two nodes, `(src, dst)` carrying a kind and a confidence. Binary; addressed as the ordered pair, not a single uri.
- **edge_kind** — the interned closed enum of the two provenance values (declared, discovered); a vocabulary namespace.
- **edge_stereotype** — the junction table linking an edge to its stereotype labels; a set per edge.
- **filter** — narrowing the corpus by property-graph and stereotype predicates; one of the two ideas behind match.
- **fingerprint** — a node's `content_hash` (exact) and `minhash` (similarity).
- **frontmatter** — the YAML block atop each document; the reification of the declare-and-describe concepts.
- **FTS** — full-text search; the `fts5` index over title, summary, and body that powers BM25 ranking.
- **ghost** — a node variant: a wikilink target with no backing file, `resolved = false`, authored `[[ghost/<slug>]]` as an open loop.
- **indexing** — the ETL that builds the graph from the corpus: walking the corpus, then building edges, including the discovered minhash-ranked ones.
- **Jaccard** — the set-similarity measure minhash estimates; the score behind discovered similarity edges.
- **kind** — an edge's provenance, declared or discovered. Distinct from its meaning (a stereotype) and its target type (a node fact).
- **match** — the read-operation that narrows the corpus by predicate; one endpoint expressing two ideas, filter and semantic search.
- **MinHash** — the similarity sketch stored per resolved document; estimates Jaccard overlap to infer discovered edges.
- **namespace** — a top-level address segment naming the kind of addressable thing: node, edge, property_key, stereotype, edge_kind. Tools dispatch on it.
- **navigation** — the read-side affordance grouping: the read-operations (survey, match, walk, projection) plus the tool-api.
- **node** — the graph's vertex: an addressable resource identified by its uri. Variants: document, ghost, url.
- **node_property** — the EAV table holding a node's properties, one row per `(nodeid, keyid, value)`.
- **open loop** — an intentional reference to a not-yet-written document, authored as a ghost; keeps unwritten work enumerable.
- **predicate atom** — a vocabulary uri used as a filter input to corpus match or walk (e.g. `stereotype/cites`, `property_key/tags/note`).
- **projection** — organizing a result set: sorting by score or distance, capping hops and size, returning the lede and tags rather than the body.
- **property** — a typed key/value fact on a node, stored EAV; the node's open description.
- **property_key** — the interned vocabulary of property keys; an open vocabulary namespace.
- **reindex** — the maintenance endpoint that triggers a drop-and-recreate rebuild.
- **reserved word** — a property key with a defined meaning and validation across the graph (e.g. `created`), distinct from the open key vocabulary.
- **resolved** — a node flag: whether its uri backs a real resource (document) or dangles (ghost, url).
- **semantic search** — topical-relevance search over the FTS index via BM25; one of the two ideas behind match.
- **src / dst** — an edge's source and destination nodes; their order carries direction.
- **stereotype** — an open-vocabulary label on a declared edge naming its meaning (cites, supports, supersedes, contradicts, not-related). Interned; a set per edge.
- **summary** — a node's first-class one-line lede, asserted by the author and indexed for FTS. Bare in frontmatter.
- **survey** — the read-operation that reads the vocabulary before a predicate is composed; match + walk applied to the vocabulary graph (find a namespace, walk it to its values).
- **tag** — a property that classifies a document — what it is. Immutable identity, distinct from mutable state properties.
- **title** — a node's first-class short name, asserted by the author and indexed for FTS. Bare in frontmatter.
- **uri** — a node's identity: a medium-agnostic, case-insensitive locator — a repo path (`docs/…`), a `ghost/<slug>`, or a `https://…` url. Stored bare; addressed as `node/<uri>`.
- **url node** — a node variant: an external `http(s)` reference, `resolved = false`, terminal, carrying a synthetic `url` tag.
- **vault** — a corpus root in the cross-repo case; a segment under `node/` (`node/<vault>/<uri>`).
- **vocabulary** — the surveyable interned namespaces — property_key, stereotype, edge_kind — exposed as a single view, each entry a `source/value` uri. A concept over three tables, not a base table.
- **vocabulary graph** — the graph of namespaces joined to their values (`property_key/tags → {note, design}`), walked by survey. Contrast corpus graph.
- **WAL / mmap** — the SQLite settings that make the file-based store fast: WAL for concurrent readers-with-writers and cheap commits, mmap for read-through-page-cache. They retire the in-memory peer.
- **walk** — the read-operation that traverses edges from a node to gather a neighborhood. The same verb applied to the vocabulary graph is survey's second move.
- **wikilink** — an in-body `[[docs/<path>.md]]` or `[[ghost/<slug>]]` reference; materializes a declared edge.

## See also

- [[docs/hoplite/hoplite.md]] — problem statement and scope.
- [[docs/hoplite/hoplite-graph.md]] — the structure: nodes, edges, properties, stereotypes, vocabulary.
- [[docs/hoplite/hoplite-affordances.md]] — the read-operations: survey, match, walk, projection.
- [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]] — the two-graph and namespace-address model.
- [[docs/hoplite/README.md]] — the document map.
