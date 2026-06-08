---
title: Hoplite tool API
summary: Signatures, parameters, return types, and MCP-boundary semantics for the four agent-facing tools — where, relatives, refresh, export.
tags: [hoplite, mcp, tool-api, spec]
created: 2026-05-25
document.status: wip
---

# Hoplite tool API

Signatures, parameters, return types, and MCP-boundary semantics for the four agent-facing tools — `where`, `relatives`, `refresh`, `export`.

## Overview

Server name: `catalog` (the plugin namespace already carries the `hoplite` product identity, so the server names its capability).

Four agent-facing tools. Two for query, one for maintenance, one for debug. The plugin namespace prefix (`plugin:hoplite:catalog__<tool>`) already scopes the names against built-in tools and other MCP servers, so the tool names themselves stay short.

- Query: `where`, `relatives`
- Maintenance: `refresh`
- Debug: `export`

There is no CRUD surface. Agents write `.md` files directly through their own file tools (`Write`, `Edit`, `Bash`); Hoplite is the read/query/traversal head over the corpus, not its write path. The `taking-notes` and `journaling` skills teach the file shape, the wikilink syntax, and the convention of calling `refresh` after a batch of writes.

Entities referenced below — `Document`, `Edge`, `Hit`, `TraversalHit`, `WriteResult` — and the rules around frontmatter, wikilink resolution, ghost documents, and edge derivation are documented in [[docs/hoplite/hoplite-architecture.md]].

## MCP tool hints

Each tool's MCP annotation hints:

- `readOnlyHint` — true means the tool doesn't modify state.
- `destructiveHint` — true means the tool performs destructive (overwrite or delete) operations.
- `idempotentHint` — true means repeat calls with the same arguments produce the same end state.
- `openWorldHint` — true means the tool reaches into an external mutable system. False for every tool here — the corpus is a closed system.

Per-tool settings:

- `where`, `relatives` — readOnly: true, destructive: false, idempotent: true, openWorld: false. Pure reads over the in-memory graph.
- `refresh` — readOnly: false, destructive: false, idempotent: true, openWorld: false. Rebuilds the in-memory graph; doesn't modify any persistent state (the `.md` files stay untouched). Second call with identical corpus state produces an identical graph.
- `export` — readOnly: false, destructive: true, idempotent: true, openWorld: false. Overwrites the destination SQLite file. Second call to the same path produces an identical file content given identical in-memory state.

## Predicates

