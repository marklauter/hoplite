---
title: walker.py — corpus → SQLite walker
summary: `walker.py` exposes `walk(conn, corpus_root) -> WriteResult`. It truncates every persisted table inside the caller's `BEGIN IMMEDIATE` transaction, then runs a two-pass scan over `*.md` files under `corpus_root` to repopulate `document`, `document_property`, `edge`, `edge_property`, and `fts`. The walker is the only writer in the system; every schema invariant the row factories and queries rely on is enforced here at insert time.
tags: [note, sqlite, design, hoplite, walker]
created: 2026-05-28
document.status: design
---

# walker.py — corpus → SQLite walker

`walker.py` exposes `walk(conn, corpus_root) -> WriteResult`. It truncates every persisted table inside the caller's `BEGIN IMMEDIATE` transaction, then runs a two-pass scan over `*.md` files under `corpus_root` to repopulate `document`, `document_property`, `edge`, `edge_property`, and `fts`. The walker is the only writer in the system; every schema invariant the row factories and queries rely on is enforced here at insert time.

Sibling design notes: [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale; [[docs/notes/db-refactor.md]] for the broader plan; [[docs/notes/db-py-design.md]] (transaction protocol), [[docs/notes/migrations-py-design.md]] (schema lifecycle), [[docs/notes/row-factories-py-design.md]] (the projection contracts this walker must satisfy), and [[docs/notes/graph-sqlite-py-design.md]] (the caller). This note covers `walker.py` alone.

## Module location and surface

New module at `plugins/hoplite/mcp/src/hoplite/walker.py`. One public function:

```python
def walk(conn: sqlite3.Connection, corpus_root: Path) -> WriteResult: ...
```

Why a separate module from `graph_sqlite.py`:
- Today's walker in `graph.py:walk` is ~115 lines. Inlining that as a method on `SqliteGraph` would balloon the class.
- The walker has its own test surface (`:memory:` connection plus a synthetic corpus directory) that doesn't need a `SqliteGraph` instance.
- Separating walker from query layer means the implementation agent for step 5 can land the walker without touching `graph_sqlite.py`. Symmetric: the implementation agent for step 4 doesn't need the walker to exist.

The walker writes through a raw `sqlite3.Connection`; it is `SqliteGraph`'s internal repopulation strategy, not part of the `Graph` Protocol. The peer `InMemoryGraph` uses its own existing walker (today's `graph.walk`) — different module, same `WriteResult` shape.

`walk` assumes the caller has already opened the rw connection, applied migrations, and started a `BEGIN IMMEDIATE` via `write_transaction(conn)`. Returns a `WriteResult` with row counts and warnings; raises on any DB error, letting `write_transaction`'s `ROLLBACK` undo the partial walk.

## Truncate-and-rebuild semantics

Day-one is truncate-then-insert, not reconcile-on-changes. The walker's first action inside the caller's transaction:

```python
conn.execute("DELETE FROM fts")
conn.execute("DELETE FROM edge_property")
conn.execute("DELETE FROM edge")
conn.execute("DELETE FROM document_property")
conn.execute("DELETE FROM document")
```

Order matters because of FK direction. `edge_property` references `edge.id`; `edge` references `document.id`; `document_property` references `document.id`; `fts` is independent but cleared for the same logical reason. We don't enable `PRAGMA foreign_keys = ON` for these DELETEs — they happen inside the write transaction the caller opened, and the FK constraints would fire spuriously on the intermediate states (deleting `edge` rows while `edge_property` rows still point at them). The caller's PRAGMA state is `foreign_keys = ON` per [[docs/notes/db-py-design.md]], so the walker explicitly disables it for the duration of the truncate:

```python
conn.execute("PRAGMA defer_foreign_keys = ON")
```

`defer_foreign_keys = ON` defers FK checks to commit time, which is what we want — the walker re-inserts every referenced row before the transaction commits, so FKs are satisfied at the boundary. This pragma is per-transaction and resets at COMMIT, so no cleanup is needed.

Reconcile semantics (added/changed/removed detection via `content_hash`) is future work — see [[docs/notes/db-refactor.md]] "Held for future."

## Pass 1: identity collection

Glob `*.md` recursively under `corpus_root`. For each file:

1. Compute `canonical = relative_path.as_posix()` (the repo-relative path with forward slashes).
2. Skip if `canonical` contains `/.hoplite/` or starts with `.hoplite/`.
3. Read the file as UTF-8; on `OSError` or `UnicodeDecodeError`, append a warning and continue.
4. Parse YAML frontmatter (the regex matches `---\n...\n---\n` at the head of the file). Missing frontmatter → warning, skip.
5. Validate mandatory fields (`title`, `summary`, `tags`, `created`). Missing → warning, skip.
6. Validate `tags` is a list and `aliases` (if present) is a list. Otherwise → warning, skip.
7. Compute `content_hash = sha256(body).hexdigest()`.
8. Insert into `document`:

```sql
INSERT INTO document (id, path, resolved, content_hash, minhash)
VALUES (?, ?, 1, ?, NULL)
```

The `id` is assigned in iteration order starting at 1; the walker holds a `path_to_id: dict[str, int]` map for use in pass 2 and the aggregate pass. Paths are casefolded before insert.

9. Insert frontmatter into `document_property`. **`title` and `summary` are skipped — they're FTS-only fields, not properties** (see [[docs/notes/row-factories-py-design.md]] "Why summary isn't in document_property"). Every other key fans out per the EAV decomposition pattern in [docs/hoplite/hoplite-architecture.md#eav-decomposition](../hoplite/hoplite-architecture.md#eav-decomposition):
   - Scalar value → one row `(id, key, str(value))`.
   - List value → one row per element `(id, key, str(element))`. Tag values are casefolded; other list values are stored verbatim (alias values, custom user-defined keys).
   - `None` values → skip.

Pass 1 collects every parsed file into a list `parsed: list[tuple[str, dict, str]]` (canonical, meta, body) for pass 2 to iterate. Memory cost: bodies held in RAM during the walk, freed after pass 2. At 1000 docs × 5 KB average body, ~5 MB peak.

## Pass 2: edges, FTS, MinHash

For each `(canonical, _meta, body)` in `parsed`:

### Wikilink mentions edges

Extract wikilinks via `hoplite.wikilinks.extract(body)`. For each target:

1. Strip `|alias` and `#anchor` to get the bare target.
2. Validate: target must start with `docs/` or `ghost/`. Otherwise → warning, skip.
3. Resolve via path → alias → casefold-path chain (same as `SqliteGraph._resolve_wikilink`, but executed against the in-walk state — the walker queries `document` and `document_property` directly).
4. If unresolved:
   - For `docs/...` targets → materialize a ghost document at the bare path with `resolved=0`, `content_hash=NULL`, `minhash=NULL`, and a synthetic `(id, 'tags', 'ghost')` property row.
   - For `ghost/...` targets → same shape, but keyed under the `ghost/<slug>` path.
5. Dedupe per `(src, target)` pair within the same source document.
6. Insert one `edge` row: `(id, src_id, target_id, 'mentions', 1.0)`. The `edge.id` is assigned in walk order; the walker holds an `edge_pair_to_id: dict[tuple[int, int], int]` for future `edge_property` writes (none today; the map is built for symmetry with `_write_edge_properties`).

### URL cites edges

Extract URLs via `hoplite.urls.extract(body)`. For each unique URL:

1. If not already a document: materialize a URL node at the verbatim URL string with `resolved=0`, `content_hash=NULL`, `minhash=NULL`, synthetic `(id, 'tags', 'url')` property row.
2. Insert one `edge` row: `(id, src_id, url_id, 'cites', 1.0)`.

### MinHash signature

Compute `minhash.signature(body)` (128 × uint64, ~50ms per document). Serialize via `minhash.to_bytes(sig)`. Update the document row:

```sql
UPDATE document SET minhash = ? WHERE id = ?
```

### FTS5 row

Insert into the virtual table:

```sql
INSERT INTO fts (rowid, path, title, summary, body)
VALUES (?, ?, ?, ?, ?)
```

`rowid` is `document.id` — this is the join key `row_to_hit`'s SQL contract uses. `title` and `summary` come from the parsed frontmatter (not from `document_property`, since they were never inserted there). `body` is the full body text minus frontmatter.

## Aggregate pass: related edges

After pass 2 commits all `document` and `mentions`/`cites` edges, run pairwise MinHash similarity:

1. Load every resolved document's `(id, minhash)` from the database.
2. Load the set of pairs already connected by `mentions` (in either direction) — these are skipped per today's `_emit_related_edges` behavior.
3. For each pair `(d1, d2)` with `d1.id < d2.id` not in the mentions set: compute Jaccard similarity from the two MinHash signatures.
4. If similarity ≥ `minhash.DEFAULT_THRESHOLD` (0.20 today): insert two symmetric edges:
   - `(src=d1.id, dst=d2.id, kind='related', confidence=score)`
   - `(src=d2.id, dst=d1.id, kind='related', confidence=score)`

The `UNIQUE (src, dst)` constraint on `edge` enforces single-edge-per-pair regardless of kind. This matches the schema (see [[docs/notes/graph-sqlite-py-design.md]] "Schema vs dataclass docstring contradiction") — if a pair has a `mentions` edge in one direction, the reverse-direction `related` edge from this pass would *not* collide because the `(src, dst)` ordered pair differs. But if a pair has `mentions` in both directions (unusual but possible), the related skip-check above already prevents the conflict.

Cost: O(N²) — pairwise comparisons. ~100ms for 1000 docs (128-int Jaccard is cheap). Past 10⁵ docs, LSH bucketing is the optimization to reach for; out of scope for this module.

## Path normalization

Paths are casefolded before insert — `canonical = canonical.casefold()` once, then used for the `path_to_id` map and every downstream insert (`document.path`, edge endpoints, ghost/URL bare identifiers). The `SqliteGraph._resolve_wikilink` casefold step then queries `WHERE path = ?` with a casefolded input against the same column. No separate column, no custom collation.

## Frontmatter classification — the canonical rule

The walker is where the rule "what goes to FTS vs document_property" is enforced. Stating it explicitly so the implementation agent can read it once:

| Frontmatter field | Destination |
|---|---|
| `title` | `fts.title` only |
| `summary` | `fts.summary` only |
| `tags` (list) | `document_property` rows with `key='tags'`, values casefolded |
| `aliases` (list) | `document_property` rows with `key='aliases'`, values verbatim |
| `created` (scalar) | `document_property` row with `key='created'` |
| `document.<anything>` (scalar) | `document_property` row with `key='<anything>'` |
| `document.<anything>` (list) | `document_property` rows with `key='<anything>'`, one row per element |

