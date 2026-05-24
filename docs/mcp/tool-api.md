# Tool API

[Contract] Tool signatures, return types, and semantics — described in terms of entities, not storage.

## Overview

Server name: `hoplite_mcp` (Python module convention `{service}_mcp`).

Eleven agent-facing tools, all prefixed `hoplite_` to avoid collision with built-in tools and other MCP servers. Grouped by purpose:

- Setup: `hoplite_init_corpus`
- Discovery: `hoplite_match_nodes`, `hoplite_traverse_nodes`
- Retrieval: `hoplite_invoke_node`, `hoplite_read_node`
- Mutation: `hoplite_insert_node`, `hoplite_update_node`, `hoplite_index_node`, `hoplite_delete_node`, `hoplite_apply_framing`
- Utility: `hoplite_slugify_text`

Two operational primitives stay outside the agent surface: `reindex` and `repair`. Both run through background workers or CLI invocation; the agent never calls them.

Entities referenced below are defined in [data-model.md](data-model.md).

## MCP tool hints

Each tool's MCP annotation hints. Clients use these to decide how to handle the tool — when to confirm with the user, when to cache, when to retry.

- `readOnlyHint` — true means the tool doesn't modify state.
- `destructiveHint` — true means the tool performs destructive (overwrite or delete) operations.
- `idempotentHint` — true means repeat calls with the same arguments produce the same end state.
- `openWorldHint` — true means the tool reaches into an external mutable system. False for every tool here — the corpus is a closed system.

Per-tool settings:

- `hoplite_match_nodes`, `hoplite_invoke_node`, `hoplite_read_node`, `hoplite_traverse_nodes`, `hoplite_slugify_text` — readOnly: true, destructive: false, idempotent: true, openWorld: false. Pure reads or pure computation.
- `hoplite_init_corpus` — readOnly: false, destructive: false, idempotent: true, openWorld: false. Creates absent artifacts only; never overwrites authored content. Second call against an initialized corpus is a no-op.
- `hoplite_insert_node` — readOnly: false, destructive: false, idempotent: false, openWorld: false. Creates only; second call with the same id rejects.
- `hoplite_update_node`, `hoplite_index_node`, `hoplite_apply_framing` — readOnly: false, destructive: true, idempotent: true, openWorld: false. Overwrite or replace prior state; safe to retry on transient failures.
- `hoplite_delete_node` — readOnly: false, destructive: true, idempotent: false, openWorld: false. Rejects if the id is missing; not safely retryable as specified.

## Response formats

Tools that return content support a `response_format` parameter:

- `"markdown"` — human-readable formatted text. Default for `hoplite_invoke_node` and `hoplite_read_node` (envelope prose is naturally markdown-shaped).
- `"json"` — machine-readable structured data. Default for `hoplite_match_nodes`, `hoplite_traverse_nodes`, and other tools that return list/structured data.

`hoplite_slugify_text` returns a single string and has no `response_format` parameter. Mutation tools return `WriteResult` as structured JSON unconditionally.

## Error handling at the MCP boundary