The two query tools accept a tag predicate that filters which documents appear in results. The predicate is a string with the grammar defined in [[docs/hoplite/hoplite-architecture.md#tag-predicates]].

The wire format wraps the predicate string in a small JSON object so other filter dimensions (e.g., text search for `where`, edge-type filter for `relatives`) can ride alongside it:

```json
{
  "text": "graph property",
  "tagged": "(notes | journal) & !draft"
}
```

The `tagged` key is the sugar — its value is the predicate string. `tagged: hoplite` in user-facing prose is equivalent to a JSON object `{"tagged": "hoplite"}` on the wire. Internally, the predicate compiles to a property lookup over `key='tags' AND value=<slug>` against the in-memory property store; tags are properties on documents, not separate nodes.

When `tagged` is absent or empty, no tag filter applies.

## Tools

### `where(predicate, k=5) -> [Hit]`

Returns up to `k` `Hit` records ranked by relevance to the predicate.

Predicate fields (at least one required):

- `text` (string) — scored via BM25 over document bodies and summaries through the in-memory FTS5 index.
- `tagged` (string) — a tag predicate (see [Predicates](#predicates)) that filters which candidates appear.

When both are present, candidates are first scored by `text` and then filtered by `tagged` (post-filter).

`score` on each `Hit` is a sort key within the call only — different predicates produce incomparable absolute magnitudes.

No pagination day one. The `k` cap is the result bound; the agent picks `k` to match how much it wants to look at. Pagination is on the [[docs/hoplite/hoplite-roadmap.md|roadmap]].

### `relatives(from_, predicate=None, depth=1) -> [TraversalHit]`

Breadth-first walk from a starting document. Returns up to `depth` layers of `TraversalHit` records. The origin is not included. `depth` must be `≥ 1`.

Predicate fields (all optional):

- `edge_types` (list of strings) — only follow edges of these kinds: `declared`, `discovered`. Default: both. Filtering by relationship *meaning* (only citations, only refutations) is a stereotype filter, not a kind filter; a stereotype predicate is a planned addition that lands with stereotype wiring.
- `top_k_discovered` (positive integer or unset) — cap the number of `discovered` edges followed from each node, keeping the K strongest by confidence. `declared` edges are always followed (asserted = full confidence). Default: no cap.
- `direction` (`"out" | "in" | "both"`) — which edge direction to follow. Default: `"out"`.
- `tagged` (string) — a tag predicate that filters which reached documents appear in the result. Applied as post-filter: the walk traverses through non-matching intermediate documents; the result includes only documents matching the expression.

`from_` is the origin document's path. The trailing underscore avoids the Python keyword `from`; the JSON wire name matches.

BFS uses a visited-set. Each document appears at most once, tagged with the shortest distance to it; `via_edges` records the path taken on that first reach.

No pagination. Traversal results are bounded by `depth` (and by the predicate's filters). If the result set is too large, lower `depth` or tighten `tagged`.

### `refresh() -> WriteResult`

Triggers a fresh corpus walk: the walker re-globs `**/*.md`, re-parses frontmatter, rebuilds the in-memory graph, repopulates the FTS5 virtual table, recomputes MinHash signatures, re-emits all edges.

No parameters. The walk runs against the corpus rooted at the server's CWD.

Returns a `WriteResult` with `path` set to the corpus root. The `warnings` list surfaces non-fatal advisories — frontmatter parse failures, unparseable wikilinks, documents missing mandatory fields.

Day one this is the only way to pick up file changes between queries. Agents that write `.md` files call `refresh` afterward to make the new content visible. Human edits in Obsidian show up after the next reindex call. See [[docs/hoplite/hoplite-architecture.md#the-walker]] for the walk's two-pass shape.

### `export(path=None) -> WriteResult`

Snapshots the in-memory graph state to a SQLite file for SQL-level debugging.

Parameters:

- `path` (optional, string) — destination file path. Default: `.hoplite/<ISO-timestamp>.index.sqlite` relative to the corpus root, where the timestamp is UTC `YYYY-MM-DDTHH-MM-SS` (colons replaced with dashes for Windows compatibility). Each dump produces a uniquely-named file; prior snapshots stay on disk for comparison.

One-shot operation. The schema is a byte-for-byte mirror of in-memory state — `document`, `document_property`, `edge`, `edge_property`, plus an FTS5 index over `path`, `title`, `summary`, and `body` replayed from the live FTS connection. Full DDL in [[docs/hoplite/hoplite-architecture.md#dump-schema]].

Returns a `WriteResult` with `path` set to the absolute path of the written file and `counts` populated with row counts per entity (`{"documents": N, "ghosts": G, "edges": K}`).

Then `sqlite3 .hoplite/<file>` gives developers a full SQL surface over the derived state — useful for diagnosing "why didn't this query return that document" cases.

## Error handling at the MCP boundary

Per [[docs/hoplite/hoplite-architecture.md#error-model]], invariant violations throw exceptions (programming errors the caller could have prevented — `None` for a required string, malformed predicate); constraint violations ride along inside successful results as warnings (frontmatter parse failures, unwritable dump destinations).

At the MCP wire boundary, thrown invariant exceptions surface as structured error content with `isError: true`. Constraint warnings ride inside the `warnings` field of `WriteResult` or the analogous shape on `refresh` and `export` results. JSON-RPC protocol-level errors stay reserved for transport-level failures; tool-execution errors always come back as content the agent can read.
