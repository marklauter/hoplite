---
title: Hoplite DB refactor — file-based SQLite execution plan
summary: Numbered plan to move Hoplite from in-memory dicts plus `:memory:` FTS to a persistent file-based SQLite store with WAL, shared across MCP processes. The old `graph.py` stays in tree as the reference implementation; new code lands in `graph_sqlite.py` alongside.
tags: [note, todo, sqlite, hoplite, architecture]
created: 2026-05-27
document.priority: high
document.effort: high
document.status: in-progress
---

# Hoplite DB refactor — file-based SQLite execution plan

Numbered plan to move Hoplite from in-memory dicts plus `:memory:` FTS to a persistent file-based SQLite store with WAL, shared across MCP processes. The old `graph.py` stays in tree as the reference implementation; new code lands in `graph_sqlite.py` alongside.

See [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the *why* and the trigger that fired this work. This note is the *how*.

## Decisions captured

These are settled. Revisit only with cause.

- **Schema source.** The canonical DDL lives at `plugins/hoplite/mcp/src/hoplite/schema.sql`. Loaded once at module import as `SCHEMA`. Used by both the live DB and any debug export.
- **Migrations split from connection.** `db.py` owns connection lifecycle and PRAGMAs only; `migrations.py` owns schema lifecycle. The two collaborate at one call site (`refresh`) but don't share a file. Connection-open is stable and barely changes; schema apply will grow as real migrations arrive. Mirrors the Kingo C# split (`SqliteConnectionFactory.cs` vs `Migrations.cs`) by the same reasoning.
- **DB file path.** `.hoplite/hoplite.schema.001.sqlite` at the corpus root. Schema version embedded in the filename; bumping the version creates a new file alongside, so multiple MCP processes on different schema versions never trample each other. No `PRAGMA user_version` — the filename is the version marker.
- **Server startup does nothing.** The MCP server boots with no DB I/O — no file creation, no schema apply, no walk. The first manual `refresh()` call is the bootstrap: opens the file with `Mode=ReadWriteCreate`, applies the schema if tables are missing, runs the walk. Every subsequent `refresh()` runs the same path. One bootstrap path, not two; no startup race, no per-window cold start; processes that never call `refresh` never pay any cost.
- **Connection per tool call, behind an interface.** Tool handlers don't open connections directly — they call methods on a `Database` interface that returns context-manager-wrapped connections. The day-one implementation (`FileDatabase`) opens a fresh connection per call and closes on exit; no pool, no shared state, no lock. A shared connection would chokepoint concurrent requests (one transaction per connection) and would crash outright under FastMCP's concurrent handler model (stdlib `sqlite3` defaults to `check_same_thread=True`). Per-call open is cheap under WAL: pragma application is microseconds, `mmap_size = 256MB` keeps most reads in the OS page cache across connection close. Pooling is a future swap-in behind the same interface — see "Held for future" below.
- **Query tools fail loud if the index is missing.** `where`/`relatives`/`export` open the DB in read-only mode (`file:<path>?mode=ro` URI). If the file doesn't exist or the schema is absent, surface an explicit "no index — call `refresh` first" error rather than silently returning empty. Empty results from a missing index look identical to empty results from a real query; the failure mode would be invisible. Loud is right.
- **Refresh semantics.** Day-one stays *truncate and rebuild*, same as today. Reconcile (added/changed/removed via `content_hash` + mtime) is future work — held aside, mentioned at the bottom.
- **PRAGMAs.** WAL is persistent per-database; foreign-key enforcement, sync mode, temp store, and mmap size are per-connection and must be set on every open. See section below.
- **Tests use `:memory:`.** Not temp directories. Fixtures bootstrap a `:memory:` connection with the same schema, populate via the walker, exercise the DAO. Faster, more deterministic, no filesystem cleanup.
- **`graph.py` stays.** New code in `graph_sqlite.py`. The old in-memory implementation is the reference for parity checks throughout the refactor. Deprecation is a separate decision after parity is confirmed.
- **Module naming.** Python module names cannot contain `.` (it's the package separator). `graph_sqlite.py` is the correct file name — imported as `hoplite.graph_sqlite`.
- **No `hoplite init` step.** `refresh` is the init step — same path users already invoke. Adding a separate init command duplicates code and gives users a second thing to remember.

## Numbered steps

Work in this order. Each step is shippable on its own — tests pass, parity preserved against `graph.py`.

1. **`db.py` — `Database` interface + `FileDatabase` impl.**
   - `Database` is a `typing.Protocol` (or `ABC`) with two methods, both context managers that yield a fresh connection per call:
     - `open_rw(self) -> ContextManager[sqlite3.Connection]` — write path. Used only by `refresh`.
     - `open_ro(self) -> ContextManager[sqlite3.Connection]` — read path. Used by every query tool.
   - Neither method knows anything about the schema; that's `migrations.py`'s job.
   - `FileDatabase(path: Path)` is the day-one implementation. `open_rw` creates-if-missing, applies rw PRAGMAs, sets `row_factory = sqlite3.Row`, yields, closes. `open_ro` opens with `file:<path>?mode=ro&immutable=0` URI (errors cleanly if the file doesn't exist), applies ro PRAGMAs, yields, closes.
   - Caller shape: `with db.open_ro() as conn: rows = conn.execute(...).fetchall()`. Connection lifetime equals the `with`-block lifetime; no caching, no sharing.
   - PRAGMA order on rw: `journal_mode = WAL` (no-op if already WAL — idempotent and cheap, no separate flag needed), `foreign_keys = ON`, `synchronous = NORMAL`, `temp_store = MEMORY`, `mmap_size = 268435456` (256 MiB).
   - ro pragmas: `foreign_keys = ON`, `temp_store = MEMORY`, `mmap_size = 268435456`. (FK enforcement is harmless on a read-only connection but keeps `EXPLAIN QUERY PLAN` honest.)
   - The interface is the seam: a future `PooledDatabase` slots in by satisfying `Database` with no changes to tool handlers or `refresh`.
   - Unit tests against `:memory:` for `FileDatabase.open_rw`: pragmas set, two sequential `with` blocks produce independent connections, both see the same data after the first commits. `open_ro` tests need a real temp file (URI semantics aren't available on `:memory:`) — one acceptable exception to the "tests use `:memory:`" rule.

2. **`migrations.py` — schema lifecycle.**
   - `apply(conn: sqlite3.Connection) -> None`. Checks `sqlite_master` for the `document` table. If absent, runs `executescript(SCHEMA)` inside `BEGIN IMMEDIATE` so concurrent first-refreshes serialize cleanly. If present, no-op.
   - No version detection day-one beyond "table exists yes/no." The filename carries the schema version; cross-version migration is future work that lives here when it lands.
   - Unit tests against `:memory:`: applying twice is idempotent; applying to a fresh connection creates every expected table and index (introspect `sqlite_master`).

3. **Row factories.**
   - A small `row_factories.py` module: `_row_to_document`, `_row_to_edge`, `_row_to_hit`, `_row_to_traversal_hit`. Each takes a `sqlite3.Row` and returns the matching dataclass from `models.py`.
   - Explicit per-field projection (Pattern A from the earlier discussion). When the schema changes, `KeyError` surfaces immediately under test.

4. **`graph_sqlite.py` — new Graph class.**
   - `class Graph` holding a `sqlite3.Connection`. Same external surface as today's `Graph` (the methods `tools.py` and the walker call), but every method runs a SQL query through the connection instead of touching a Python dict.
   - Methods to port, in order:
     - `resolve_wikilink(target)` — lookup against `document.path`, alias property rows, casefolded lookup. SQL: `SELECT id, path FROM document WHERE path = ? OR path = ? COLLATE NOCASE` plus a property-row lookup for aliases.
     - `out_edges_for(doc_id, kind)`, `in_edges_for(doc_id, kind)` — covered by the indexes we just added.
     - `properties_for(doc_id)` — group rows from `document_property` into the `dict[str, list[str]]` shape.
     - `fts_search(text, limit)` — `SELECT d.path, p.value AS summary, bm25(fts) FROM fts JOIN document d ON d.id = fts.rowid LEFT JOIN document_property p ON p.id = d.id AND p.key = 'summary' WHERE fts MATCH ? ORDER BY bm25 LIMIT ?`.
   - Each method gets a unit test against a populated `:memory:` DB; the test asserts the same output `graph.py` would produce for the same input.

5. **Walker against the DB.**
   - `walk(corpus_root, conn)` in `graph_sqlite.py`. Same two-pass shape as today's walker but writes to SQL inside one transaction. Wraps the whole walk in `BEGIN IMMEDIATE` so concurrent processes block cleanly.
   - Day-one truncate semantics: `DELETE FROM fts; DELETE FROM edge_property; DELETE FROM edge; DELETE FROM document_property; DELETE FROM document;` at the top of `walk`, then re-insert. Order matters because of FK cascade.
   - The `path_to_id` map we already build during the dump becomes the live map during the walk — same code, different consumer.
   - Aggregate pass for `related` edges runs against the populated `document` table; pairwise loop reads MinHash blobs from rows.

6. **Tool surface rewrite.**
   - `where` — runs the FTS query above through the connection, applies the tag predicate via SQL `WHERE EXISTS (SELECT 1 FROM document_property WHERE id = d.id AND key = 'tags' AND value = ?)` clauses. The expression parser can stay in Python; emit it as composed SQL.
   - `relatives` — recursive walk. Either a CTE (`WITH RECURSIVE`) or a Python loop that issues per-depth `SELECT * FROM edge WHERE src IN (...) AND kind IN (...)` queries. Start with the Python loop; CTE is an optimization if the loop is slow at scale.
   - `refresh` — calls the new walker against the live connection. Returns the same `WriteResult` shape.
   - `export` — becomes `conn.backup(target_conn)` or `VACUUM INTO 'path'`. Both produce a byte-for-byte copy of the live DB. Drop the per-table `_write_*` helpers entirely; the new `export` is two lines.

7. **Server bootstrap — do nothing.**
   - `server.py` registers the four tool handlers and returns. No DB connection, no file creation, no walk. The DB path (`<corpus_root>/.hoplite/hoplite.schema.001.sqlite`) is computed once and held as a string; tools open their own connections inside `with db.open_ro(path)` / `with db.open_rw(path)` blocks on every call.
   - First `refresh()` call opens an rw connection, creates schema if missing, walks. Subsequent `refresh()` calls follow the same path — file already there, schema check is a no-op, walk truncates and repopulates. Concurrent refreshes serialize on `BEGIN IMMEDIATE`.
   - First `where`/`relatives`/`export` call before any `refresh` fails with the "no index — call `refresh` first" error. Same shape every subsequent call uses if the file goes missing.
   - Concurrent query tool calls don't block each other under WAL; each gets its own ro connection and sees the last committed snapshot.

8. **Tests migrate to `:memory:`.**
   - Existing `tests/` exercises against temp corpora and an in-memory `Graph`. Port fixtures one file at a time: open a `:memory:` connection, run the walker against a small in-memory corpus, exercise the DAO/tools.
   - The 178 existing tests are the parity oracle. Both `graph.py` and `graph_sqlite.py` should pass them. When both pass, parity is proven.

9. **Parity check on the real corpus.**
   - Run `where` and `relatives` against the existing 68-doc corpus with both implementations; diff results. Any divergence is a bug to fix before declaring done.

10. **Cutover.**
   - Switch `server.py` to import from `graph_sqlite.py`. `graph.py` becomes dead reference code, deleted in a follow-up commit once we trust the new path in real use.

## PRAGMA reference

For the connection-open sequence in step 1:

| PRAGMA | Scope | Why |
|---|---|---|
| `journal_mode = WAL` | per-database, persistent | Many-readers-one-writer concurrency. The whole point. Set once; sticks. |
| `foreign_keys = ON` | per-connection | Enables FK enforcement. Off by default for backward compat. Without it, our `REFERENCES` declarations are decorative. |
| `synchronous = NORMAL` | per-connection | Fewer fsync calls than `FULL`; durable under WAL. Faster. |
| `temp_store = MEMORY` | per-connection | Sort buffers and temp tables stay in RAM, not the tmpdir. |
| `mmap_size = 268435456` | per-connection | 256 MiB of memory-mapped I/O. Reads bypass the read() syscall; OS page cache does the work. |

`cache_size` left at the default 2000 pages (~8 MiB per connection). Tune later if profiling says so.

## Held for future

These are explicitly *not* in this refactor's scope. Capture them so they aren't forgotten.

- **Reconcile semantics.** Replace truncate-and-rebuild with three-set diff against the filesystem: added (insert), removed (cascade-delete), changed (`content_hash` differs → re-extract). Cheap mtime check first, hash on mtime-mismatch. Unlocks incremental reindex.
- **Schema migration tooling.** Filename-versioning sidesteps in-place migration for now. When a real schema change ships, we may want a one-shot `hoplite migrate v001 → v002` that copies rows with the new shape, instead of a full re-walk.
- **`relatives` via recursive CTE.** Drop the Python loop if traversal benchmarks show it as the bottleneck.
- **Connection pooling vs locking — tradeoff on complexity.** Day-one is connection-per-call behind the `Database` interface. If profiling under concurrent load shows that open/pragma overhead is meaningful, two paths exist:
  - **Lock around a single shared connection** — simplest possible code (one connection, one `threading.Lock`, all calls serialize). But it defeats WAL's whole point: concurrent reads block each other, the N-readers concurrency win disappears. Right only if concurrency is genuinely low and locks are rarely contended.
  - **Small connection pool** — more code (lifecycle tracking, max size, wait queue, possibly split pools for ro vs rw). Preserves WAL's N-readers model. Each pooled connection costs page-cache RAM, so size accordingly.
  - **Pool is the right future direction.** WAL was designed for the many-readers case; a global lock throws that away. Reach for the pool when the bottleneck is real.
  - Either swap-in lands behind the existing `Database` interface — no tool-handler or refresh-path changes.

## Open questions to resolve as we go

These need a call when we hit them, not before.

- **DAO organization.** One `db.py` with everything (open, factories, queries), or `db.py` for bootstrap and `dao.py` for query functions? Lean: start in one file; split if it grows past ~300 lines.
- **`relatives` SQL shape.** Python loop versus recursive CTE. Default Python until proven slow.
- **Walk transaction granularity.** One big transaction for the whole walk (atomic, all-or-nothing) versus per-pass transactions (concurrent reads see partial progress). Lean: one big transaction. Walks are short; partial progress isn't useful.
- **Test fixture shape.** A single `db_with_corpus()` fixture parameterized by corpus snippets, or per-test corpus construction. Lean: a small helper that takes a list of `(path, frontmatter, body)` tuples and populates a `:memory:` DB.

## Reference

The C# project at `D:\kingo\kingo\src\Kingo.Storage\Sqlite` is the user's working example of a similar setup. Most relevant: `SqliteConnectionFactory.cs` (connection string with `ForeignKeys = true`, `Mode = ReadWriteCreate`, WAL pragma on first open), `SqliteSequence.N.cs` (retry-with-backoff for concurrent writes — useful pattern if we ever need optimistic concurrency, not day-one). The header/journal versioning machinery in `SqliteDocumentWriter.D.cs` is more than Hoplite needs; ignore it.
