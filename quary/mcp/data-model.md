---
title: Data model
summary: "[Contract] The entities the graph carries and the fields each one holds — pure schema, implementation-agnostic."
tags: [hoplite, mcp, contract, data-model]
created: 2026-05-25
aliases: []
---

## Overview

The graph is an in-memory labeled property graph over markdown files. One node type — `Document` — connects to other documents via two edge kinds — `mentions`, `related`. Both nodes and edges carry arbitrary key-value properties. Everything authored in YAML frontmatter — including tags — is a node property. The corpus of `.md` files is the only persistent state; everything else is derived at MCP startup.

Four core entities plus three result types:

- `Document` — a markdown file in the corpus.
- `Edge` — a typed connection between two documents.
- `NodeProperty` — a key-value pair attached to a node (a document). Tags, title, summary, created, aliases, and any user-defined frontmatter keys are all node properties.
- `EdgeProperty` — a key-value pair attached to an edge. `confidence` for `related` edges is the day-one example.
- `Hit` — a result from search.
- `TraversalHit` — a result from graph walk.
- `WriteResult` — a result from an index-maintenance operation.

`Graph` is the in-memory container that holds documents, edges, and properties; see [implementation.md](implementation.md) for its runtime shape and walker.

## Document

A markdown file in the corpus, identified by its relative path from the corpus root.

