---
title: Data model
summary: "[Contract] The entities the graph carries and the fields each one holds — pure schema, implementation-agnostic."
tags: [hoplite, mcp, contract, data-model]
created: 2026-05-25
aliases: []
---

## Overview

The graph is an in-memory property graph over markdown files. Two node types — `Document` and `Tag` — connect via three edge kinds — `member`, `mentions`, `related`. Documents are markdown files in the corpus; tags are free-form annotations that documents carry. The corpus of `.md` files is the only persistent state; everything else is derived at MCP startup.

Three core entities plus three result types:

- `Document` — a markdown file in the corpus.
- `Tag` — a free-form annotation, a first-class graph node with member documents.
- `Edge` — a typed connection between nodes.
- `Hit` — a result from search.
- `TraversalHit` — a result from graph walk.
- `WriteResult` — a result from an index-maintenance operation.

`Graph` is the in-memory container that holds documents, tags, and edges; see [implementation.md](implementation.md) for its runtime shape and walker.

## Document

A markdown file in the corpus, identified by its relative path from the corpus root.

Fields:

- `path` (required, string) — relative path from the corpus root including the file extension. Example: `notes/property-graphs.md`. The path is the document's identity within the runtime graph; rename means update the path. Aliases handle wikilink continuity across renames.
- `resolved` (required, bool) — `true` for documents that exist on disk; `false` for ghost documents (see below).
- `title` (required when `resolved`, string; null when ghost) — from frontmatter.
- `summary` (required when `resolved`, string; null when ghost) — from frontmatter; one-line lede used by `hoplite_match_nodes` and `hoplite_traverse_nodes` so callers can pick a candidate without fetching the body.
- `body` (required when `resolved`, string; null when ghost) — markdown content after the YAML frontmatter block.
- `tags` (required, frozenset of strings) — tag slugs the document carries. Empty for ghosts and for documents with no `tags:` field.
- `aliases` (required, tuple of strings) — alternate paths that resolve to this document. Populates on rename; agents and humans can add entries manually. Empty by default.
- `content_hash` (required when `resolved`, string; null when ghost) — sha256 of the body. Used for staleness detection on reindex.
- `created` (required when `resolved`, ISO date string; null when ghost) — from frontmatter.
- `minhash` (required when `resolved`, bytes; null when ghost) — 1024-byte MinHash signature (128 × uint64). Computed at startup; held in RAM, never persisted.

The `updated` value isn't a Document field — it derives from git history when callers need it, not from frontmatter or filesystem mtime (mtime lies after git checkouts and file copies).

### Ghost documents

A wikilink pointing to a `path` that doesn't yet exist resolves to a **ghost document** — a first-class graph entity with the canonical identity but no body content. Inbound edges (typically `:mentions`) point at the ghost as if it were a real document. When a real document at the matching path is later added, the ghost is **promoted** in place: identity stays stable, content fields fill in, every inbound edge already points at the right node.

Ghosts have:

- `resolved = false`
- `path` set to the wikilink target text (after casefold-normalized lookup against the alias index fails)
- `tags = frozenset()`, `aliases = ()`
- All content fields (`title`, `summary`, `body`, `content_hash`, `created`, `minhash`) = `null`

The set of unresolved documents is queryable — `[doc for doc in graph.documents.values() if not doc.resolved]` returns the agent's intent backlog of documents referenced but not yet written.

## Tag

A free-form annotation. Tags are first-class graph nodes that contain documents as members.

Fields:

- `slug` (required, string) — canonical kebab-case form. Used as the dictionary key.
- `text` (required, string) — human-readable original (preserves casing from first frontmatter occurrence).
- `summary` (optional, string) — a one-line description of what the tag covers. Absent unless a user sets it.

Tag membership is materialized as `member` edges from the tag to each document that carries it (see [Edge](#edge)). The set of member documents is derived from the edge adjacency, not stored on the `Tag` value itself.

## Edge

A typed, directional connection between two nodes.

Fields:

- `src` (required, string) — source node identifier. For `member` edges, a tag slug. For `mentions` and `related` edges, a document path.
- `dst` (required, string) — target node identifier. Always a document path day one.
- `kind` (required, string) — edge type. Day-one vocabulary: `member`, `mentions`, `related`. No other kinds.
- `confidence` (optional, float in `[0, 1]`) — edge strength. `related` edges carry the MinHash similarity score; `member` and `mentions` edges leave this null (implicit 1.0).

Each `(src, dst, kind)` triple is unique — at most one edge per pair per kind.

### Edge vocabulary

Three edge kinds, closed set:

- `member` — tag → document. Materialized for every `(tag, doc)` pair where the document's frontmatter `tags` list contains the tag's slug. The external query verb `tagged: X` translates internally to traversal over `member` edges with `src` filtered to tag `X`.
- `mentions` — document → document (or document → ghost document). Materialized from `[[wikilinks]]` parsed in the body. Multiple wikilinks from one document to the same target collapse to a single edge; the graph records relationships, not occurrences.
- `related` — document ↔ document, symmetric. Materialized from pairwise MinHash similarity above a configured threshold. Both directions emitted (two edge rows per related pair).

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
- `tags: dict[str, Tag]` — keyed by canonical slug.
- `out_edges: dict[str, list[Edge]]` — keyed by `src` (path or slug).
- `in_edges: dict[str, list[Edge]]` — keyed by `dst`.
- `aliases: dict[str, str]` — alternate path → canonical path.
- `casefold_index: dict[str, str]` — casefolded key → canonical key. Used for case-insensitive wikilink and tag lookup.
- `fts: sqlite3.Connection` — in-memory `:memory:` database with one FTS5 virtual table holding tokenized bodies for BM25 scoring.

All entities (`Document`, `Tag`, `Edge`) are immutable values (frozen dataclasses); the `Graph` container is mutable.
