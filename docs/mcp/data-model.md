# Data model

[Contract] The entities the graph carries and the fields each one holds — pure schema, implementation-agnostic.

## Overview

The graph is a labeled multigraph. Nodes carry content and metadata. Labels are named sets that nodes belong to. Edges are typed connections between nodes. Envelopes wrap content during retrieval to set the reading contract.

Six core entities plus three response types:

- Node — a content unit.
- Label — a named set of nodes.
- Edge — a typed connection between two nodes.
- Envelope — a structured wrapper applied during retrieval.
- Landing — a result from search.
- TraversalHit — a result from graph walk.
- WriteResult — a result from a write operation.

## Node

A unit of content identified by a stable id.

Fields:

- `id` (required, string) — the node's stable identifier. Lowercase kebab-case slug, `[a-z0-9-]` only.
- `labels` (required, list of strings) — the set of labels this node carries. Includes both author-supplied labels and any labels the system auto-derives.
- `out_edges` (required, list of Edge; may be empty) — edges originating from this node, both authored and derived.
- `summary` (required, string) — one-sentence lede of the body content. Used by `match`, `Landing`, and `TraversalHit` without requiring a full body read.
- `in_edges` (optional, list of Edge) — cached inversion of incoming edges; populated when corpus size makes on-demand inversion slow.
- `embedding` (optional, opaque reference) — opaque pointer to the node's vector embedding when one exists.
- `body` (required, string) — the node's content. Authored prose, typically markdown.

## Label

A named set of nodes. A label exists as a graph entity once the first node references it.

Fields:

- `id` (required, string) — the label name. Same slug rule as node ids.
- `summary` (optional, string) — one-line description of what the label covers.
- `envelope_body` (optional, string) — prose the loader inlines during `invoke` when serving a node carrying this label. Present for the three shipped framing-axis labels and any topic labels the user has set framing on.
- `members` (required, set of node ids; may be empty) — node ids that carry this label. Maintained by the indexer on every write.
- `out_edges` (optional, list of Edge) — reserved for future label-to-label edges (hierarchy, parent links). Empty day one.

## Edge

A typed, directional connection between two nodes.

Fields:

- `type` (required, string) — edge type, lowercase kebab-case. Day-one vocabulary: `mentions`, `related`. Aspirational types reserved for future passes — see [behavior.md](behavior.md#edge-vocabulary).
- `to` (required, string; for outgoing edges) — target node id.
- `from` (required, string; for incoming edges) — source node id.
- `confidence` (optional, float in `[0, 1]`) — edge strength. Authored edges carry implicit confidence 1.0. Derived edges carry the signal's score.
- `source` (optional, string) — provenance for derived edges (e.g., `minhash`, `embedding-cosine`). Authored edges omit this field.
- `rationale` (optional, string) — explanation, useful for derived edges where the reason is non-obvious.

Author-supplied edges with `source` set are rejected at write time — provenance is reserved for derived edges produced by the indexer.

## Envelope

A structured wrapper applied during retrieval. Both `invoke` and `read` return content wrapped in an envelope; the verb chooses which envelope is composed.

Fields:

- `framing` (required, string) — the primary contract for reading the body. For `invoke`: the body of the framing-axis label's envelope (defaults to the `reference` envelope when no framing-axis label is present). For `read`: the fixed content envelope, label-independent.
- `primes` (required, list of `{label: string, body: string}`; may be empty) — supplementary label envelopes, alphabetical by label name. Populated by `invoke` with any non-framing-axis labels' envelope bodies. Always empty for `read`.

The canonical display order is `framing` + `primes[*].body` + node `body`. Order matches LLM attention patterns: contract first, payload last, supplementary primes in the middle.

## Landing

A search result returned by `match`. Carries enough metadata for the agent to pick a candidate without loading the full body.

Fields:

- `id` (required, string) — the landing node's id.
- `summary` (required, string) — cached lede.
- `labels` (required, list of strings) — the node's labels.
- `score` (required, float) — relevance score from the search. Comparable within a single `match()` call as a sort key. Not comparable across calls; absolute magnitudes depend on the predicate.

## TraversalHit

A result from `traverse`. One per node reached.

Fields:

- `id` (required, string) — the reached node's id.
- `summary` (required, string) — cached lede.
- `labels` (required, list of strings) — the node's labels.
- `distance` (required, int ≥ 1) — hops from origin to this node. Each node appears at the shortest distance from origin.
- `via_edges` (required, list of Edge) — the path taken from origin on first reach. One Edge per hop.

The origin is not included in the result set. BFS uses a visited-set; cycles short-circuit, and equal-or-longer alternative paths to an already-visited node are dropped.

## WriteResult

Result returned by the write tools (`insert`, `update`, `delete`, `apply_framing`).

Fields:

- `id` (required, string) — the affected node's id (or label's id, for `apply_framing`).
- `warnings` (optional, list of strings) — non-fatal advisories from the write. Examples: dangling wiki-link targets, labels that didn't exist before this write and got created.
