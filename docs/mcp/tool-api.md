# Tool API

[Contract] Tool signatures, return types, and semantics — described in terms of entities, not storage.

## Overview

Ten agent-facing tools, grouped by purpose:

- Discovery: `match`, `traverse`
- Retrieval: `invoke`, `read`
- Mutation: `insert`, `update`, `index`, `delete`, `apply_framing`
- Utility: `slugify`

Two operational primitives stay outside the agent surface: `reindex` and `repair`. Both run through background workers or CLI invocation; the agent never calls them.

Entities referenced below are defined in [data-model.md](data-model.md).

## Discovery

### `match(predicate, k=5) -> [Landing]`

Returns up to `k` `Landing` records ranked by relevance to the predicate. Day one, the predicate is a text string. Later, the predicate can grow into a structured filter combining text, label constraints, and embedding similarity.

`score` on each Landing is a sort key within the call only — different predicates produce incomparable absolute magnitudes.

### `traverse(from, depth=1, predicate) -> [TraversalHit]`

Breadth-first walk from a starting node. Returns up to `depth` layers of nodes reachable from the origin — neighbors at `distance=1`, neighbors-of-neighbors at `distance=2`, and so on through `distance=depth`. The origin is not included in the result. `depth` must be `≥ 1`.

The `predicate` filters which edges the walk follows:

- `edge_types: [string]` — only follow edges of these types. Default: all types.
- `min_confidence: float` — skip edges below this confidence. Default: no filter.
- `direction: 'out' | 'in' | 'both'` — which edge direction to follow. Default: `'out'`.

BFS uses a visited-set. Each node appears at most once, tagged with the shortest distance to it; `via_edges` records the path taken on that first reach. Default `depth=1` returns immediate neighbors — the typical "what's around this node" preview.

## Retrieval

Both retrieval tools return the same shape — a node with body, metadata, and a structured envelope. They differ in which envelope is composed.

### `invoke(id) -> FetchedNode`

Invokes a node as a directive. The verb declares intent: calling `invoke` is the agent committing to read the response under the framing the node's framing-axis label sets — `instruction` to follow, `reference` to factor into reasoning, `observation` to treat as historical record. When no framing-axis label is present, the response defaults to the `reference` envelope.

Populates `envelope.framing` with the framing-axis label's envelope body. Populates `envelope.primes` with the bodies of any other labels the node carries (alphabetical by label name).

### `read(id) -> FetchedNode`

Reads a node as content. The verb declares the opposite intent from `invoke`: the agent treats the response as data, ignoring any imperatives in the body. The content envelope overrides whatever framing the node's labels would otherwise carry.

Populates `envelope.framing` with the fixed content envelope (label-independent). Leaves `envelope.primes` empty — `read` isn't engaging the node behaviorally, so supplementary primes get dropped.

Use `invoke` when you intend to act on the content. Use `read` when you intend to inspect, edit, refactor, or extract from it. The verb is the declaration.

## Mutation

### `insert(id, body, labels=[], out_edges=[]) -> WriteResult`

Creates a new node. Rejects if a node already exists at the supplied id. Triggers synchronous indexing: parses `[[wiki-links]]` from the body to emit `:mentions` edges, validates labels and edges, derives the cached summary, persists the node's metadata, ensures every label the node carries exists as a graph entity and records the new membership.

### `update(id, body, labels=[], out_edges=[]) -> WriteResult`

Modifies an existing node. Rejects if no node exists at the supplied id. Same indexing flow as `insert`, plus reconciles label memberships: drops membership from labels the node no longer carries.

Edge reconciliation preserves derived edges across updates. The new `out_edges` set is: parsed `:mentions` edges from the body (replacement) + author-supplied edges from the tool parameter (replacement of edges without `source`) + existing derived edges from the prior state (edges with `source` set survive). Dedupe by `(type, to)`.

### `index(id, labels=[], out_edges=[]) -> WriteResult`

Indexes a node from a pre-existing file. Same indexing flow as `insert`, except the body comes from the file already on disk at the path the id resolves to — `index` does not write the file. Creates a new node entry if none exists; refreshes the entry if one does (with the same label-reconciliation and edge-reconciliation semantics as `update`).

Use cases: ingesting content created out-of-band (an external editor wrote the file, a script generated it, a migration deposited it); re-indexing after hand-editing a body; bulk ingest by walking a directory and calling `index` per file. Rejects if the file at the id's resolved path does not exist.

### `delete(id) -> WriteResult`

Removes a node. Rejects if no node exists at the supplied id. Drops the node's content, metadata, and all of its label memberships. Wiki-link references to the deleted id from other nodes become dangling and drop silently from query results, per the broken-link semantic.

Cached back-references in other nodes' `in_edges` and symmetric `:related` edges don't exist day one (reindex is deferred); when reindex lands, the next pass reconciles back-references to deleted ids.

### `apply_framing(label, content) -> WriteResult`

Creates or replaces the envelope body for a label. Idempotent — repeat calls overwrite. Use to add or update framing/behavior-modifier prose for any label, including the three shipped framing-axis defaults (`instruction`, `reference`, `observation`).

The fixed content envelope used by `read` is structurally separate from label envelopes and is not editable via this tool — it's updated through hand-edit or repair-style operations.

Passing empty content writes an empty envelope — the loader still finds it but contributes nothing. Explicit envelope removal is deferred to a repair operation, not part of the day-one agent surface.

## Utility

### `slugify(s) -> string`

Pure function. Returns the canonical kebab-case form of `s`: lowercase, whitespace converted to hyphens, characters outside `[a-z0-9-]` stripped. Doesn't mutate graph state.

The agent calls `slugify` at the input boundary when normalizing human-supplied strings (a title, a label, an id) before passing them to validating tools. The other tools reject non-canonical input rather than silently transforming, so `slugify` is the explicit normalize-then-submit step.

## Operational (not agent-facing)

- `reindex(scope)` — runs the background indexer pass: MinHash signatures, embedding generation, `:related` edge materialization. Day one no server-side reindex exists; the agent-as-driver pattern (walking nodes and calling `update` on each) covers the soft-reindex case. See [implementation-sqlite-hybrid.md](implementation-sqlite-hybrid.md#reindex--deferred-not-forgotten) and [behavior.md](behavior.md#edge-vocabulary).
- `repair(scope)` — recovers inconsistency between the index and the source of truth. Walks the corpus, regenerates derived state. Invoked through CLI when the index disagrees with reality.

Both are CLI or background-worker entry points, not MCP tools the agent invokes.
