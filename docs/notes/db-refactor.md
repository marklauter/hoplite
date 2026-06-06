---
title: Hoplite DB refactor — file-based SQLite execution plan
summary: Numbered plan to replace the in-memory dict-backed graph with a persistent file-based SQLite store (WAL, shared across MCP processes). The in-memory graph is retired — SQLite is the only implementation. A single `Graph` class in `graph.py` runs SQL against the `node`/`edge`/`edge_kind`/`fts` schema; traversal is a recursive CTE.
tags: [note, todo, sqlite, hoplite, architecture]
created: 2026-05-27
document:
  priority: high
  effort: high
  status: in-progress
---

# Hoplite DB refactor — file-based SQLite execution plan

Numbered plan to replace the in-memory dict-backed graph with a persistent file-based SQLite store (WAL, shared across MCP processes). The in-memory graph is **retired** — there is no Protocol and no two-implementation peer; SQLite is the only store. A single `Graph` class in `graph.py` opens a connection per call through an injected `Database`, runs SQL against the `node`/`edge`/`edge_kind`/`fts` schema, and projects rows to the domain dataclasses.

See [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the *why* and the trigger that fired this work. This note is the *how*.

## Decisions captured

These are settled. Revisit only with cause.

- **One store, one `Graph`.** The in-memory dict-backed graph is retired. `Graph` (in `graph.py`) is the single implementation, backed by file SQLite. No `typing.Protocol`, no `InMemoryGraph`/`SqliteGraph` split, no parity oracle. Design at [[docs/notes/graph-py-design.md]].
- **Schema source.** The canonical DDL lives at `plugins/hoplite/mcp/src/hoplite/schema.sql`. Loaded once at import as `SCHEMA`. Current shape: `node`/`node_property`, `edge` with an interned `edge_kind` FK, `edge_property`, and the `fts` virtual table. `node.uri`, `node_property.key`, and `edge_kind.kind` carry `COLLATE NOCASE`.
- **Case-insensitivity is the column's job.** `node.uri COLLATE NOCASE` makes `WHERE uri = ?` case-insensitive. The old "casefold paths on store, casefold the input on resolve" contract is **deleted** everywhere — no casefold-on-store. The walker writes URIs verbatim.
- **Migrations split from connection.** `db.py` owns connection lifecycle and PRAGMAs only; `migrations.py` owns schema lifecycle. They collaborate at one call site (`refresh`) but don't share a file. Connection-open is stable and barely changes; schema apply grows as real migrations arrive.
- **DB file path.** `.hoplite/hoplite.schema.001.sqlite` at the corpus root. Schema version embedded in the filename; bumping it creates a new file alongside, so processes on different schema versions never trample each other. No `PRAGMA user_version`.
- **Server startup does nothing.** The MCP server boots with no DB I/O — no file creation, no schema apply, no walk. The first manual `refresh()` is the bootstrap: opens the file read-write-create, applies the schema if tables are missing, runs the walk. One bootstrap path; no startup race; no per-window cold start.
- **Connection per tool call, behind an interface.** Handlers don't open connections directly — they call methods on a `Database` interface that returns context-manager-wrapped connections. `FileDatabase` opens a fresh connection per call and closes on exit; no pool, no shared state, no lock. Per-call open is cheap under WAL. Pooling is a future swap-in behind the same interface (see "Held for future").
- **Query tools fail loud if the index is missing.** `where`/`relatives`/`export` open read-only (`file:<path>?mode=ro`). Missing file → explicit "no index — call `refresh` first" error, not a silent empty result.
- **Refresh semantics.** Day-one stays *truncate and rebuild*. Reconcile (added/changed/removed via `content_hash` + mtime) is future work.
- **PRAGMAs.** WAL is persistent per-database; foreign-key enforcement, sync mode, temp store, and mmap size are per-connection and set on every open. See the PRAGMA reference below.
- **Traversal is a recursive CTE.** `relatives` walks the `edge` table with a recursive CTE that handles depth-bounding, cycle-safety, `edge_kind` filtering, direction, the `top_k_related` cap, and shortest-distance-per-node in one query. The window functions (`top_k_related` ranking, shortest-path dedupe) live in the non-recursive CTEs; the recursive term only walks. Detail at [[docs/notes/graph-py-design.md]].
- **Tests use `:memory:`.** Fixtures bootstrap a `:memory:` connection with the same schema, populate via the walker, exercise the methods. The one exception is `open_ro` URI behavior, which needs a real file.
- **`tools.py` depends on `Graph` directly.** Handlers construct `Graph(db, corpus_root)` per call and delegate. Search/traverse logic that lived in `tools.py` (BFS, `_neighbors`, FTS query, escape) moves onto `Graph`; the handler bodies shrink to predicate parsing plus a single `graph.search(...)` / `graph.traverse(...)` call.
- **No `hoplite init` step.** `refresh` is the init step.

## Schema/model vocabulary drift — open reconcile

`schema.sql` has moved to `node`/`uri`/`edge_kind`, but `models.py` and `row_factories.py` still use `Document`/`path`. The queries in [[docs/notes/graph-py-design.md]] bridge it by projecting `n.uri AS path`, so the landed factories keep working unchanged. This is a deliberate, contained drift. A later pass either renames the models (`Document` → `Node`, `path` → `uri`) to match the schema and the "addressable byte resource / medium-agnostic identity" framing in `docs/hoplite/hoplite-architecture.md`, or accepts the `AS path` alias as permanent. Not resolved in this refactor; flagged so it isn't forgotten.

## Numbered steps

Work in this order. Each step is shippable on its own — tests pass.

1. **`db.py` — `Database` interface + `FileDatabase` impl.** Design at [[docs/notes/db-py-design.md]]. **Done 2026-05-27** — landed with passing tests covering pragmas, URI handling, parent-dir auto-create, both domain errors, the `write_transaction` commit/rollback/busy paths, and (added later) crash-orphaned-WAL recovery under a read-only connection.

2. **`migrations.py` — schema lifecycle.** Design at [[docs/notes/migrations-py-design.md]]. **Done 2026-05-27** — landed with tests covering the four-quadrant race matrix (error-text match × schema-present), partial-schema detection, and schema-constant integrity. (The expected-table list needs updating to the current `node`/`edge_kind` schema — see the note.)

3. **Row factories.** Design at [[docs/notes/row-factories-py-design.md]]. **Done 2026-05-28** — landed with tests covering the projection contracts, the compose-on-base invariants, the `via_edges` mutability copy, and the miswritten-alias gap pin. (Targets the `Document`/`path` vocabulary; SQL writers project `n.uri AS path` to match.)

4. **The `Graph` class in `graph.py`.** Design at [[docs/notes/graph-py-design.md]]. Replace the in-memory container with a single SQLite-backed `Graph(db, corpus_root)`. Move `search`/`traverse`/`_escape_fts5_query` off `tools.py` onto `Graph`; implement `traverse` as the recursive CTE; implement `refresh` (delegates to the walker) and `export` (online backup). The old `walk` free function and `dump_index` writers leave `graph.py`.

5. **Walker against the DB.** Design at [[docs/notes/walker-py-design.md]].

6. **Tool surface rewrite.** Design at [[docs/notes/tools-py-design.md]].

7. **Server bootstrap — do nothing.** Design at [[docs/notes/server-py-design.md]].

8. **Tests migrate to `:memory:`.**
   - Port fixtures one file at a time: open a `:memory:` connection, run the walker against a small corpus, exercise the handlers (which delegate to `Graph`).
   - The existing tests are the behavioral oracle for the rewrite — `Graph` should reproduce today's observable `where`/`relatives` results.

9. **Correctness check on the real corpus.**
   - Run `search` and `traverse` against the existing corpus; assert results match the documented contracts (tag-sort ascending, `(distance, path)` order, `related` tie-break `(confidence desc, target asc)`, unresolved-origin `ValueError`, origin excluded). This stays in the suite as a regression guard.

10. **Wire `Graph` in `server.py`.**
   - `server.py` (via `tools.set_root`) constructs `FileDatabase(<path>)`; each handler builds `Graph(db, corpus_root)` per call (see [[docs/notes/server-py-design.md]] and [[docs/notes/tools-py-design.md]]).

## PRAGMA reference

For the connection-open sequence in step 1:

| PRAGMA | Scope | Why |
|---|---|---|
| `journal_mode = WAL` | per-database, persistent | Many-readers-one-writer concurrency. Set once; sticks. |
| `foreign_keys = ON` | per-connection | Enables FK enforcement. Off by default. Without it, `REFERENCES` is decorative. |
| `synchronous = NORMAL` | per-connection | Fewer fsyncs than `FULL`; durable under WAL. |
| `temp_store = MEMORY` | per-connection | Sort buffers and temp tables in RAM. |
| `mmap_size = 268435456` | per-connection | 256 MiB memory-mapped I/O; reads bypass `read()`. |

`cache_size` left at the default 2000 pages (~8 MiB per connection).

## Held for future

Explicitly *not* in scope. Captured so they aren't forgotten.

- **Reconcile semantics.** Replace truncate-and-rebuild with a three-set diff against the filesystem: added (insert), removed (cascade-delete), changed (`content_hash` differs → re-extract). Cheap mtime check first. Unlocks incremental reindex.
- **Schema migration tooling.** Filename-versioning sidesteps in-place migration. When a real schema change ships, a one-shot `migrate_v001_to_v002` copies rows with the new shape instead of a full re-walk.
- **Model/schema vocabulary reconcile.** Rename `Document`/`path` to `Node`/`uri`, or bless the `n.uri AS path` alias permanently (see drift section above).
- **Connection pooling vs locking.** Day-one is connection-per-call behind the `Database` interface. If open/pragma overhead proves meaningful under concurrent load:
  - **Lock around a single shared connection** — simplest, but defeats WAL: concurrent reads serialize, the N-readers win disappears. Only right if concurrency is genuinely low.
  - **Small connection pool** — more code (lifecycle, max size, wait queue, maybe split ro/rw pools), but preserves WAL's N-readers model. Each pooled connection costs page-cache RAM.
  - **Pool is the right direction** when the bottleneck is real. Either swap-in lands behind the existing `Database` interface — no handler or refresh-path changes.

## Open questions to resolve as we go

- **DAO organization.** Keep query SQL in `graph.py`, or split a `dao.py` if it grows past ~300 lines? Lean: one file; split on size.
- **Walk transaction granularity.** One big transaction for the whole walk (atomic) vs per-pass (concurrent reads see partial progress). Lean: one big transaction.
- **Test fixture shape.** A `:memory:` helper taking `(uri, frontmatter, body)` tuples and populating the DB.
