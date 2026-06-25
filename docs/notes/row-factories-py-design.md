---
title: row_factories.py — sqlite3.Row to dataclass mappers
summary: "`row_factories.py` turns `sqlite3.Row` objects into the dataclasses in `models.py`. Inputs are explicit; transformations (JSON parsing, summary fallback, edge-list copy) are contained inside the module. Each factory carries a named SQL contract the query writer in `graph.py` must satisfy. The factories read `Document`/`path`-vocabulary column names; the queries project the `node`/`uri` schema onto those names via `AS` aliases."
tags: [note, sqlite, design, hoplite, interface]
created: 2026-05-27
status: design
---

# row_factories.py — sqlite3.Row to dataclass mappers

`row_factories.py` turns `sqlite3.Row` objects into the dataclasses defined in `models.py`. Inputs are explicit; transformations (JSON parsing, summary fallback, edge-list copy) are contained inside the module rather than delegated to SQL writers. Each factory carries a named SQL contract.

Sibling design notes: [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale; [[docs/notes/db-refactor.md]] for the broader plan; [[docs/notes/db-py-design.md]] and [[docs/notes/migrations-py-design.md]] for collaborating modules; [[docs/notes/graph-py-design.md]] for the sole consumer. This note covers `row_factories.py` alone.

## Schema/vocabulary note

The landed factories read the `Document`/`path` vocabulary (`row["path"]`, `row["src_path"]`, `row["kind"]`). The current `schema.sql` uses `node`/`uri` and an interned `edge_kind`. The two are bridged in the **query**, not the factory: every SQL block below projects `n.uri AS path` and joins `edge_kind` to surface `k.kind AS kind`. The factory code is therefore unchanged by the schema rename — only the SQL contracts move. The `node`/`uri` ↔ `Document`/`path` drift is tracked in [[docs/notes/db-refactor.md]].

## Public API

Six functions, all public — they cross module boundaries by design. `graph.py` is the consumer once step 4 lands.

```python
def row_to_document(row: sqlite3.Row) -> Document: ...
def row_to_document_with_id(row: sqlite3.Row) -> tuple[int, Document]: ...
def row_to_edge(row: sqlite3.Row) -> Edge: ...
def row_to_hit(row: sqlite3.Row) -> Hit: ...
def row_to_traversal_hit(row: sqlite3.Row, via_edges: list[Edge]) -> TraversalHit: ...
def parse_tags(raw: str | None) -> list[str]: ...
```

`row_to_traversal_hit` takes an extra `via_edges` argument because the edge list is variable-length per row and can't fit in one `sqlite3.Row` without aggregation. The caller assembles edges separately and passes them in; the factory copies the list so caller-side mutation can't leak into a frozen `TraversalHit`.

`row_to_document_with_id` is a thin sibling for the common case where a caller needs both the integer id (for edge-table joins) and the dataclass. `parse_tags` is exposed because the JSON-array shape is part of the module's contract.

### SQL contracts at a glance

| Factory                  | Required columns                          | Notes                                                            |
|--------------------------|-------------------------------------------|------------------------------------------------------------------|
| `row_to_document`        | `path`, `resolved`, `content_hash`, `minhash` | `path` is `node.uri AS path`. Extra columns tolerated.       |
| `row_to_document_with_id`| `id`, plus the four above                 | Returns `(id, Document)`.                                        |
| `row_to_edge`            | `src_path`, `dst_path`, `kind`, `confidence` | `kind` is `edge_kind.kind`; paths join from `node`. See below.  |
| `row_to_hit`             | `path`, `summary`, `tags`, `score`        | `tags` is JSON-array text from `json_group_array`.               |
| `row_to_traversal_hit`   | `path`, `summary`, `tags`, `distance`     | `via_edges` passed separately; factory copies the list.          |

Extra columns are always tolerated — `sqlite3.Row.__getitem__` ignores anything the factory doesn't ask for. The contract is "at least these columns," not "exactly these."

## Factories

Each factory names every column it reads, so a schema change that renames or drops a column surfaces as an `IndexError` from `sqlite3.Row.__getitem__` under test — not a silent default. (`sqlite3.Row` raises `IndexError` for both integer-out-of-range and string-key-not-found, per CPython's `Modules/_sqlite/row.c`.) `row_to_document` and `row_to_edge` are essentially pure projection; `row_to_hit`/`row_to_traversal_hit` also carry contained transformations the SQL writer can't produce from one column.

### `row_to_document`

Maps a `node` row to the `Document` dataclass.

**SQL contract.** Row must carry: `path` (str — projected `node.uri AS path`), `resolved` (int — SQLite has no bool), `content_hash` (str | None), `minhash` (bytes | None).

```python
def row_to_document(row: sqlite3.Row) -> Document:
    return Document(
        path=row["path"],
        resolved=bool(row["resolved"]),
        content_hash=row["content_hash"],
        minhash=row["minhash"],
    )
```

`id` is not projected by `row_to_document` — `Document` is identity-keyed in the dataclass. Callers that need both the id and the dataclass use `row_to_document_with_id`:

```python
def row_to_document_with_id(row: sqlite3.Row) -> tuple[int, Document]:
    return row["id"], row_to_document(row)
```

`resolved` widens int → bool via `bool(...)`, relying on the schema's `resolved INTEGER NOT NULL` constraint.

### `row_to_edge`

Maps an `edge` row to the `Edge` dataclass. The schema stores `src`/`dst` as integer FKs to `node.id` and `kind` as an integer FK to `edge_kind.id`, but `Edge.src`/`dst` are URI strings and `Edge.kind` is the kind name. The factory expects the row to carry the resolved strings, joined out:

**SQL contract.** Row must carry: `src_path` (str), `dst_path` (str), `kind` (str), `confidence` (float). The caller's SQL joins `node` twice for the URIs and `edge_kind` once for the name:

```sql
SELECT k.kind,
       e.confidence,
       sn.uri AS src_path,
       dn.uri AS dst_path
FROM edge e
JOIN edge_kind k ON k.id = e.kind
JOIN node sn ON sn.id = e.src
JOIN node dn ON dn.id = e.dst
```

```python
def row_to_edge(row: sqlite3.Row) -> Edge:
    return Edge(
        src=row["src_path"],
        dst=row["dst_path"],
        kind=row["kind"],
        confidence=row["confidence"],
    )
```

The `src_path`/`dst_path` naming (not `src`/`dst`) deliberately mismatches the table columns so the join intent is explicit at every call site. If a query writes `SELECT src, dst, ...` and feeds those rows to the factory, the `IndexError` fires immediately. Likewise `kind` must be the *joined* `edge_kind.kind` string, not the raw integer `edge.kind` — a query that selects `e.kind` directly would put an integer into `Edge.kind`.

**Gap worth owning.** This catches the *missing-alias* case but not the *miswritten-alias* case. A query that writes `SELECT e.src AS src_path, e.dst AS dst_path, e.kind AS kind, ...` aliases integer FKs to the expected names; the factory cheerfully constructs `Edge(src=<int>, dst=<int>, kind=<int>, ...)` and the frozen dataclass performs no runtime type check. Integers then silently propagate. The deliberate name mismatch is half a defense, not a full one. Mitigations considered (runtime `isinstance`, typed-scalar args instead of a Row) are rejected day-one; rely on the integration tests that round-trip real edges through `relatives` to surface int-as-string mistakes.

### `row_to_hit`

Maps a `where`-query row to the `Hit` dataclass — a document plus its summary, tags, and BM25 score.

**SQL contract.** Row must carry: `path` (str), `summary` (str), `tags` (str — JSON array as text), `score` (float). Summary comes directly from the `fts` virtual table; tags are aggregated from `node_property` via `json_group_array`:

```sql
SELECT n.uri AS path,
       fts.summary,
       (SELECT json_group_array(value) FROM (
          SELECT value FROM node_property
          WHERE id = n.id AND key = 'tags'
        )) AS tags,
       bm25(fts) AS score
FROM fts
JOIN node n ON n.id = fts.rowid
WHERE fts MATCH ?
ORDER BY score
LIMIT ?
```

**Why summary isn't in `node_property`.** FTS5 already stores the original text of each indexed column, and `fts` carries one row per document by construction. Duplicating title/summary into `node_property` as `(id, 'summary', <text>)` rows would mean two sources of truth and a uniqueness problem. The walker writes `title`/`summary` to FTS only; `node_property` holds every other frontmatter key.

**Tags is one instance of the EAV list-decomposition pattern.** List-valued frontmatter fields decompose into multiple EAV rows — the convention is documented in [docs/hoplite/hoplite-architecture.md#eav-decomposition](../hoplite/hoplite-architecture.md#eav-decomposition). The factories materialize one such list back out via the `json_group_array(...)` sub-select; `Hit.tags` is the first list-property the dataclasses surface by name, but the same SQL shape and `parse_tags` helper work for any other list-property.

```python
def row_to_hit(row: sqlite3.Row) -> Hit:
    return Hit(
        path=row["path"],
        summary=row["summary"] or "",
        tags=sorted(parse_tags(row["tags"])),
        score=row["score"],
    )
```

`summary` may be `None` for documents indexed without a frontmatter summary; fall back to empty string. Ghosts and URL nodes never reach this path — they have no FTS row, so `JOIN fts` filters them out. `tags` is parsed from a JSON-array string and sorted ascending before construction — see [Tag sort lives here](#tag-sort-lives-here).

### `row_to_traversal_hit`

Maps a `relatives`-query row plus its edge list to the `TraversalHit` dataclass.

**SQL contract.** Row must carry: `path` (str), `summary` (str), `tags` (str — JSON array), `distance` (int). `via_edges` arrives as a fully-assembled `list[Edge]` from the caller; the factory copies it.

```python
def row_to_traversal_hit(row: sqlite3.Row, via_edges: list[Edge]) -> TraversalHit:
    return TraversalHit(
        path=row["path"],
        summary=row["summary"] or "",
        tags=sorted(parse_tags(row["tags"])),
        distance=row["distance"],
        via_edges=list(via_edges),
    )
```

**The `list(via_edges)` copy is load-bearing.** `TraversalHit` is `frozen=True, slots=True`, but freezing applies to attribute *bindings*, not to the mutable lists held on them. If the caller passes a per-row buffer that's cleared and refilled across iterations, every `TraversalHit` would point at the same final list. The shallow copy isolates the dataclass. `tags` is accidentally safe because `parse_tags` returns a fresh `list`; `via_edges` is the asymmetric case that needs explicit handling.

## Tag sort lives here

The `sorted(parse_tags(row["tags"]))` call inside `row_to_hit` and `row_to_traversal_hit` is the canonical sort site for tag lists on result dataclasses. There is one `Graph` implementation (see [[docs/notes/graph-py-design.md]]) and it goes through these factories, so pinning the sort here means tag ordering can't be silently violated by a caller. `parse_tags` itself does **not** sort — it stays the generic "JSON-array of strings to `list[str]`" parser; sortedness is a property of how the factories compose `parse_tags` with `sorted`.

**`node_property` has no insertion order.** It is a `WITHOUT ROWID` table, so there is no `rowid` to `ORDER BY` — the old "SQL preserves insertion order, factory sorts" two-stage claim no longer applies. The `json_group_array` sub-select returns tags in `node_property`'s primary-key order `(id, key, value)`, i.e. value-sorted within a key. That's harmless here precisely because the factory sorts anyway: `Hit.tags`/`TraversalHit.tags` are ascending-sorted regardless of the column's order. Any *future* order-sensitive list-property would need an explicit ordinal column, not a reliance on rowid.

## List-property representation (tags is the first example)

The contract between the SQL writers and the factories: any list-valued property arrives as a **JSON-array-formatted string** in a column named for the property. One public helper parses any such column:

```python
def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [str(item) for item in json.loads(raw)]
```

Named `parse_tags` because tags is the only list-property `Hit` currently surfaces — but the parser is just "JSON-array of strings to `list[str]`." Rename to `parse_list_property` in one move if a second list-property lands; the body doesn't change.

JSON over comma-separated because `json_group_array` is a built-in SQLite aggregate, so the SQL stays one line and the format is self-describing. The contracted shape returns `'[]'` for the zero-row case, not `NULL`, so the `if not raw` branch is unreachable under the documented contract — it stays as a defense for alternative SQL shapes (e.g. a `LEFT JOIN ... GROUP BY` yielding real `NULL`).

The `[str(item) for item in json.loads(raw)]` form is deliberate: `json.loads` returns `Any`, and a `cast(list[str], ...)` would be a typing lie (`json.loads("[1,2]")` is a list of ints). The `str(...)` coercion keeps the type honest if the walker invariant ever cracks. Malformed JSON propagates as `json.JSONDecodeError` — a real walker bug worth surfacing, not catching.

## Module skeleton

```python
import json
import sqlite3

from hoplite.models import Document, Edge, Hit, TraversalHit


def row_to_document(row: sqlite3.Row) -> Document:
    return Document(
        path=row["path"],
        resolved=bool(row["resolved"]),
        content_hash=row["content_hash"],
        minhash=row["minhash"],
    )


def row_to_document_with_id(row: sqlite3.Row) -> tuple[int, Document]:
    return row["id"], row_to_document(row)


def row_to_edge(row: sqlite3.Row) -> Edge:
    return Edge(
        src=row["src_path"],
        dst=row["dst_path"],
        kind=row["kind"],
        confidence=row["confidence"],
    )


def row_to_hit(row: sqlite3.Row) -> Hit:
    return Hit(
        path=row["path"],
        summary=row["summary"] or "",
        tags=sorted(parse_tags(row["tags"])),
        score=row["score"],
    )


def row_to_traversal_hit(row: sqlite3.Row, via_edges: list[Edge]) -> TraversalHit:
    return TraversalHit(
        path=row["path"],
        summary=row["summary"] or "",
        tags=sorted(parse_tags(row["tags"])),
        distance=row["distance"],
        via_edges=list(via_edges),
    )


def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [str(item) for item in json.loads(raw)]
```

## Tests

Tests use `:memory:` connections populated via `executescript` of `schema.sql` plus a small fixture of inserts, then read back through the factories. No `FileDatabase` dependency.

```python
def _populate_node(conn, *, id, uri, resolved=True, content_hash=None, minhash=None): ...
def _populate_property(conn, *, id, key, value): ...
def _populate_edge(conn, *, id, src, dst, kind='mentions', confidence=1.0): ...  # interns edge_kind
def _populate_fts(conn, *, rowid, uri, title='', summary='', body=''): ...
```

Test bullets:

1. `test_row_to_document_projects_all_fields` — insert one node row; SELECT with `uri AS path`; assert path/resolved/content_hash/minhash.
2. `test_row_to_document_handles_null_optional_fields` — ghost-shape row (`resolved=0`, nulls); assert `content_hash is None`, `minhash is None`.
3. `test_row_to_document_widens_resolved_to_bool` — `resolved=1`/`0` → `True`/`False`.
4. `test_row_to_document_with_id_composes_on_base` — id=5; assert `row_to_document_with_id(row) == (5, row_to_document(row))`.
5. `test_row_to_edge_projects_resolved_strings_not_ids` — two nodes, one edge; SELECT with the `edge_kind` + double-`node` join; assert `Edge.src`/`dst` are URIs and `Edge.kind` is the name string.
6. `test_row_to_edge_raises_indexerror_on_missing_join` — SELECT without the joins (returning integer `src`/`kind`); assert `IndexError`. Guards the missing-alias case.
7. `test_row_to_edge_does_not_guard_miswritten_alias` — SELECT `e.src AS src_path, e.kind AS kind, ...`; assert the factory constructs `Edge(src=<int>, kind=<int>, ...)` without raising. Makes the known gap visible.
8. `test_row_to_hit_returns_tags_sorted_ascending` — insert tag rows `[('note',), ('hoplite',)]`; SELECT with the `json_group_array` form; assert `Hit.tags == ['hoplite', 'note']`. Same shape for `row_to_traversal_hit`.
9. `test_row_to_hit_handles_empty_tags` — no tag rows; `json_group_array` returns `'[]'`; assert `Hit.tags == []`.
10. `test_row_to_hit_handles_null_summary` — FTS row with NULL/empty summary; assert `Hit.summary == ''`.
11. `test_parse_tags_coerces_non_string_elements` — `parse_tags('[1, 2, 3]') == ['1','2','3']`.
12. `test_parse_tags_propagates_malformed_json` — `parse_tags('not-json')` raises `json.JSONDecodeError`.
13. `test_row_to_traversal_hit_copies_via_edges` — identity check that the stored list isn't the input list; mutate the input, assert the dataclass is unchanged.
14. `test_row_to_traversal_hit_preserves_edge_order` — length-3 list in known order; assert order preserved.

**Scope of these tests.** The `:memory:` tests prove the projections work against a freshly-applied schema. They do **not** prove the queries in `graph.py` produce the right domain objects for the real corpus — that's the step-9 correctness check.

## Why a separate module

**Alternative A: classmethods on the dataclasses in `models.py`** (`Document.from_row(row)`). Rejected: `models.py` stays schema-agnostic — it knows its own fields, not `sqlite3.Row` or the JSON-array tag encoding. Hoplite has churned through several persistence designs; a clean models module survives those churns. Classmethods on frozen dataclasses are also awkward syntactically.

**Alternative B: free functions inline at the top of `graph.py`** — co-located queries make schema drift harder to introduce. Rejected with less conviction: the factories ship as a step-3 artifact validated by `:memory:` tests before `graph.py`'s query layer lands in step 4, they have potential consumers beyond `graph.py` (a debug-dump tool reusing `parse_tags`, integration tests round-tripping rows), and test isolation is real. The choice is "step boundaries beat code-locality" — reversible if step 4 wants to inline.

## Why explicit projection over reflection

`cls(**dict(row))` would work only if column names matched field names. Two reasons it's wrong: (1) the names *don't* match — `edge.src` is an integer id, `Edge.src` is a URI; `edge.kind` is an integer FK, `Edge.kind` is a name; reflection would either inject integers or force the SQL to alias to field names, making the implicit contract brittler than the explicit one. (2) Schema drift surfaces louder — renaming a column raises `IndexError` from the exact factory that reads it. The tradeoff (schema changes touch the factory file) is right at Hoplite's scale — five factories plus one helper.

## Risks for the implementer

### Hard rules — don't violate these

- **Don't add defensive coding inside factories.** A missing column's `IndexError` is the bug signal. Don't catch it; don't substitute defaults. Same for malformed JSON in `parse_tags`.
- **Don't drop the `list(via_edges)` copy in `row_to_traversal_hit`.** Pinned by test #13.
- **Don't reach for naive JSON slicing as a perf shortcut.** `json_group_array` emits JSON-escaped values; `raw[1:-1].split(", ")` breaks on commas/quotes inside values.
- **Model-evolution rule.** Adding a dataclass field means editing `models.py`, `schema.sql`, `row_factories.py`, and the matching SQL in `graph.py` together. One home for the schema-to-dataclass mapping; don't grow a second path.

### Known gaps — accepted, documented, not yet fixed

- **`row_to_edge` doesn't guard the miswritten-alias case** (integer FK or integer `kind` aliased to the expected name passes through unchecked). Captured in test #7. Revisit (typed-scalar args) if integration tests surface it.
- **`row_to_edge` doesn't guard scalar type widening either.** `Edge.confidence: float` is unenforced at runtime; `CAST(confidence AS INTEGER) AS confidence` would yield an int. Same class of gap.
- **Schema vs dataclass docstring contradiction.** `schema.sql` declares `edge UNIQUE (src, dst)` — at most one edge per ordered pair, *regardless of kind*. `models.py`'s `Edge` docstring still says "at most one edge per kind." The `UNIQUE (src, dst)` constraint is the **correct** one: the locked-in stereotype model ([[docs/notes/stereotypes-are-open-vocab-edge-properties.md]]) depends on one edge per pair with stereotypes hung off it as `edge_property` rows, and the doc→doc / doc→URL kinds never collide on a pair anyway. The fix is to correct the `Edge` docstring, not to widen the constraint. The factory is downstream and unaffected.
- **Keep the SQL contracts above in sync with the queries in `graph.py`.** A mismatch shows up as an `IndexError` in tests — good — but the intent is for SQL writers to read the contract before writing the query.
- **`conn.row_factory = sqlite3.Row` is set in `FileDatabase`** (see [[docs/notes/db-py-design.md]]). A test constructing a connection directly must set it before use.

### Future considerations — forward-pointers

- **`row_to_edge_with_id`** if edge-property reads arrive — parallel to `row_to_document_with_id`, ~3 lines.
- **`parse_tags` → `parse_list_property`** if a second list-property query lands.
- **`json_group_array` is SQLite-specific.** If portable SQL is ever needed, the tag aggregation changes shape.

### Editorial / bikeshed

- **`sqlite3.Row` indexing is case-insensitive.** Use lowercase consistently to match the schema.
- **Naming: `row_to_*` reads procedurally** — kept for module-internal parallelism (every public function starts with the same verb).
- **`row_to_traversal_hit`'s two-arg signature breaks `map()` symmetry.** Cosmetic — all factories are called inside loops.
