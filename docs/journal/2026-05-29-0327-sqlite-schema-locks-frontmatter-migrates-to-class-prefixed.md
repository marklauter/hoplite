---
title: SQLite schema locks; frontmatter migrates to class-prefixed
summary: Declared db.py shippable with a crash-orphaned-WAL recovery regression test, retired the in-memory graph for a single SQLite Graph with recursive-CTE traversal, locked schema.sql as frozen canon, migrated the whole corpus to class-prefixed frontmatter and flipped the shipped hook to match, and extracted frontmatter parsing into a new frontmatter.py on the prefixed standard.
tags: [journal, hoplite, sqlite, schema, frontmatter, session-summary]
created: 2026-05-29
---

# SQLite schema locks; frontmatter migrates to class-prefixed

Declared `db.py` shippable, retired the in-memory graph in favor of one SQLite-backed `Graph`, locked `schema.sql` as frozen canon, migrated the corpus to class-prefixed frontmatter and flipped the shipped contract to match, then extracted parsing into a new `frontmatter.py`.

## Context

Going in, the SQLite refactor ([[docs/todos/db-refactor.md]]) had steps 1–3 landed (`db.py`, `migrations.py`, `row_factories.py`) and step 4 (the graph) still framed as a `Graph` Protocol with two permanent peers — `InMemoryGraph` and `SqliteGraph`. The design notes had drifted on two axes: the in-memory/two-impl framing, and an older `document`/`path`/casefold-on-store schema vocabulary that `schema.sql` had already moved past (`node`/`uri`/`edge_kind`, `COLLATE NOCASE`).

## db.py shippable — WAL recovery proven, not assumed

The connection layer is sound; the one risk that could pass every unit test and still fail in production was a `mode=ro` reader recovering a crash-orphaned WAL — the classic "read-only can't create the `-shm`" gotcha.

[Observation] Proven empirically, then locked in as `test_open_ro_recovers_orphaned_wal`: a subprocess writes a row and `os._exit(0)`s without checkpointing, leaving an orphaned WAL; the test asserts the row is WAL-only (invisible to an `immutable=1` open of the base file), that the `open_ro` connection is genuinely read-only (a write raises `readonly`), and that it still reads the value back. Holds with the `-shm` present and deleted. Works because the *directory* is writable, so SQLite recreates the sidecar files even though the database connection can't write — and `.hoplite/` is always writable by design.

[Decision] The `?mode=ro&immutable=0` URI carries a dead flag (`immutable=0` is the default). Flagged as cosmetic; left as-is since the user declared `db.py` sussed. Do not flip to `immutable=1` — that disables the recovery the test just proved.

## In-memory graph retired; one SQLite Graph, CTE traversal

[Decision] The graph is SQLite-only. No `typing.Protocol`, no `InMemoryGraph`/`SqliteGraph` split, no parity oracle. One `Graph` class in `graph.py`, connection-per-call through the injected `Database`. Traversal moves from a Python BFS to a recursive CTE over `edge`/`edge_kind` — the `top_k_related` ranking and shortest-path dedupe live in the non-recursive CTEs (SQLite forbids window functions in the recursive term). Rationale recorded in [[docs/notes/graph-py-design.md]].

Rebased the whole design-note cluster onto this: deleted the dead Protocol note and `graph-sqlite-py-design.md` (folded into [[docs/notes/graph-py-design.md]]); rewrote [[docs/todos/db-refactor.md]], [[docs/notes/walker-py-design.md]], [[docs/notes/row-factories-py-design.md]], [[docs/notes/tools-py-design.md]], plus `migrations`/`db-py`/`server`/`reify`. Dropped the Kingo C# reference (db.py is settled). Deleted the casefold-on-store contract — `node.uri COLLATE NOCASE` makes case-insensitivity the column's job. Confirmed `UNIQUE(src, dst)` is correct (the stereotype model depends on one edge per pair); the fix for the stale `Edge` docstring is the docstring, not the constraint.

## schema.sql locked

[Decision] The user declared `schema.sql` officially locked — frozen canon (`node`/`node_property`/`edge`/`edge_kind`/`edge_property`/`fts`, `COLLATE NOCASE`, `WITHOUT ROWID` props). The property tables' foreign-key columns are `nodeid`/`edgeid` — named for the key they carry outward to `node(id)`/`edge(id)`, not a local row id. `fts` uses `detail = 'column'`: the agent consumer needs ranked matches, not human snippets, so it pays for no token positions. Recorded in memory; design resolves any drift in the schema's favor. The `models.py`/`row_factories.py` `Document`/`path` vocabulary still trails the schema's `node`/`uri`; queries bridge it with `n.uri AS path` rather than renaming the models in this pass.

## Frontmatter migrated to class-prefixed, hook flipped

[Decision] Adopted the class-prefix contract for real: `title`/`summary` stay bare (first-class FTS fields), everything else carries `document.` (node properties) or `edge.` (edge stereotypes). Migrated all 78 `.md` under `docs/` — `tags`/`created`/`aliases` → `document.tags`/`document.created`/`document.aliases` — via a Python pass that touched only the frontmatter block and preserved encoding (no BOM, CRLF intact; verified em-dash bytes survived).

[Observation] The shipped `check-frontmatter.py` hook caught the break in real time — it enforced the bare contract and rejected every migrated doc mid-edit. Flipped it (and the canonical `templates/components/shape/frontmatter.md`) to prefixed-only and rebuilt, so the hook and the four skills now teach `document.tags`/`document.created`. The user chose the hard flip over a dual-accept transition.

[Observation] `edge.blocked_by` is already in live use across four notes — an open-vocab stereotype the seed vocab doesn't list. My earlier "no stereotype usage in the corpus" claim was wrong; I'd scoped the grep to the canonical vocab. Stereotypes are locked-in design, so the stereotype notes' "migration out of scope" claims were marked done.

## frontmatter.py extracted

[Decision] Moved frontmatter parsing out of the renamed dead query graph (`mostly_dead_code_quary_only_graph.py`) into a clean `frontmatter.py` on the prefixed standard: `parse` (split → YAML → normalize → validate), `to_properties` (strip `document.`, casefold `tags`, exclude `title`/`summary`/`edge.*`), `fts_fields`, `edge_stereotypes`. `aliases` is optional. Both authoring shapes are accepted.

[Observation] Dotted and nested YAML are not natively identical — `yaml.safe_load` gives `{"document.tags": …}` for the flat form and `{"document": {"tags": …}}` for the nested form. Plain YAML has no dotted-path semantics; `frontmatter._normalize` flattens the nested mapping to dotted keys at the application level. Verified flat and nested produce identical properties and stereotypes. pyright and ruff clean.

## Next

- Step 5: `walker.py`, consuming `frontmatter.py` and writing the locked schema.
- The renamed query graph is still otherwise dead against the schema (its SQL references the old `document` table and `fts(path, …)`); its mandatory-field check is also bare. Do not run a live `refresh` on this corpus until the walker catches up — the hook and corpus are ahead of the shipped indexer.
- Deferred: reconcile `models.py`/`row_factories.py` `Document`/`path` to the schema's `node`/`uri`, or bless the `AS path` alias permanently.
