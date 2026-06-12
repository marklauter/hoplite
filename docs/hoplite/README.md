---
title: Hoplite spec — document map
summary: The index and table of contents for the Hoplite spec corpus. Captures the agreed document hierarchy — problem, structure and indexing, write-side and read-side affordances — and tracks which nodes are files, sections, or still planned.
tags: [hoplite, index, spec]
created: 2026-06-04
document.status: wip
---

# Hoplite spec — document map

The agreed outline for the Hoplite spec corpus, treated as an index. Each node is a concept; some are their own file, some are sections within a parent, some are planned. The tree shows the hierarchy; the list below links the files and marks status.

## Map

- hoplite - problem statement and scope
  - feature taxonomy - the nouns: give rise to affordances
  - affordances - the verbs: read and write operations
    - authoring
      - frontmatter - reifies asserted feature in the YAML block
      - in-content links - reifies declared edges as inline wikilinks
    - navigation - read-side
      - survey
      - search
      - filter
      - walk
      - projection
  - graph
    - structure
      - nodes
      - edges
      - property graph
      - stereotype graph
      - vocabulary
      - FTS
      - minhash ranked edges
    - indexing
      - walking the corpus
      - discover: minhash-ranked edges section
  - tool-api - MCP endpoint signatures
    - match -> {survey, filter, search, walk, projection}
    - reindex

## Documents

- [[docs/hoplite/hoplite.md]] — problem statement and scope. Why the graph exists, what it covers. *Exists.*
- [[docs/hoplite/hoplite-feature-taxonomy.md]] — the feature taxonomy: intrinsic (recovered from the bytes) vs asserted (supplied by the author), and the IDF-weighted Jaccard relatedness over the unified feature set. The nouns — they give rise to the affordances. *Exists (wip).*
- [[docs/hoplite/hoplite-declare-and-describe.md]] — authoring: the write-side mutation surface for asserting features. Rename to `authoring` pending. *Exists (stub).*
- [[docs/hoplite/hoplite-frontmatter.md]] — reifies the asserted features in the YAML block: title, summary, tags, properties, stereotyped edges. *Exists.*
- [[docs/hoplite/hoplite-affordances.md]] — navigation: the read-side query surface — match and its clauses (survey, filter, search, walk, projection). Rename to `navigation` pending. *Exists; rename pending.*
- [[docs/hoplite/hoplite-graph.md]] — the structure (nodes, edges, property and stereotype graph, vocabulary, BM25 FTS, minhash edges) plus **indexing**, the ETL that builds the graph from the corpus (walking the corpus → building minhash-ranked edges). Indexing is a section here, breakable into its own file if it grows. *Exists; indexing section pending.*
- [[docs/hoplite/hoplite-tool-api.md]] — the MCP endpoint surface: survey, match, walk, reindex. Realizes the read-operations (survey/match/walk) plus the reindex trigger for indexing, so it spans graph and navigation. *Exists.*

## Outside the map

- [[docs/hoplite/hoplite-architecture.md]] — system internals (walker, FTS, minhash, dump). Placement under the map is deferred; it overlaps `indexing`.
- [[docs/hoplite/hoplite-roadmap.md]] — features deferred past day one.
- [[docs/hoplite/hoplite-glossary.md]] — definitions for every Hoplite domain term; cross-cutting reference over the whole map.

## Conventions

- The tree is the contract; the files trail it. A node marked *section* lives inside its parent file until it earns its own.
- `survey` is the read-operation; `vocabulary` is its structural counterpart in graph.
- `match` is one operation expressing two ideas — property/stereotype predicates and semantic FTS search.
