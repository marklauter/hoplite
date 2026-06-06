---
title: Hoplite spec — document map
summary: The index and table of contents for the Hoplite spec corpus. Captures the agreed document hierarchy — problem, structure and indexing, write-side and read-side affordances — and tracks which nodes are files, sections, or still planned.
tags: [hoplite, index, spec]
created: 2026-06-04
---

# Hoplite spec — document map

The agreed outline for the Hoplite spec corpus, treated as an index. Each node is a concept; some are their own file, some are sections within a parent, some are planned. The tree shows the hierarchy; the list below links the files and marks status.

## Map

- hoplite - problem statement and scope
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
  - affordances - write-side + read-side (grouping)
    - declare-and-describe - write-side concepts: the mutation surface
      - frontmatter - the reification of those concepts
    - navigation - read-side (grouping)
      - read-operations
        - survey
        - match
        - walk
        - projection
  - tool-api - MCP endpoint signatures
    - survey
    - match
    - walk
    - reindex

## Documents

- [[docs/hoplite/hoplite.md]] — problem statement and scope. Why the graph exists, what it covers. *Exists.*
- [[docs/hoplite/hoplite-graph.md]] — the structure (nodes, edges, property and stereotype graph, vocabulary, BM25 FTS, minhash edges) plus **indexing**, the ETL that builds the graph from the corpus (walking the corpus → building minhash-ranked edges). Indexing is a section here, breakable into its own file if it grows. *Exists; indexing section pending.*
- **affordances** — the affordances over the structure, write-side and read-side. A grouping, not yet its own file.
  - [[docs/hoplite/hoplite-declare-and-describe.md]] — write-side concepts: the mutation surface authors use to declare and describe. *Exists (stub).*
  - [[docs/hoplite/hoplite-frontmatter.md]] — the reification of the declare-and-describe concepts: their concrete YAML implementation. Standalone for now; folds in as the final section of declare-and-describe if ever absorbed. *Exists.*
  - **navigation** — the read-side. A grouping.
    - [[docs/hoplite/hoplite-affordances.md]] — the read-operations: survey, match (filter + semantic search behind one endpoint), walk, projection. Currently named `affordances`; resolves into the navigation read-operations doc. *Exists; rename pending.*
- [[docs/hoplite/hoplite-tool-api.md]] — the MCP endpoint surface: survey, match, walk, reindex. Realizes the read-operations (survey/match/walk) plus the reindex trigger for indexing, so it spans graph and navigation. *Exists.*

## Outside the map

- [[docs/hoplite/hoplite-architecture.md]] — system internals (walker, FTS, minhash, dump). Placement under the map is deferred; it overlaps `indexing`.
- [[docs/hoplite/hoplite-roadmap.md]] — features deferred past day one.
- [[docs/hoplite/hoplite-glossary.md]] — definitions for every Hoplite domain term; cross-cutting reference over the whole map.

## Conventions

- The tree is the contract; the files trail it. A node marked *section* lives inside its parent file until it earns its own.
- `survey` is the read-operation; `vocabulary` is its structural counterpart in graph.
- `match` is one operation expressing two ideas — property/stereotype predicates and semantic FTS search.
