---
title: walker.py — corpus → SQLite walker
summary: "`walker.py` exposes `walk(conn, corpus_root) -> WriteResult`. It truncates the persisted tables inside the caller's `BEGIN IMMEDIATE` transaction, then runs a two-pass scan over `*.md` files under `corpus_root` to repopulate `node`, `node_property`, `edge` (with interned `edge_kind`), `edge_property`, and `fts`. The walker is the only writer in the system; every schema invariant the queries rely on is enforced here at insert time."
tags: [note, sqlite, design, hoplite, walker]
created: 2026-05-28
status: evolving
---

# walker.py — corpus → SQLite walker

`walker.py` exposes `walk(conn, corpus_root) -> WriteResult`. It truncates the persisted tables inside the caller's `BEGIN IMMEDIATE` transaction, then runs a two-pass scan over `*.md` files under `corpus_root` to repopulate `node`, `node_property`, `edge`, `edge_property`, and `fts`. The walker is the only writer in the system; every schema invariant the queries rely on is enforced here at insert time.

Sibling design notes: [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale; [[docs/notes/db-refactor.md]] for the broader plan; [[docs/notes/db-py-design.md]] (transaction protocol), [[docs/notes/migrations-py-design.md]] (schema lifecycle), [[docs/notes/row-factories-py-design.md]] (the projection contracts this walker must satisfy), and [[docs/notes/graph-py-design.md]] (the caller — `Graph.refresh`). This note covers `walker.py` alone.

## Module location and surface

New module at `plugins/hoplite/mcp/src/hoplite/walker.py`. One public function:

```python
def walk(conn: sqlite3.Connection, corpus_root: Path) -> WriteResult: ...
```

Why a separate module from `graph.py`: today's walker (`graph.py:walk`) is ~115 lines. Inlining it as a method on `Graph` would balloon the class, and the walker has its own test surface (`:memory:` connection plus a synthetic corpus directory) that doesn't need a `Graph` instance. `Graph.refresh()` is the only caller (see [[docs/notes/graph-py-design.md]]).

`walk` assumes the caller has opened the rw connection, applied migrations, and started a `BEGIN IMMEDIATE` via `write_transaction(conn)`. Returns a `WriteResult` with row counts and warnings; raises on any DB error, letting `write_transaction`'s `ROLLBACK` undo the partial walk.

## Schema and vocabulary note

The walker writes the current `schema.sql`: `node(id, uri, resolved, content_hash, minhash)`, `node_property(id, key, value)` (`WITHOUT ROWID`), `edge(id, src, dst, kind, confidence)` where `kind` is an integer FK into `edge_kind(id, kind)`, `edge_property`, and `fts(uri, title, summary, body)`. The frontmatter vocabulary in this note (`title`, `summary`, `tags`, `aliases`, `created`) is unchanged from today.

No casefold-on-store. `node.uri COLLATE NOCASE` makes URI matching case-insensitive at query time. The walker stores each URI verbatim, in its natural case. There is no casefolded copy and no casefold step; that contract is deleted. Tag values are still casefolded on store, a tag-normalization choice independent of URI identity, so predicate matching against casefolded query tags works.

## Edge-kind interning

`edge.kind` is an integer FK, not a string. Before writing edges, seed the vocabulary and build a lookup:

```python
conn.executemany(
    "INSERT OR IGNORE INTO edge_kind (kind) VALUES (?)",
    [("mentions",), ("cites",), ("related",)],
)
kind_to_id = dict(conn.execute("SELECT kind, id FROM edge_kind").fetchall())
```

`edge_kind` is a fixed vocabulary, not truncated by the walk; truncating it would orphan the FK from `edge`. `INSERT OR IGNORE` keeps it idempotent across rebuilds. Every `edge` insert uses `kind_to_id[kind]`.

## Truncate-and-rebuild semantics

Day-one is truncate-then-insert, not reconcile-on-changes. The walker's first action inside the caller's transaction:

```python
conn.execute("DELETE FROM fts")
conn.execute("DELETE FROM edge_property")
conn.execute("DELETE FROM edge")
conn.execute("DELETE FROM node_property")
conn.execute("DELETE FROM node")
```

`edge_kind` is left intact (see above). Order respects FK direction: `edge_property → edge`, `edge → node`, `node_property → node`. `fts` is independent but cleared for the same logical reason. The caller's PRAGMA state is `foreign_keys = ON` per [[docs/notes/db-py-design.md]], so the walker defers FK checks to commit time for the duration of the truncate-and-reinsert:

```python
conn.execute("PRAGMA defer_foreign_keys = ON")
```

`defer_foreign_keys = ON` is per-transaction and resets at COMMIT. The walker re-inserts every referenced row before the transaction commits, so FKs are satisfied at the boundary. No cleanup needed.

Reconcile semantics (added/changed/removed via `content_hash`) is future work — see [[docs/notes/db-refactor.md]] "Held for future."

## Pass 1: identity collection

Glob `*.md` recursively under `corpus_root`. For each file:

1. Compute `canonical = relative_path.as_posix()` (repo-relative, forward slashes). Stored verbatim — no casefold.
2. Skip if `canonical` contains `/.hoplite/` or starts with `.hoplite/`.
3. Read as UTF-8; on `OSError`/`UnicodeDecodeError`, warn and continue.
4. Parse YAML frontmatter. Missing/unterminated → warn, skip.
5. Validate mandatory fields: `title` and `summary` only (bare, first-class). `created`, `tags`, and `aliases` are optional. Missing `title`/`summary` → warn, skip. Note: today's `graph.py` checks `tags`/`created` as mandatory; the reduced mandatory set requires this updated check, so they must land together.
6. Validate `tags` is a list and `aliases` (if present) is a list. Otherwise → warn, skip.
7. Compute `content_hash = sha256(body).hexdigest()`.
8. Insert into `node`:

```sql
INSERT INTO node (id, uri, resolved, content_hash, minhash)
VALUES (?, ?, 1, ?, NULL)
```

The `id` is assigned in iteration order starting at 1; the walker holds a `uri_to_id: dict[str, int]` map for pass 2 and the aggregate pass.

9. Insert frontmatter into `node_property`. `title` and `summary` are skipped: they're FTS-only fields, not properties (see [[docs/notes/row-factories-py-design.md]] "Why summary isn't in node_property"). Every other key fans out per the EAV decomposition pattern in [docs/hoplite/hoplite-architecture.md#eav-decomposition](../hoplite/hoplite-architecture.md#eav-decomposition):
   - Scalar value → one row `(id, key, str(value))`.
   - List value → one row per element `(id, key, str(element))`. Tag values are casefolded; other list values stored verbatim (aliases, custom keys).
   - `None` → skip.

Pass 1 collects every parsed file into `parsed: list[tuple[str, dict, str]]` (canonical, meta, body) for pass 2.

## Pass 2: edges, FTS, MinHash

For each `(canonical, _meta, body)` in `parsed`:

### Wikilink mentions edges

Extract via `hoplite.wikilinks.extract(body)`. For each target:

1. Strip `|alias` and `#anchor` to the bare target.
2. Validate: must start with `docs/` or `ghost/`. Otherwise → warn, skip.
3. Resolve via the chain (exact `uri` match — case-insensitive through `COLLATE NOCASE` — then `aliases` property, then `.md` retry), executed against the in-walk `node`/`node_property` state. No casefolding of inputs; the column collation handles case.
4. If unresolved:
   - `docs/...` target → materialize a ghost `node` at the bare URI with `resolved=0`, `content_hash=NULL`, `minhash=NULL`, and a synthetic `(id, 'tags', 'ghost')` property row.
   - `ghost/...` target → same shape, keyed under the `ghost/<slug>` URI.
5. Dedupe per `(src, target)` within the source document.
6. Insert one `edge`: `(id, src_id, target_id, kind_to_id['mentions'], 1.0)`.

### URL cites edges

Extract via `hoplite.urls.extract(body)`. For each unique URL:

1. If not already a node: materialize a URL node at the verbatim URL string with `resolved=0`, `content_hash=NULL`, `minhash=NULL`, synthetic `(id, 'tags', 'url')` property row.
2. Insert one `edge`: `(id, src_id, url_id, kind_to_id['cites'], 1.0)`.

### MinHash signature

Compute `minhash.signature(body)` (128 × uint64, ~50 ms/doc). Serialize via `minhash.to_bytes(sig)`:

```sql
UPDATE node SET minhash = ? WHERE id = ?
```

### FTS5 row

```sql
INSERT INTO fts (rowid, uri, title, summary, body) VALUES (?, ?, ?, ?, ?)
```

`rowid` is `node.id` — the join key the query layer uses (`JOIN node n ON n.id = fts.rowid`). `title`/`summary` come from parsed frontmatter (never inserted into `node_property`). `body` is the body text minus frontmatter.

## Aggregate pass: related edges

After pass 2 writes all nodes and asserted edges, run pairwise MinHash similarity:

1. Load every resolved node's `(id, minhash)`.
2. Load the set of pairs already connected by `mentions` (either direction) — skipped per today's `_emit_related_edges` behavior.
3. For each pair `(d1, d2)` with `d1.id < d2.id` not in the mentions set: compute Jaccard similarity.
4. If similarity ≥ `minhash.DEFAULT_THRESHOLD` (0.20): insert two symmetric edges:
   - `(src=d1.id, dst=d2.id, kind=kind_to_id['related'], confidence=score)`
   - `(src=d2.id, dst=d1.id, kind=kind_to_id['related'], confidence=score)`

The `UNIQUE (src, dst)` constraint on `edge` allows at most one edge per ordered pair regardless of kind. A reverse-direction `related` edge does not collide with a forward `mentions` edge because the ordered pair differs; the mentions skip-check handles the both-directions case.

Cost: O(N²) pairwise (~100 ms for 1000 docs). Past 10⁵ docs, LSH bucketing is the optimization; it is out of scope here.

## Frontmatter classification — the canonical rule

The walker is where "FTS vs `node_property`" is enforced:

| Frontmatter field | Destination |
|---|---|
| `title` | `fts.title` only |
| `summary` | `fts.summary` only |
| `tags` (list) | `node_property` rows with `key='tags'`, values casefolded |
| `aliases` (list) | `node_property` rows with `key='aliases'`, values verbatim |
| `created` (scalar) | `node_property` row with `key='created'` |
| `<any-key>` (scalar) | `node_property` row with `key='<any-key>'` |
| `<any-key>` (list) | `node_property` rows with `key='<any-key>'`, one row per element |

Keys are flat, with no `document.` prefix (see [docs/hoplite/hoplite-architecture.md#eav-decomposition](../hoplite/hoplite-architecture.md#eav-decomposition)); the walker stores each non-special key verbatim (`priority: high` → `(id, 'priority', 'high')`).

A property whose value is a wikilink is a stereotyped edge, handled by the stereotype layer, a locked-in design (see [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] and [[docs/notes/ship-the-stereotype-edge-annotation-layer.md]]). Each wikilink in a `<stereotype>: ["[[target]]"]` value (and each inline `[[target]]<!--stereotype-->`) materializes a `mentions` edge plus an `edge_property` row `(edge_id, 'stereotype', '<stereotype>')` keyed by that edge's id. The stereotype layer ships as its own coordinated cycle, independent of this refactor's ship order; this walker is where its emit path lands when the two converge.

## Tests

`:memory:` connections, schema via `migrations.apply(conn)`, walked against a synthetic corpus directory (`tmp_path`).

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

Test bullets:

1. `test_walk_populates_node_row` — one well-formed doc at source path `Docs/Notes/Foo.md`; assert one `node` row with `uri = "Docs/Notes/Foo.md"` **verbatim** (no casefold), `resolved=1`, non-null `content_hash`, non-null `minhash`. Pins the verbatim-store contract.
2. `test_walk_skips_title_and_summary_from_property` — assert `node_property` has no `key='title'`/`key='summary'` rows.
3. `test_walk_populates_fts_with_title_and_summary` — assert `fts` carries the title/summary text.
4. `test_walk_casefolds_tag_values` — doc with `tags: [Hoplite, NOTE]`; assert `node_property` rows have `value='hoplite'`, `value='note'`.
5. `test_walk_preserves_alias_case` — doc with `aliases: [Old/Path.MD]`; assert the alias row has `value='Old/Path.MD'` (not casefolded).
6. `test_walk_stores_user_property` — doc with `priority: high`; assert `(id, 'priority', 'high')`.
7. `test_walk_interns_edge_kind` — assert `edge_kind` contains `mentions`/`cites`/`related` and `edge.kind` holds their integer ids.
8. `test_walk_emits_mentions_edge_for_resolved_wikilink` — two docs, one links the other; assert one `mentions` edge.
9. `test_walk_resolves_wikilink_case_insensitively` — doc at `docs/notes/foo.md`, another wikilinking `docs/notes/FOO.md`; assert the edge resolves to the existing node (collation), no ghost created.
10. `test_walk_materializes_ghost_for_unresolved_wikilink` — wikilink to `docs/notes/missing.md`; assert a ghost node at that URI with `resolved=0`, synthetic `ghost` tag, and the `mentions` edge points at it.
11. `test_walk_materializes_ghost_for_ghost_prefix` — target `ghost/missing`; assert ghost node at `ghost/missing`.
12. `test_walk_warns_on_malformed_wikilink` — target neither `docs/` nor `ghost/`; assert a warning, no edge.
13. `test_walk_emits_cites_edge_for_url` — `[link](https://example.com)`; assert URL node and `cites` edge.
14. `test_walk_emits_related_edges_above_threshold` — two similar docs; assert two symmetric `related` edges.
15. `test_walk_skips_related_when_mentions_exists` — two similar docs that also wikilink each other; assert no `related` edge.
16. `test_walk_truncates_before_repopulating` — pre-populate a stale node; walk a different corpus; assert the stale row is gone.
17. `test_walk_returns_writeresult_with_counts` — assert `counts` carries `documents`/`ghosts`/`urls`/`edges`.
18. `test_walk_returns_warnings_on_missing_frontmatter` — file without frontmatter; assert a warning, no node row.

## Risks for the implementer

### Hard rules — don't violate these

- `defer_foreign_keys = ON` before the truncate. Without it the FK cascades fire on intermediate states and the truncate fails. Per-transaction; no cleanup.
- Don't truncate `edge_kind`. It's a fixed vocabulary that `edge.kind` FKs into. Seed with `INSERT OR IGNORE`; leave it across rebuilds.
- Don't casefold URIs. Store verbatim; `COLLATE NOCASE` does case-insensitive matching at query time. Casefolding on store is the deleted contract.
- Title and summary skip `node_property`. This is not optional. The query layer reads summary from `fts.summary`; duplicating into `node_property` reintroduces a two-sources-of-truth problem (see [[docs/notes/row-factories-py-design.md]]).
- The walker holds the only write surface. Don't add a second write path. Future mutations go through `walk` (full rebuild) until reconcile semantics arrive.

### Known gaps — accepted, documented, not yet fixed

- No reconcile semantics. Every walk is truncate-and-rebuild. Past ~5k docs this is minutes per refresh; reconcile is the next perf lever (see [[docs/notes/db-refactor.md]] "Held for future").
- The stereotype layer is locked-in design, shipped on its own cycle. Both authoring surfaces (`[[target]]<!--stereotype-->` inline, `<stereotype>: "[[target]]"` frontmatter) emit a `mentions` edge plus an `edge_property` stereotype row through this walker (see [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] and [[docs/notes/ship-the-stereotype-edge-annotation-layer.md]]). Whether it lands in the same pass as this refactor depends on ship order between the two clusters, which is free.
- `node_property` is `WITHOUT ROWID`. No insertion-order column. Tags are sorted at projection, so order is moot for them; any future order-sensitive property needs an explicit ordinal.

### Future considerations — forward-pointers

- MinHash cold start dominates walk time (~50 ms × N). A persistent signature cache returns when corpus sizes grow.
- Body memory pressure: bodies held in RAM during the walk (~25 MB at 5k × 5 KB). Stream pass 2 (read, process, discard) if it grows.
- The `executescript`-vs-`write_transaction` integration test (deferred from [[docs/notes/migrations-py-design.md]]) lands here: walker called inside a `write_transaction` with a fresh schema apply just before; verify no spurious COMMIT.

### Editorial

- `wikilinks.extract` and `urls.extract` are reused unchanged from today's `graph.py`.
- The pass-1/pass-2 separation is load-bearing: the resolve step in pass 2 depends on pass 1 having materialized every canonical URI first.