Documents split into two parts: **file-level facts** (the file itself qua file on disk) and **declared properties** (everything authored in the YAML frontmatter). File-level facts live as fields on the `Document` value; declared properties live as separate `Property` records attached to the document by id (see [Property](#property)).

File-level fields:

- `path` (required, string) — relative path from the corpus root including the file extension. Example: `notes/property-graphs.md`. The path is the document's identity within the runtime graph; rename means update the path. Aliases handle wikilink continuity across renames.
- `resolved` (required, bool) — `true` for documents that exist on disk; `false` for ghost documents (see below).
- `content_hash` (required when `resolved`, string; null when ghost) — sha256 of the body. Used for staleness detection on reindex.
- `minhash` (required when `resolved`, bytes; null when ghost) — 1024-byte MinHash signature (128 × uint64). Computed at startup; held in RAM, never persisted.

Body lives in the markdown file on disk. Hoplite reads bodies during the walk to tokenize them for FTS5 and compute MinHash signatures, then discards them — body is never persisted in the graph or the dump. To read a document's body, `Read` the file at the `path`. The markdown file is the source of truth; the graph holds derived metadata only.

Declared properties (lookup via the property store):

- `title`, `summary`, `created` — mandatory frontmatter fields, scalar values.
- `tags`, `aliases` — mandatory frontmatter fields, multi-value (one property row per element).
- Any user-defined keys — passed through unchanged with whatever shape the author wrote.

The `updated` value isn't anywhere on the model — it derives from git history when callers need it, not from frontmatter or filesystem mtime (mtime lies after git checkouts and file copies).

### Ghost documents

A wikilink pointing to a `path` that doesn't yet exist resolves to a **ghost document** — a first-class graph entity with the canonical identity but no body content and no declared properties. Inbound edges (typically `mentions`) point at the ghost as if it were a real document. When a real document at the matching path is later added, the ghost is **promoted** in place: identity stays stable, file-level fields fill in, properties populate from the new frontmatter, every inbound edge already points at the right node.

Ghosts have:

- `resolved = false`
- `path` set to the wikilink target text (after casefold-normalized lookup against the alias index fails)
- File-level fields: `content_hash`, `minhash` both `null`
- No property rows in the property store

The set of unresolved documents is queryable — ghost documents are documents with `resolved = false`, returned as the agent's intent backlog of documents referenced but not yet written.

## NodeProperty

A key-value pair attached to a node. Every YAML frontmatter field — mandatory (`title`, `summary`, `tags`, `created`, `aliases`) and user-defined (`status`, `priority`, anything else) — is a node property on the owning document.

Fields:

- `node_id` (required, int) — the node the property belongs to.
- `key` (required, string) — the frontmatter field name.
- `value` (required, string) — the field value. SQLite type-affinity preserves numeric and date values authored as such, even though the column is declared TEXT.

A document with an array-valued field (`tags: [graph-db, notes]`) carries one property row per array element. Array order is **not** preserved at the storage layer; multi-value reads return in alphabetical order by value.

Tags are properties with `key='tags'`. Tag membership queries (`tagged: graph-db`) resolve to lookups against `key='tags' AND value='graph-db'`. There is no separate Tag node type; the unification is at the property level, not the node level.

Properties never appear as edge endpoints. Edges connect nodes to nodes; properties describe what a node is.

## EdgeProperty

A key-value pair attached to an edge. Same shape as `NodeProperty`, keyed on `edge_id` instead of `node_id`.

Fields:

- `edge_id` (required, int) — the edge the property belongs to.
- `key` (required, string) — the property name.
- `value` (required, string) — the property value. Same type-affinity behavior as `NodeProperty.value`.

Day-one usage: `related` edges carry `key='confidence', value=<minhash-jaccard-score>`. `mentions` edges have no properties. The table exists to keep the model symmetric — anything we want to attach to an edge (provenance markers, derivation timestamps, custom annotations) follows the same EAV pattern without schema change.

The same indexing strategy applies: a B-tree on `(key, value)` serves the inverted lookup "which edges have this property?" without a separate table.

## Edge

A typed, directional connection between two documents.

Fields:

- `src` (required, string) — source document's canonical path.
- `dst` (required, string) — target document's canonical path (may be a ghost).
- `kind` (required, string) — edge type. Day-one vocabulary: `mentions`, `related`. No other kinds.

Each `(src, dst, kind)` triple is unique — at most one edge per pair per kind. Edge metadata beyond these three columns lives in `EdgeProperty` rows (e.g., `confidence` for `related` edges).

### Edge vocabulary

Two edge kinds, closed set:

- `mentions` — document → document (or document → ghost document). Materialized from `[[wikilinks]]` parsed in the body. Multiple wikilinks from one document to the same target collapse to a single edge; the graph records relationships, not occurrences. No properties day one.
- `related` — document ↔ document, symmetric. Materialized from pairwise MinHash similarity above a configured threshold. Both directions emitted (two edge rows per related pair). Carries a `confidence` property holding the Jaccard score.

Tag membership is **not** an edge. Tags are properties on the document; queries like `tagged: graph-db` resolve to property lookups, not edge traversal.

No aspirational types are reserved. Use cases like "cites," "contradicts," and "requires" express through `mentions` plus body prose. Tag hierarchy doesn't exist day one.

## Hit

A result from `hoplite_match_nodes`. Carries enough metadata for the agent to pick a candidate without fetching the body.

Fields:

- `path` (required, string) — the matched document's path.
- `summary` (required, string) — cached lede from frontmatter.
- `tags` (required, list of strings) — the document's tags.
- `score` (required, float) — BM25 score from FTS5. Comparable within a single call as a sort key; not comparable across calls (absolute magnitudes depend on the predicate).

`hoplite_match_nodes` returns a list of `Hit` ordered by descending score.

## TraversalHit

A result from `hoplite_traverse_nodes`. One per node reached.

Fields:

- `path` (required, string) — the reached document's path.
- `summary` (required, string) — cached lede.
- `tags` (required, list of strings) — the document's tags.
- `distance` (required, int ≥ 1) — hops from origin. Each node appears at the shortest distance from origin.
- `via_edges` (required, list of Edge) — the path taken from origin on first reach. One Edge per hop.

The origin is never included in the result set. BFS uses a visited-set; cycles short-circuit. Equal-or-longer alternative paths to an already-visited node are dropped.

## WriteResult

Returned by `hoplite_reindex` and `hoplite_dump_index`.

Fields:

- `path` (required, string) — for `reindex`, the corpus root that was scanned. For `dump_index`, the absolute path of the SQLite file written.
- `counts` (optional, dict of string → int) — row counts by entity. Returned by `dump_index`: `{"documents": N, "tags": M, "edges": K, "ghosts": G}`. Omitted by `reindex`.
- `warnings` (optional, list of strings) — non-fatal advisories. Examples: frontmatter parse errors with fallback applied, ambiguous aliases.

## Predicate

A string-typed boolean expression used by `hoplite_match_nodes` and `hoplite_traverse_nodes` to filter candidates by tag membership. The grammar is operators `&`, `|`, `!`, parentheses, with precedence `!` > `&` > `|`, left-associative. Examples: `notes`, `notes & mcp`, `(notes | journal) & !draft`.

The external query verb `tagged:` is sugar; `tagged: graph-db` is equivalent to the predicate `graph-db`. See [tool-api.md](tool-api.md#predicates) for the wire shape.

## Graph (runtime container)

The in-memory shape that holds the entities at runtime. Not a contract entity — the spec describes the conceptual graph; the implementation defines the Python `Graph` class. Summarized here so cross-references make sense:

- `documents: dict[str, Document]` — keyed by canonical path.
- `properties: dict[str, dict[str, list[str]]]` — keyed by canonical path, then by property key, yielding a list of values. `properties[path]['tags']` returns the tag list for `path`; `properties[path]['status']` returns a single-element list if `status: draft` was set.
- `out_edges: dict[str, list[Edge]]` — keyed by `src` document path.
- `in_edges: dict[str, list[Edge]]` — keyed by `dst` document path.
- `aliases: dict[str, str]` — alternate path → canonical path.
- `casefold_index: dict[str, str]` — casefolded key → canonical key. Used for case-insensitive wikilink lookup.
- `fts: sqlite3.Connection` — in-memory `:memory:` database with one FTS5 virtual table holding tokenized bodies for BM25 scoring.

All entities (`Document`, `Edge`) are immutable values (frozen dataclasses); the `Graph` container is mutable.
