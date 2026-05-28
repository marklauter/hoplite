---
title: migrations.py — schema lifecycle
summary: `migrations.py` owns the schema-apply path. `apply(conn)` checks `sqlite_master` for the `document` table; if absent, runs the full schema script. Idempotent, race-tolerant, no in-place migrations day-one — schema versioning is carried in the filename, not in the database header.
tags: [note, sqlite, design, hoplite, architecture]
created: 2026-05-27
document.status: design
---

# migrations.py — schema lifecycle

`migrations.py` owns the schema-apply path. `apply(conn)` checks `sqlite_master` for the `document` table; if absent, runs the full schema script. Idempotent, race-tolerant, no in-place migrations day-one — schema versioning is carried in the filename, not in the database header.

Sibling design notes: [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale and trigger; [[docs/notes/db-refactor.md]] for the broader refactor plan; [[docs/notes/db-py-design.md]] for the `Database` interface this collaborates with. This note covers `migrations.py` alone.

## Public API

One function, one constant, one private helper:

```python
def apply(conn: sqlite3.Connection) -> None: ...

SCHEMA: Final[str]  # full DDL, loaded from schema.sql at module import
```

`apply` is the only entry point callers use. `SCHEMA` is exposed because the dump path in `graph.py` (during the transition period before cutover) and any future debug tooling may want the canonical DDL string. After cutover, `SCHEMA` can be made module-private if no consumer remains.

## Schema source

The canonical DDL lives at `plugins/hoplite/mcp/src/hoplite/schema.sql`. `migrations.py` loads it at import time:

```python
SCHEMA: Final = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
```

This duplicates the load that `graph.py` already does (also reading from the same file). Both modules holding their own copy is fine — they load from one file, can't drift between reads, and graph.py is on a deprecation path. Once `graph.py` is removed (step 10 of the refactor), `migrations.py` becomes the only owner.

## Idempotency strategy

The presence check uses `sqlite_master`:

```python
row = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='document'"
).fetchone()
```

If `document` exists, the schema is "already applied" — no-op. If it doesn't, run `executescript(SCHEMA)`. The `document` table is the canonical marker because every other persisted table references it; if `document` is present and the others aren't, the DB is corrupt and a different recovery path is needed (not migrations's job).

We do **not** use `CREATE TABLE IF NOT EXISTS` in the schema script. Reasons:

- It would silently mask a partial-schema corruption case (some tables present, others not), turning a clear "table already exists" error into invisible damage.
- The filename-versioning scheme means we never need to ADD a table to an existing v001 database — a schema change means a new file. So the only races we handle are "two processes apply v001 from empty," which the explicit check + race handling below covers cleanly.

## Transaction shape and the `executescript` gotcha

Python's `sqlite3.Connection.executescript` has a documented surprise: under autocommit mode (`isolation_level=None`), it issues an implicit `COMMIT` of any pending transaction before running the script. That means **`apply` cannot be safely wrapped inside an outer `write_transaction`** — the outer `BEGIN IMMEDIATE` would commit prematurely the moment `executescript` runs.

Implication: `apply` is called *outside* `write_transaction`. The refresh flow becomes:

```python
def refresh():
    with db.open_rw() as conn:
        migrations.apply(conn)          # outside any explicit transaction
        with db.write_transaction(conn):
            walk(corpus_root, conn)     # the actual ingest, atomic
```

`apply` runs first, in autocommit. `executescript` handles its own transactional unit internally. Then `write_transaction` wraps the walk.

### Race handling

Two processes calling `refresh` on a fresh corpus might both observe "no document table" and both call `executescript`. SQLite serializes the writes, so the second one fails with `OperationalError: table document already exists`. We treat this as a benign race — the schema *is* present after the failure; we just weren't the one who created it.

```python
def apply(conn: sqlite3.Connection) -> None:
    if _schema_present(conn):
        return
    try:
        conn.executescript(SCHEMA)
    except sqlite3.OperationalError:
        # Race: another process applied the schema between our check and
        # executescript. Re-check; if the schema is now present, the race
        # resolved itself in our favor. Otherwise the error is real.
        if not _schema_present(conn):
            raise
```

This pattern is honest — the outer `OperationalError` is only swallowed when we can prove the desired state was reached anyway. Any other error (disk full, permission denied, etc.) raises.

## Future migrations

Day-one has one schema: `hoplite.schema.001.sqlite`. The filename carries the version. When v2 lands:

- A new file `hoplite.schema.002.sqlite` is created when an MCP process on the v2 codebase calls `refresh`.
- The v1 file stays on disk until manually deleted; v1 MCP processes can keep using it.
- No in-place ALTER, no down migrations, no schema_version table.

This sidesteps the entire class of "running migration N at startup" bugs. The cost is data: a fresh `refresh` rebuilds the whole graph from the corpus rather than incrementally moving rows over. At Hoplite's corpus sizes that's acceptable (seconds to minutes).

When this becomes painful — corpus too large to rewalk on each schema bump — write a one-shot `migrate_v001_to_v002(src_conn, dst_conn)` script that lives next to `apply` in `migrations.py`. It's not part of the runtime path.

## Module skeleton

```python
import sqlite3
from pathlib import Path
from typing import Final


SCHEMA: Final = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")


def apply(conn: sqlite3.Connection) -> None:
    """Apply the schema to `conn` if not already present. Idempotent.

    Must be called outside any explicit transaction — `executescript`
    implicitly commits the current transaction in autocommit mode, which
    would prematurely close any outer `write_transaction`.

    Race-tolerant: if another process applies the schema between our
    presence check and our executescript, the resulting OperationalError
    is swallowed only if the post-error state shows the schema present.
    """
    if _schema_present(conn):
        return
    try:
        conn.executescript(SCHEMA)
    except sqlite3.OperationalError:
        if not _schema_present(conn):
            raise


def _schema_present(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='document'"
    ).fetchone()
    return row is not None
```

## Tests

All tests use `:memory:` connections constructed directly — `migrations.py` doesn't need `FileDatabase` to exercise. Full annotations, `pytest.raises(Exc, match=...)` for error cases.

1. `test_apply_creates_all_expected_tables` — fresh `:memory:` connection; call `apply`; introspect `sqlite_master` for every expected table (`document`, `document_property`, `edge`, `edge_property`, `fts`) and every index (`idx_document_path`, `idx_document_property_key_value`, `idx_edge_kind_src`, `idx_edge_kind_dst`, `idx_edge_property_key_value`).
2. `test_apply_is_idempotent` — call `apply` twice; second call returns without raising; table list unchanged between calls.
3. `test_apply_no_op_when_document_exists` — manually `CREATE TABLE document (id INTEGER)` (deliberately wrong shape) then call `apply`; the function returns without touching the existing table. Proves the presence check is the gate.
4. `test_apply_race_recovery_succeeds_when_schema_present` — monkeypatch `executescript` to raise `OperationalError("table document already exists")`, but pre-create the `document` table via a separate path so `_schema_present` returns True after the raise. Assert `apply` returns normally.
5. `test_apply_race_recovery_reraises_when_schema_absent` — same monkeypatch shape, but no pre-created `document` table. Assert the original `OperationalError` propagates.
6. `test_schema_constant_matches_file` — assert `SCHEMA` equals the contents of `schema.sql` on disk. Catches the case where someone hard-codes the constant in the module and forgets to load.

Test #4 and #5 verify the race-handling contract specifically — they're the load-bearing tests for the one piece of subtle logic in the module.

## Risks for the implementer

- **`executescript` and autocommit interaction.** The docstring on `apply` calls this out explicitly; the test suite doesn't catch it (because `:memory:` tests don't exercise the outer `write_transaction` boundary). The integration test that catches it lands in step 5 (walker) when `refresh` is wired up.
- **`OperationalError` over-broad catch.** The race-recovery `except` clause is intentionally narrow — it only swallows the error if the post-state shows success. Don't broaden it. If a future implementer wants to log the "race resolved itself" case, that's fine; just don't drop the `_schema_present` re-check.
- **Module-level SCHEMA load.** Reading `schema.sql` at import time means the file must ship with the package. `pyproject.toml` already declares `[tool.setuptools.package-data] hoplite = ["schema.sql"]` from the schema-extraction work earlier. Don't undo that.