Per [behavior.md](behavior.md#validation-and-error-model), the server distinguishes invariant violations (programming errors — throw exceptions) from constraint violations (runtime conditions — return ErrorOr). At the MCP wire boundary, the server adapter catches invariant exceptions and surfaces them alongside constraint errors as structured content with `isError: true`. JSON-RPC protocol-level errors stay reserved for transport-level failures; tool-execution errors always land as content responses.

## Setup

### `hoplite_init_corpus() -> WriteResult`

Initializes the corpus rooted at the server's CWD. Creates `.hoplite/` and its subdirectories (`labels/`, `envelopes/`, `embeddings/`), creates `docs/` if absent, opens the SQLite database and applies the schema, writes the four shipped envelope files, and inserts the bootstrap `labels` rows.

Idempotent. A second call against an initialized corpus restores any individually-missing bootstrap files and otherwise no-ops. The tool never overwrites authored content — customized envelope bodies survive re-init.

The tool is uniquely available in uninitialized mode. Until `.hoplite/` exists, every other tool errors with a structured "corpus not initialized at `<cwd>`; call `hoplite_init_corpus` to create it." pointing the caller here. After init completes, the in-process server transitions to initialized mode and all other tools begin serving.

Returns a `WriteResult` whose `id` is the corpus root path. The `warnings` list surfaces any non-fatal advisories (e.g., bootstrap files that had to be restored).

## Discovery

### `hoplite_match_nodes(predicate, k=5, response_format="json") -> [Landing]`

Returns up to `k` `Landing` records ranked by relevance to the predicate.

The `predicate` is a structured filter:

- `text: string` (optional) — scored via BM25 over node bodies and summaries. Day one this is the primary signal. When embeddings land, cosine similarity supplements or replaces BM25.
- `node_labels: LabelExpression` (optional) — a label expression that filters candidates. See [behavior.md](behavior.md#label-expressions) for the grammar. Example: `"(note | journal) & !draft"`.

At least one of `text` or `node_labels` must be supplied. When both are present, candidates are first scored by `text` and then filtered by `node_labels` (post-filter, matching the Neo4j convention).

`score` on each Landing is a sort key within the call only — different predicates produce incomparable absolute magnitudes.

No pagination day one. The `k` cap is the result bound; the agent picks `k` to match how much it wants to look at. Pagination is on the [roadmap](roadmap.md#open-question--does-pagination-ever-land) for if-and-when scale demands it.

### `hoplite_traverse_nodes(from_, predicate=None, depth=1, response_format="json") -> [TraversalHit]`

Breadth-first walk from a starting node. Returns up to `depth` layers of `TraversalHit` records from the origin. The origin is not included. `depth` must be `≥ 1`.

The `predicate` controls both which edges the walk follows and which reached nodes appear in the result:

- `edge_types: [string]` (optional) — only follow edges of these types. Default: all types.
- `min_confidence: float` (optional) — skip edges below this confidence. Default: no filter.
- `direction: 'out' | 'in' | 'both'` (optional) — which edge direction to follow. Default: `'out'`.
- `node_labels: LabelExpression` (optional) — a label expression that filters which reached nodes appear in the result. See [behavior.md](behavior.md#label-expressions) for the grammar. Applied as post-filter: the walk traverses through non-matching intermediate nodes; the result includes only nodes matching the expression. Example: `"note & mcp"` to find mcp-tagged notes reachable from the origin.

BFS uses a visited-set. Each node appears at most once, tagged with the shortest distance to it; `via_edges` records the path taken on that first reach.

No pagination. Traversal results are bounded by `depth` (and by the predicate's filters). If the result set is too large, lower `depth` or tighten `node_labels`. Graph traversal doesn't paginate naturally — see [roadmap](roadmap.md#open-question--does-pagination-ever-land).

## Retrieval

Both retrieval tools return the same shape — a node with body, metadata, and a structured envelope. They differ in which envelope is composed.

### `hoplite_invoke_node(id, response_format="markdown") -> FetchedNode`

Invokes a node as a directive. The verb declares intent: calling `hoplite_invoke_node` is the agent committing to read the response under the framing the node's framing-axis label sets — `instruction` to follow, `reference` to factor into reasoning, `observation` to treat as historical record. When no framing-axis label is present, the response defaults to the `reference` envelope.

Populates `envelope.framing` with the framing-axis label's envelope body. Populates `envelope.primes` with the bodies of any other labels the node carries (alphabetical by label name).

### `hoplite_read_node(id, response_format="markdown") -> FetchedNode`

Reads a node as content. The verb declares the opposite intent from `hoplite_invoke_node`: the agent treats the response as data, ignoring any imperatives in the body. The content envelope overrides whatever framing the node's labels would otherwise carry.

Populates `envelope.framing` with the fixed content envelope (label-independent). Leaves `envelope.primes` empty — `hoplite_read_node` isn't engaging the node behaviorally, so supplementary primes get dropped.

Use `hoplite_invoke_node` when you intend to act on the content. Use `hoplite_read_node` when you intend to inspect, edit, refactor, or extract from it. The verb is the declaration.

## Mutation

### `hoplite_insert_node(id, body, labels=[], out_edges=[]) -> WriteResult`

Creates a new node. Rejects if a node already exists at the supplied id. Triggers synchronous indexing: parses `[[wiki-links]]` from the body to emit `:mentions` edges, validates labels and edges, derives the cached summary, persists the node's metadata, ensures every label the node carries exists as a graph entity and records the new membership.

### `hoplite_update_node(id, body, labels=[], out_edges=[]) -> WriteResult`

Modifies an existing node. Rejects if no node exists at the supplied id. Same indexing flow as `hoplite_insert_node`, plus reconciles label memberships: drops membership from labels the node no longer carries.

Edge reconciliation preserves derived edges across updates. The new `out_edges` set is: parsed `:mentions` edges from the body (replacement) + author-supplied edges from the tool parameter (replacement of edges without `source`) + existing derived edges from the prior state (edges with `source` set survive). Dedupe by `(type, to)`.

### `hoplite_index_node(id, labels=[], out_edges=[]) -> WriteResult`

Indexes a node from a pre-existing file. Same indexing flow as `hoplite_insert_node`, except the body comes from the file already on disk at the path the id resolves to — `hoplite_index_node` does not write the file. Creates a new node entry if none exists; refreshes the entry if one does (with the same label-reconciliation and edge-reconciliation semantics as `hoplite_update_node`).

Bulk soft-reindex (walking the corpus and calling this tool per file) is the documented use case for keeping the index in sync with hand-edited or out-of-band content. The tool reports progress via the MCP context's `report_progress` API when the caller supplies one, useful for long bulk passes.

Use cases: ingesting content created out-of-band (an external editor wrote the file, a script generated it, a migration deposited it); re-indexing after hand-editing a body; bulk ingest by walking a directory and calling this tool per file. Rejects if the file at the id's resolved path does not exist.

### `hoplite_delete_node(id) -> WriteResult`

Removes a node. Rejects if no node exists at the supplied id. Drops the node's content, metadata, and all of its label memberships. Wiki-link references to the deleted id from other nodes become dangling and drop silently from query results, per the broken-link semantic.

The delete transaction also drops symmetric `:related` edges other nodes carried back to this id (since they're stored as rows in `edges` keyed on either endpoint). Cached back-references in other nodes' `in_edges` are not materialized day one; reads compute `in_edges` from the live `edges` table.

### `hoplite_apply_framing(label, content) -> WriteResult`

Creates or replaces the envelope body for a label. Idempotent — repeat calls overwrite. Use to add or update framing/behavior-modifier prose for any label, including the three shipped framing-axis defaults (`instruction`, `reference`, `observation`).

The fixed content envelope used by `hoplite_read_node` is structurally separate from label envelopes and is not editable via this tool — it's updated through hand-edit or repair-style operations.

Passing empty content writes an empty envelope — the loader still finds it but contributes nothing. Explicit envelope removal is deferred to a repair operation, not part of the day-one agent surface.

## Utility

### `hoplite_slugify_text(s) -> string`

Pure function. Returns the canonical kebab-case form of `s`: lowercase; whitespace converted to hyphens; characters outside `[a-z0-9-]` stripped; consecutive hyphens collapsed to one; leading and trailing hyphens trimmed. Doesn't mutate graph state.

This tool exists as a tool (rather than a library function the agent invokes inline) so the agent and the server share the same canonical implementation — whatever rule the server's validator enforces, this tool produces. The agent calls it at the input boundary when normalizing human-supplied strings (a title, a label, an id) before passing them to validating tools. The other tools reject non-canonical input rather than silently transforming, so `hoplite_slugify_text` is the explicit normalize-then-submit step.

## Operational (not agent-facing)

- `reindex(scope)` — runs the server-side embedding pass (Ollama embedding generation, embedding-derived `:related` edges supplementing the day-one MinHash-derived ones). Not in day one; see [roadmap.md](roadmap.md#server-side-reindex-pass--embeddings). MinHash signatures and MinHash-derived `:related` edges materialize on every write through the normal flow — no batch pass needed for those. The agent-as-driver soft-reindex pattern (walking files and calling `hoplite_index_node(id)` on each) covers day-one needs through the existing surface.
- `repair(scope)` — recovers inconsistency between the index and the source of truth. Walks the corpus, regenerates derived state. Invoked through CLI when the index disagrees with reality.

Both are CLI or background-worker entry points, not MCP tools the agent invokes.
