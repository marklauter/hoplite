---
title: Hoplite spec — document map
summary: The index and table of contents for the Hoplite spec corpus. Captures the agreed document hierarchy — problem, structure and indexing, write-side and read-side affordances — and tracks which nodes are files, sections, or still planned.
tags: [hoplite, index, spec]
created: 2026-06-04
status: evolving
---

# Hoplite spec — document map

Hoplite spec outline and index. Each items is a concept; some are their own file, some are sections within a parent, some are stubs. The tree indicates relatedness through the limitations of hierarchy and proximity.

## Map

- hoplite - problem statement and scope
  - feature taxonomy - the nouns: give rise to affordances
  - affordances - the concept: features give rise to verbs; signifiers advertise them
    - authoring - write-side: assert features
      - frontmatter - reifies asserted features in the YAML block
      - in-content links - reifies declared edges as inline wikilinks
    - navigation - read-side: query features
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

- [[docs/specs/hoplite.md]] — problem statement and scope. Why the graph exists, what it covers. *Exists.*
- [[docs/specs/hoplite-feature-taxonomy.md]] — the feature taxonomy: intrinsic (recovered from the bytes) vs asserted (supplied by the author), and the IDF-weighted Jaccard relatedness over the unified feature set. The nouns — they give rise to the affordances. *Exists (wip).*
- [[docs/specs/hoplite-authoring.md]] — authoring: the write-side mutation surface for asserting features (declare relationships, describe documents). *Exists (stub).*
- [[docs/specs/frontmatter.md]] — the frontmatter standard: flat Obsidian Properties, special keys, and edges as wikilink-valued properties. *Exists.*
- [[docs/specs/hoplite-affordances.md]] — the affordances concept: features give rise to affordances, the write/read split, and signifiers (MCP descriptions, ambient skills). The verbs over the feature nouns; sibling of feature-taxonomy. *Exists (wip).*
- [[docs/specs/hoplite-navigation.md]] — navigation: the read-side query surface — the five moves (survey, filter, walk, project, read). The read half of the affordances. *Exists (wip).*
- [[docs/specs/hoplite-read-model.md]] — the read model reduced to structure: the operations (match, walk, projection, survey) and their shared condition input (filter and semantic-search as condition kinds, composed into search expressions). The spec that navigation's move taxonomy will reconcile against. *Exists (evolving).*
- [[docs/specs/hoplite-graph.md]] — the structure (nodes, edges, property and stereotype graph, vocabulary, BM25 FTS, minhash edges) plus **indexing**, the ETL that builds the graph from the corpus (walking the corpus → building minhash-ranked edges). Indexing is a section here, breakable into its own file if it grows. *Exists; indexing section pending.*
- [[docs/specs/hoplite-tool-api.md]] — the MCP endpoint surface: survey, match, walk, reindex. Realizes the read-operations (survey/match/walk) plus the reindex trigger for indexing, so it spans graph and navigation. *Exists.*

## Outside the map

- [[docs/specs/hoplite-architecture.md]] — system internals (walker, FTS, minhash, dump). Placement under the map is deferred; it overlaps `indexing`.
- [[docs/specs/schema.md]] — the canonical SQLite schema in a `sql` block: a triple store over a node dictionary (nodes, predicates, statement edges, the slot store backing the slot nodes, FTS). Source of truth the importer's `schema.sql` mirrors.
- [[docs/specs/hoplite-roadmap.md]] — features deferred past day one.
- [[docs/glossary/README.md]] — index over the per-term glossary nodes under `docs/glossary/`; definitions for every Hoplite domain term, cross-cutting reference over the whole map.

## Conventions

- The tree is the contract; the files trail it. A node marked *section* lives inside its parent file until it earns its own.
- `survey` is the read-operation; `vocabulary` is its structural counterpart in graph.
- `match` is one operation evaluating a search expression — crisp filter conditions and scoring semantic search, composed.
