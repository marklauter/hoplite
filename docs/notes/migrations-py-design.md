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

This duplicates the load that `graph.py` already does (also reading from the same file). Both modules holding their own copy is fine — they read from the same source, so any drift window is bounded by process lifetime (a file edit between the two `import` events would diverge them, but no production path triggers that). Graph.py is on a deprecation track; once it's removed in step 10, `migrations.py` becomes the only owner.

The alternative was lazy loading inside `apply` itself — read `schema.sql` only when first called. Rejected because a packaging error that omits `schema.sql` should fail loudly at import time, not silently survive until the first refresh.

## Idempotency strategy

The presence check verifies **every** expected table exists, not just one:

```python
_EXPECTED_TABLES: Final = ("document", "document_property", "edge", "edge_property", "fts")

def _schema_present(conn: sqlite3.Connection) -> bool:
    placeholders = ",".join("?" * len(_EXPECTED_TABLES))
    sql = (
        f"SELECT COUNT(*) FROM sqlite_master "
        f"WHERE type='table' AND name IN ({placeholders})"
    )
    row = conn.execute(sql, _EXPECTED_TABLES).fetchone()
    return row[0] == len(_EXPECTED_TABLES)
```

A single-table marker (e.g., just `document`) would lie about partial-corruption states. If `executescript` crashed after creating `document` but before later tables, the marker would say "present" forever — every subsequent `apply` would no-op on a half-built schema. The multi-table check requires *all* declared tables to exist before treating the schema as applied; a half-built state is correctly seen as "not present" and triggers re-execution, which then surfaces an "already exists" error on the partial tables and aborts loudly.

We do **not** use `CREATE TABLE IF NOT EXISTS` in the schema script. The argument isn't about partial-corruption detection (the multi-table check handles that). The argument is about silent races: `IF NOT EXISTS` turns the "two processes both try to bootstrap" case into a no-op for the loser, with no error signal. The explicit catchable `OperationalError("table … already exists")` lets us prove via re-check that the desired state was reached before swallowing — `IF NOT EXISTS` gives us no error to verify against.

## Transaction shape and the `executescript` gotcha

Python's `sqlite3.Connection.executescript` issues an implicit `COMMIT` of any pending transaction before running the script — this is unconditional in stdlib `sqlite3`, not specific to autocommit mode or any `isolation_level` setting. That means **`apply` cannot be safely wrapped inside an outer `write_transaction`** — any outer `BEGIN IMMEDIATE` is closed prematurely the moment `executescript` runs.

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

Two processes calling `refresh` on a fresh corpus might both observe "no schema" and both call `executescript`. SQLite serializes the writes, so the second one fails with `OperationalError: table <name> already exists`. We treat that *specific* shape as a benign race — the schema is fully present after the failure; we just weren't the one who created it.

```python
def apply(conn: sqlite3.Connection) -> None:
    if _schema_present(conn):
        return
    try:
        conn.executescript(SCHEMA)
    except sqlite3.OperationalError as e:
        # Belt and suspenders. (a) narrow by error text — we only swallow
        # the "already exists" shape, not arbitrary OperationalError. (b)
        # re-check post-state — we only swallow if the full multi-table
        # schema is actually present.
        if "already exists" in str(e) and _schema_present(conn):
            return
        raise
```

Both filters matter. The text match guards against silently absorbing unrelated failures (disk full, permission denied, malformed SQL during a schema edit) that happen to leave *some* tables behind. The post-state re-check guards against the case where the schema script is mid-edit and an `already exists` error fires *without* the full schema present — partial corruption masquerading as a benign race. Only the intersection — "looks like a race AND state proves it" — gets swallowed.

## Future migrations

Day-one has one schema: `hoplite.schema.001.sqlite`. The filename carries the version. When v2 lands:

- A new file `hoplite.schema.002.sqlite` is created when an MCP process on the v2 codebase calls `refresh`.
- The v1 file stays on disk until manually deleted; v1 MCP processes can keep using it.
- No in-place ALTER, no down migrations, no schema_version table.

This sidesteps the entire class of "running migration N at startup" bugs. The cost is data: a fresh `refresh` against v2 rebuilds the whole graph from the corpus rather than copying rows over from v1. v1 and v2 files coexist on disk but there's **no data continuity** between them — the user can't query v2 to see v1's data without an explicit migration step. At Hoplite's corpus sizes a rewalk is acceptable (seconds to minutes).

When this becomes painful — corpus too large to rewalk on each schema bump — write a one-shot `migrate_v001_to_v002(src_conn, dst_conn)` script that lives next to `apply` in `migrations.py`. It's not part of the runtime path.

## Module skeleton