The `document.` prefix in frontmatter is a corpus convention (see [docs/hoplite/hoplite-architecture.md#eav-decomposition](../hoplite/hoplite-architecture.md#eav-decomposition)); the walker stores the key without the prefix (`document.priority: high` → `(id, 'priority', 'high')`). Stripping the prefix is the walker's job.

`edge.<stereotype>` keys are future work (see the stereotype notes); day-one walker ignores them or warns. Recommend warn, so the implementation agent surfaces unimplemented features instead of silently dropping them.

## Tests

Tests use `:memory:` connections constructed directly, populated with the schema via `migrations.apply(conn)`, then walked against a synthetic corpus directory (`tmp_path` from pytest).

Synthetic-corpus helper:

```python
def _make_corpus(tmp_path: Path, files: dict[str, str]) -> Path:
    """files maps relative path -> file contents. Returns the corpus root."""
    root = tmp_path / "docs"
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root
```

Each test passes a small dict of `docs/<path>.md → frontmatter+body` strings, calls `walk(conn, root.parent)`, then asserts against the DB state.

Test bullets:

1. `test_walk_populates_document_row` — one well-formed doc (e.g., source file `Docs/Notes/Foo.md`); assert one row in `document` with `path = "docs/notes/foo.md"` (casefolded canonical), `resolved=1`, non-null `content_hash`, non-null `minhash`. Pins the walker's casefold-on-store contract.
2. `test_walk_skips_title_and_summary_from_property` — well-formed doc with `title: Foo` and `summary: Bar`; assert `document_property` contains no rows with `key='title'` or `key='summary'`.
3. `test_walk_populates_fts_with_title_and_summary` — same doc; assert `fts` carries the title and summary text.
4. `test_walk_casefolds_tag_values` — doc with `tags: [Hoplite, NOTE]`; assert `document_property` rows have `value='hoplite'` and `value='note'`.
5. `test_walk_preserves_alias_case` — doc with `aliases: [Old/Path.MD]`; assert the alias property row has `value='Old/Path.MD'` (not casefolded).
6. `test_walk_strips_document_prefix` — doc with `document.priority: high`; assert `document_property` has `(id, 'priority', 'high')` not `(id, 'document.priority', 'high')`.
7. `test_walk_emits_mentions_edge_for_resolved_wikilink` — two docs, one wikilinks to the other; assert one `mentions` edge from src to dst.
8. `test_walk_materializes_ghost_for_unresolved_wikilink` — one doc wikilinks to `docs/notes/missing.md`; assert a ghost document row at that path with `resolved=0`, synthetic `ghost` tag, and the `mentions` edge points at it.
9. `test_walk_materializes_ghost_for_ghost_prefix` — wikilink target `ghost/missing`; assert ghost node at `ghost/missing`.
10. `test_walk_warns_on_malformed_wikilink` — wikilink target that's neither `docs/` nor `ghost/`; assert `WriteResult.warnings` contains an entry mentioning the bad target, no edge written.
11. `test_walk_emits_cites_edge_for_url` — doc with `[link](https://example.com)`; assert URL node and `cites` edge.
12. `test_walk_emits_related_edges_above_threshold` — two docs with similar body text (forcing MinHash similarity > 0.2); assert two symmetric `related` edges.
13. `test_walk_skips_related_when_mentions_exists` — two docs that would be similar AND wikilink to each other; assert no `related` edge (the mentions skip).
14. `test_walk_truncates_before_repopulating` — pre-populate the DB with a stale document; walk a different corpus; assert the stale row is gone, only the new ones present.
15. `test_walk_returns_writeresult_with_counts` — assert `WriteResult.counts` carries `documents`, `ghosts`, `urls`, `edges` keys with the expected numbers.
16. `test_walk_returns_warnings_on_missing_frontmatter` — file without frontmatter; assert a warning, no document row inserted.

## Risks for the implementer

### Hard rules — don't violate these

- **`defer_foreign_keys = ON` before the truncate.** Without it, the FK cascade between `document` and `document_property` (and `edge` → `edge_property`) fires on the intermediate state and the truncate fails. The pragma is per-transaction; no cleanup needed.
- **Title and summary skip `document_property`.** This is not optional. The row factories' SQL contract reads summary from `fts.summary`; duplicating it into `document_property` reintroduces the schema-uniqueness problem covered in [[docs/notes/row-factories-py-design.md]].
- **The walker holds the only write surface.** Don't add a second write path elsewhere. If a future tool needs to mutate the DB, it goes through `walk` (full rebuild) until reconcile semantics arrive.

### Known gaps — accepted, documented, not yet fixed

- **Casefold-on-store is the walker's contract.** Paths land in `document.path` already casefolded; the resolver casefolds inputs and matches against the same column. No schema field, no migration.
- **No reconcile semantics.** Every walk is truncate-and-rebuild. At corpus sizes past 5k documents this becomes noticeably slow on each refresh (minutes); reconcile is the next perf lever per [[docs/notes/db-refactor.md]] "Held for future."
- **`edge.<stereotype>` frontmatter is ignored or warned.** The stereotype-edge design ([[docs/notes/stereotypes-are-open-vocab-edge-properties.md]]) isn't implemented day-one. Recommend warning so the implementation agent surfaces this as a known unimplemented feature.

### Future considerations — forward-pointers

- **MinHash cold start** dominates walk time (~50ms × N docs). A persistent `.hoplite/cache.db` for signatures returns when corpus sizes push this past tolerable limits.
- **Body memory pressure** — bodies held in RAM during the walk. At 5k docs × 5KB this is 25MB; at 50k × 10KB it's 500MB. If this becomes a problem, switch to streaming pass 2 (read body, process, discard) instead of caching in `parsed`.
- **The `executescript`-vs-`write_transaction` integration test** (deferred from [[docs/notes/migrations-py-design.md]]) lands here. Test: walker called inside a write_transaction, with a fresh schema apply just before — verify no spurious COMMIT happens. This is the one place the autocommit-vs-explicit-transaction contract gets exercised end-to-end.

### Editorial

- The walker uses `wikilinks.extract` and `urls.extract` unchanged from today's `graph.py`. No need to re-derive their behavior here.
- Pass-1 and pass-2 separation mirrors today's structure for parity reasons. Don't fold them into a single pass — the alias/casefold lookup in pass 2 depends on pass 1 having materialized every canonical path first.
