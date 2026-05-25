# Tool API

[Contract] Tool signatures, return types, and semantics — described in terms of entities, not storage.

## Overview

Server name: `hoplite_mcp` (Python module convention `{service}_mcp`).

Four agent-facing tools, all prefixed `hoplite_` to avoid collision with built-in tools and other MCP servers. Two for query, one for maintenance, one for debug.

- Query: `hoplite_match_nodes`, `hoplite_traverse_nodes`
- Maintenance: `hoplite_reindex`
- Debug: `hoplite_dump_index`

There is no CRUD surface. Agents write `.md` files directly through their own file tools (`Write`, `Edit`, `Bash`); Hoplite is the read/query/traversal head over the corpus, not its write path. The `/hoplite` skill teaches the file shape, the wikilink syntax, and the convention of calling `hoplite_reindex` after a batch of writes.

Entities referenced below are defined in [data-model.md](data-model.md). Behavioral rules (frontmatter shape, wikilink resolution, ghost documents, edge derivation) live in [behavior.md](behavior.md).

## MCP tool hints

Each tool's MCP annotation hints:

- `readOnlyHint` — true means the tool doesn't modify state.
- `destructiveHint` — true means the tool performs destructive (overwrite or delete) operations.
- `idempotentHint` — true means repeat calls with the same arguments produce the same end state.
- `openWorldHint` — true means the tool reaches into an external mutable system. False for every tool here — the corpus is a closed system.

Per-tool settings:

- `hoplite_match_nodes`, `hoplite_traverse_nodes` — readOnly: true, destructive: false, idempotent: true, openWorld: false. Pure reads over the in-memory graph.
- `hoplite_reindex` — readOnly: false, destructive: false, idempotent: true, openWorld: false. Rebuilds the in-memory graph; doesn't modify any persistent state (the `.md` files stay untouched). Second call with identical corpus state produces an identical graph.
- `hoplite_dump_index` — readOnly: false, destructive: true, idempotent: true, openWorld: false. Overwrites the destination SQLite file. Second call to the same path produces an identical file content given identical in-memory state.

## Predicates

The two query tools accept a tag predicate that filters which documents appear in results. The predicate is a string with the grammar defined in [behavior.md](behavior.md#tag-predicates).

The wire format wraps the predicate string in a small JSON object so other filter dimensions (e.g., text search for `match_nodes`, edge-type filter for `traverse_nodes`) can ride alongside it:

```json
{
  "text": "graph property",
  "tagged": "(notes | journal) & !draft"
}
```

The `tagged` key is the sugar — its value is the predicate string. The predicate parser interprets it directly; `tagged: graph-db` in user-facing prose is equivalent to a JSON object `{"tagged": "graph-db"}` on the wire.

When `tagged` is absent or empty, no tag filter applies.

## Tools

### `hoplite_match_nodes(predicate, k=5) -> [Hit]`

Returns up to `k` `Hit` records ranked by relevance to the predicate.

Predicate fields (at least one required):

- `text` (string) — scored via BM25 over document bodies and summaries through the in-memory FTS5 index.
- `tagged` (string) — a tag predicate (see [Predicates](#predicates)) that filters which candidates appear.

When both are present, candidates are first scored by `text` and then filtered by `tagged` (post-filter).

`score` on each `Hit` is a sort key within the call only — different predicates produce incomparable absolute magnitudes.

No pagination day one. The `k` cap is the result bound; the agent picks `k` to match how much it wants to look at. Pagination is on the [roadmap](roadmap.md).

### `hoplite_traverse_nodes(from_, predicate=None, depth=1) -> [TraversalHit]`

Breadth-first walk from a starting document. Returns up to `depth` layers of `TraversalHit` records. The origin is not included. `depth` must be `≥ 1`.

Predicate fields (all optional):

- `edge_types` (list of strings) — only follow edges of these kinds. Default: all kinds (`member`, `mentions`, `related`).
- `min_confidence` (float in `[0, 1]`) — skip edges below this confidence. Default: no filter.
- `direction` (`"out" | "in" | "both"`) — which edge direction to follow. Default: `"out"`.
- `tagged` (string) — a tag predicate that filters which reached documents appear in the result. Applied as post-filter: the walk traverses through non-matching intermediate documents; the result includes only documents matching the expression.

`from_` is the origin document's path. The trailing underscore avoids the Python keyword `from`; the JSON wire name matches.

BFS uses a visited-set. Each document appears at most once, tagged with the shortest distance to it; `via_edges` records the path taken on that first reach.

No pagination. Traversal results are bounded by `depth` (and by the predicate's filters). If the result set is too large, lower `depth` or tighten `tagged`.

### `hoplite_reindex() -> WriteResult`

Triggers a fresh corpus walk: the walker re-globs `**/*.md`, re-parses frontmatter, rebuilds the in-memory graph, repopulates the FTS5 virtual table, recomputes MinHash signatures, re-emits all edges.

No parameters. The walk runs against the corpus rooted at the server's CWD.

Returns a `WriteResult` with `path` set to the corpus root. The `warnings` list surfaces non-fatal advisories — frontmatter parse failures, unparseable wikilinks, documents missing mandatory fields.

Day one this is the only way to pick up file changes between queries. Agents that write `.md` files call `hoplite_reindex` afterward to make the new content visible. Human edits in Obsidian show up after the next reindex call. See [behavior.md](behavior.md#reindex) for the walk's two-pass shape.

### `hoplite_dump_index(path=None) -> WriteResult`

Snapshots the in-memory graph state to a SQLite file for SQL-level debugging.

Parameters:

- `path` (optional, string) — destination file path. Default: `.hoplite/index.db` relative to the corpus root.

One-shot operation. The destination is overwritten on each call; no live mirroring. The schema mirrors the in-memory shape — `documents`, `tags`, `edges`, `document_tags`, `document_aliases`, plus an FTS5 mirror. Full DDL in [implementation.md](implementation.md#dump-schema).

Returns a `WriteResult` with `path` set to the absolute path of the written file and `counts` populated with row counts per entity (`{"documents": N, "tags": M, "edges": K, "ghosts": G}`).

Then `sqlite3 .hoplite/index.db` gives developers a full SQL surface over the derived state — useful for diagnosing "why didn't this query return that document" cases.

## Error handling at the MCP boundary

Per [behavior.md](behavior.md#validation-and-error-model), invariant violations throw exceptions (programming errors the caller could have prevented — `None` for a required string, malformed predicate); constraint violations ride along inside successful results as warnings (frontmatter parse failures, ghost-resolved wikilinks, unwritable dump destinations).

At the MCP wire boundary, thrown invariant exceptions surface as structured error content with `isError: true`. Constraint warnings ride inside the `warnings` field of `WriteResult` or the analogous shape on `hoplite_reindex` and `hoplite_dump_index` results. JSON-RPC protocol-level errors stay reserved for transport-level failures; tool-execution errors always come back as content the agent can read.