```python
import sqlite3
from pathlib import Path
from typing import Final


SCHEMA: Final = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")

_EXPECTED_TABLES: Final = ("document", "document_property", "edge", "edge_property", "fts")


def apply(conn: sqlite3.Connection) -> None:
    """Apply the schema to `conn` if not already present. Idempotent.

    Must be called outside any explicit transaction — `executescript`
    unconditionally commits the current transaction before running the
    script, which would prematurely close any outer `write_transaction`.

    Race-tolerant: if another process applies the schema between our
    presence check and our executescript, the resulting OperationalError
    is swallowed only if the error text matches "already exists" AND the
    post-error state shows the full multi-table schema present.
    """
    if _schema_present(conn):
        return
    try:
        conn.executescript(SCHEMA)
    except sqlite3.OperationalError as e:
        if "already exists" in str(e) and _schema_present(conn):
            return
        raise


def _schema_present(conn: sqlite3.Connection) -> bool:
    placeholders = ",".join("?" * len(_EXPECTED_TABLES))
    sql = (
        f"SELECT COUNT(*) FROM sqlite_master "
        f"WHERE type='table' AND name IN ({placeholders})"
    )
    row = conn.execute(sql, _EXPECTED_TABLES).fetchone()
    return row[0] == len(_EXPECTED_TABLES)
            raise


def _schema_present(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='document'"
    ).fetchone()
    return row is not None
```

## Tests

All tests use `:memory:` connections constructed directly — `migrations.py` doesn't need `FileDatabase` to exercise. Full annotations, `pytest.raises(Exc, match=...)` for error cases.

1. `test_apply_creates_all_expected_tables` — fresh `:memory:` connection; call `apply`; introspect `sqlite_master` for every table in `_EXPECTED_TABLES` and every index (`idx_document_path`, `idx_document_property_key_value`, `idx_edge_kind_src`, `idx_edge_kind_dst`, `idx_edge_property_key_value`). The test imports `_EXPECTED_TABLES` from the module to keep the list in one place.
2. `test_apply_is_idempotent` — call `apply` twice; second call returns without raising; table list unchanged between calls.
3. `test_apply_raises_on_partial_schema` — pre-create only `document` (without the rest); call `apply`. The function sees the schema as not-present (multi-table check fails), tries `executescript`, fails with `OperationalError("table document already exists")`, the race-recovery re-checks, schema is still not present (other tables missing), error propagates. Asserts partial corruption surfaces loudly.
4. `test_apply_race_recovery_succeeds_when_schema_present` — monkeypatch `executescript` to raise `OperationalError("table document already exists")`, but pre-create every table in `_EXPECTED_TABLES` so `_schema_present` returns True after the raise. Assert `apply` returns normally.
5. `test_apply_race_recovery_reraises_when_schema_absent` — same monkeypatch shape, but the schema is not present. Assert the original `OperationalError` propagates.
6. `test_apply_does_not_swallow_non_already_exists_errors` — monkeypatch `executescript` to raise `OperationalError("disk I/O error")` *after* creating `document` (so `_schema_present` could lie if the marker were single-table — but with the multi-table check it correctly returns False). Even if `_schema_present` returned True, the error-text filter would reject this one. Assert the original `OperationalError` propagates.
7. `test_schema_constant_matches_file` — assert `SCHEMA` equals the contents of `schema.sql` on disk. Catches the case where someone hard-codes the constant in the module and forgets to load.

Tests #3 through #6 are the load-bearing tests for the race-recovery logic — they cover the four-quadrant matrix of `(error text matches | doesn't) × (schema present | absent)` and verify only the "matches AND present" cell swallows.

## Risks for the implementer

- **`executescript` and outer transactions.** The docstring on `apply` calls this out explicitly; the unit test suite doesn't catch it (because `:memory:` tests don't exercise the outer `write_transaction` boundary). The integration test that catches it lands in step 5 (walker) when `refresh` is wired up.
- **Real two-writer race test.** Tests #4 and #5 cover the translation logic via monkeypatch but don't exercise an actual contention. Add a single integration test in step 5 that opens two real connections to a shared file DB and calls `apply` on each from separate threads; the loser sees an `OperationalError` translated by `apply`'s race handling.
- **`OperationalError` filter — keep both halves.** The catch checks `"already exists" in str(e)` AND `_schema_present(conn)`. If a future implementer is tempted to drop either filter to "simplify," they will reintroduce one of two failure modes the reviewer flagged. Don't.
- **Module-level SCHEMA load.** Reading `schema.sql` at import time means the file must ship with the package. `pyproject.toml` already declares `[tool.setuptools.package-data] hoplite = ["schema.sql"]` from the schema-extraction work earlier. Don't undo that.
