---
title: server.py — MCP wiring with zero startup work
summary: "`server.py` constructs the FastMCP app, calls `tools.set_root(Path.cwd())` to compute the DB path and stash a `FileDatabase` singleton, and registers the four tool handlers. No connection opens, no schema applies, no walk runs at import. First `refresh()` call is the bootstrap; queries before refresh return an actionable error."
tags: [note, sqlite, design, mcp]
created: 2026-05-28
status: design
---

# server.py — MCP wiring with zero startup work

`server.py` constructs the FastMCP app, calls `tools.set_root(Path.cwd())` to compute the DB path and stash a `FileDatabase` singleton, and registers the four tool handlers. No connection opens, no schema applies, no walk runs at import. First `refresh()` call is the bootstrap; queries before refresh return an actionable error.

Sibling design notes: [[docs/todos/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale; [[docs/todos/db-refactor.md]] for the broader plan; [[docs/notes/tools-py-design.md]] (the handlers this wires up) and [[docs/notes/db-py-design.md]] (the `FileDatabase` constructed here) for collaborating modules. This note covers `server.py` alone.

## The startup-does-nothing decision

Today's `server.py` calls `tools.set_root(Path.cwd())` at import time, which assigns module-level path globals. The next tool call lazily builds the in-memory `Graph` via `walk()` — that's the ~50-second cold start.

The new shape keeps the same import-time `set_root` call. What changes is what `set_root` does: it computes the DB path and constructs a `FileDatabase`. No connection opens. No file is created. No walk runs. The MCP server is ready to serve requests in milliseconds.

`server.py` constructs only the `FileDatabase`; `tools._build_graph` builds the per-call `Graph(db, corpus_root)` (see [[docs/notes/graph-py-design.md]] and [[docs/notes/tools-py-design.md]]). There is one `Graph` implementation — SQLite-backed — so there is nothing to select; `server.py` names neither a connection type beyond `FileDatabase` nor the graph class.

Concrete consequences:

- N MCP processes start, all do nothing. No race window at import. The race only exists when two processes both call `refresh()` at the same time, and `BEGIN IMMEDIATE` serializes that cleanly per [[docs/notes/db-py-design.md]].
- Per-window cold start is zero. The cost of loading the corpus from scratch every session scaled linearly with corpus size and was the main reason this refactor exists. It disappears for every window after the first.
- Query tools before any refresh fail loudly. `where`/`relatives`/`export` open the file with `mode=ro&immutable=0`; if it doesn't exist, `FileDatabase.open_ro` raises `IndexNotFoundError`, which `tools.py` translates to a `ValueError("no Hoplite index at ...; call refresh to build it")`. The user sees an actionable message, not a silent empty result.
- `refresh()` is the bootstrap. First refresh creates the DB file via `FileDatabase.open_rw` (create-if-missing), `migrations.apply` lays down the schema, the walker populates everything. Subsequent refreshes follow the same path; the file is already there, migration is a no-op, the walker truncates and repopulates.

The main win: a developer with 12 Claude Code windows open against the same corpus pays the walk cost once. Every other window opens the shared DB file, sees data already there, and serves queries immediately.

## Module shape

The new `server.py` differs from today's only in what `tools.set_root` does internally. The body of `server.py` is essentially unchanged:

```python
import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from hoplite import tools

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[hoplite-server] %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP("catalog")

tools.set_root(Path.cwd())
logger.info("starting; corpus root = %s", Path.cwd() / "docs")


mcp.tool(name="where", annotations=ToolAnnotations(...))(tools.match_nodes)
mcp.tool(name="relatives", annotations=ToolAnnotations(...))(tools.traverse_nodes)
mcp.tool(name="refresh", annotations=ToolAnnotations(...))(tools.reindex)
mcp.tool(name="export", annotations=ToolAnnotations(...))(tools.dump_index)


if __name__ == "__main__":
    mcp.run()
```

The `ToolAnnotations` blocks stay byte-for-byte: same titles, same hints (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`). The MCP wire schema is unchanged.

The `logger.info("starting; corpus root = ...")` line stays useful — it confirms the server picked up the right corpus root at start.

## What `set_root` does (cross-reference)

This is `tools.py`'s domain, restated here so the server.py reader doesn't have to chase the cross-reference:

```python
def set_root(cwd: Path) -> None:
    global _database, _corpus_root, _hoplite_root
    _corpus_root = cwd / "docs"
    _hoplite_root = cwd / ".hoplite"
    db_path = _hoplite_root / "hoplite.schema.001.sqlite"
    _database = FileDatabase(db_path)
```

Four assignments, no I/O. `FileDatabase(db_path)` stashes the path on a struct; it does not open the file or create the parent directory. The parent directory is created on first `open_rw` (the walker's path) — see [[docs/notes/db-py-design.md]]'s `open_rw` description.

## Schema version in the filename

The DB file path is `<cwd>/.hoplite/hoplite.schema.001.sqlite`. The `001` is the schema version.

This enables cross-version coexistence. When the schema bumps to v2, the new code computes the path as `hoplite.schema.002.sqlite` and creates a fresh file. The v1 file stays on disk; v1 processes opening that file continue to serve. Two MCP server versions can coexist on the same corpus without stomping on each other's data.

Cost: data does not migrate from v1 to v2. The first refresh on v2 rebuilds the graph from the corpus (the source of truth). This is acceptable at Hoplite's corpus sizes. The walk takes seconds to minutes, and the user only pays it once per version bump.

Migration tooling (`migrate_v001_to_v002(src_conn, dst_conn)`) is out of scope until a real schema change forces the conversation. See [[docs/notes/migrations-py-design.md]] "Future migrations."

## Concurrency model

This ties together what [[docs/notes/db-py-design.md]] and [[docs/notes/tools-py-design.md]] state:

- N server processes start concurrently. Each calls `tools.set_root` at import; each holds its own `FileDatabase` instance pointing at the same file path. No file I/O yet.
- Process A's `refresh()` call wins the `BEGIN IMMEDIATE` writer lock first. Processes B–N's concurrent `refresh()` calls block; SQLite serializes them.
- Each waiting process re-checks the schema and rewalks the corpus. The second walk overwrites the first's results (truncate-and-rebuild), which is wasteful but not corrupting.
- Once any process completes a refresh, every process's subsequent `where`/`relatives` queries see the latest committed snapshot via WAL. Readers never block on writers; concurrent reads don't block each other either.
- A process that calls `where` before any process has run `refresh` gets `IndexNotFoundError` translated to `ValueError`. The user runs `refresh` from one process; subsequent reads from all processes succeed.

## Tests

`server.py` has no business logic worth testing in isolation. It wires modules together. The shape is verified by:

1. **`tools.set_root` tests** (in `test_tools.py` per [[docs/notes/tools-py-design.md]]) — verify the singleton is constructed correctly.
2. **MCP integration test** (in `test_smoke.py` or a new `test_server.py`) — start the server in a subprocess, send a `refresh` request, then a `where` request, verify the responses match the wire schema. Already covered by the existing smoke test against today's `server.py`; the port is to ensure the new wiring produces the same responses.
3. **Manual sanity check during step 10 cutover** — start the actual MCP server, run `refresh` from one Claude Code window, run `where` from another window pointing at the same corpus, verify the second window sees the freshly-built index without paying any walk cost.

No new test bullets specific to `server.py`. If the integration test passes and `tools.py`'s test suite passes, `server.py` is correct.

## Risks for the implementer

### Hard rules — don't violate these

- Don't open the DB at import. No `db.open_rw()`, no `migrations.apply()`, no walk. The point is that startup is free. If you want to "pre-warm" the connection or "verify the schema is current" at server boot, you're undoing the concurrency model.
- Don't move `set_root` into a function called by the first handler. Calling it at import time is correct. Every handler needs the singletons, and import is the right time to compute them. Lazy initialization buys nothing here because import is fast.
- Don't add an `init` MCP tool. `refresh` is the init. A separate `init` gives users a second thing to remember to call, and adds a code path that does what `refresh` already does.

### Known gaps — accepted, documented, not yet fixed

- First refresh against an existing v1 file when the v2 server starts. The new server opens `hoplite.schema.002.sqlite`, which doesn't exist, and creates a fresh v2 file. The v1 file stays on disk; the user pays a fresh walk on v2's first refresh. This is by design, but worth flagging in release notes.
- Server crash during a refresh. `BEGIN IMMEDIATE` rollback unwinds the partial walk, so the DB stays in its prior state. A surviving process picks up where the dead one left off, on its own next `refresh` call. No corruption, no "stuck lock" state; SQLite's WAL handles this via the journal.

### Future considerations — forward-pointers

- Connection pooling lands behind the `Database` interface (see [[docs/todos/db-refactor.md]] "Connection pooling vs locking"). `server.py` doesn't change; `tools.set_root` would construct `PooledDatabase` instead of `FileDatabase`.
- Schema migration tooling lands next to `migrations.py` when a real schema change forces it. `server.py` is unaffected.
- Health endpoint. If FastMCP grows a "is the server alive" probe, it should not trigger a refresh. The probe should answer "yes, registered, ready to receive a `refresh` call." Today's MCP protocol doesn't have one; if it lands, this is the design hook.

### Editorial

- Server module name stays `server.py`. Don't rename. The `mcp.run()` entry point is the contract MCP discovery expects.
- `mcp = FastMCP("catalog")`: "catalog" is the public MCP server name, exposed to clients as the tool group. Don't rename casually; it's user-visible.
