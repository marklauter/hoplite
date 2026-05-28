---
title: row_factories.py — sqlite3.Row to dataclass mappers
summary: `row_factories.py` turns `sqlite3.Row` objects into the dataclasses defined in `models.py`. Inputs are explicit; transformations (JSON parsing, summary fallback, edge-list copy) are contained inside the module rather than delegated to SQL writers. Each factory carries a named SQL contract.
tags: [note, sqlite, design, hoplite, architecture]
created: 2026-05-27
document.status: design
---

# row_factories.py — sqlite3.Row to dataclass mappers

`row_factories.py` turns `sqlite3.Row` objects into the dataclasses defined in `models.py`. Inputs are explicit; transformations (JSON parsing, summary fallback, edge-list copy) are contained inside the module rather than delegated to SQL writers. Each factory carries a named SQL contract.

Sibling design notes: [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] for the rationale; [[docs/notes/db-refactor.md]] for the broader plan; [[docs/notes/db-py-design.md]] and [[docs/notes/migrations-py-design.md]] for the modules this collaborates with. This note covers `row_factories.py` alone.

## Public API

Six functions, all public — they cross module boundaries by design. `graph_sqlite.py` is the primary consumer once step 4 lands.

```python
def row_to_document(row: sqlite3.Row) -> Document: ...
def row_to_document_with_id(row: sqlite3.Row) -> tuple[int, Document]: ...
def row_to_edge(row: sqlite3.Row) -> Edge: ...
def row_to_hit(row: sqlite3.Row) -> Hit: ...
def row_to_traversal_hit(row: sqlite3.Row, via_edges: list[Edge]) -> TraversalHit: ...
def parse_tags(raw: str | None) -> list[str]: ...
```

`row_to_traversal_hit` takes an extra `via_edges` argument because the edge list is variable-length per row and cannot fit in one `sqlite3.Row` without aggregation. The caller assembles edges separately and passes them in; the factory copies the list so caller-side mutation can't leak into a frozen `TraversalHit`.

`row_to_document_with_id` is a thin sibling for the common case where a caller needs both the integer id (for edge-table joins) and the dataclass. `parse_tags` is exposed because the JSON-array shape is part of the module's contract and other future callers (e.g., a tag-only query path) may want to apply the same parse.

### SQL contracts at a glance

| Factory                  | Required columns                          | Notes                                                            |
|--------------------------|-------------------------------------------|------------------------------------------------------------------|
| `row_to_document`        | `path`, `resolved`, `content_hash`, `minhash` | Extra columns tolerated.                                         |
| `row_to_document_with_id`| `id` (literal column name), plus the four above | Returns `(id, Document)`.                                  |
| `row_to_edge`            | `src_path`, `dst_path`, `kind`, `confidence` | Names deliberately mismatch `edge.src`/`edge.dst`; see below.    |
| `row_to_hit`             | `path`, `summary`, `tags`, `score`        | `tags` is JSON-array text from `json_group_array`.               |
| `row_to_traversal_hit`   | `path`, `summary`, `tags`, `distance`     | `via_edges` passed separately; factory copies the list.          |

Extra columns in the row are always tolerated — `sqlite3.Row.__getitem__` ignores anything the factory doesn't ask for. The contract is "at least these columns," not "exactly these."

## Factories

Each factory names every column it reads, so a schema change that renames or drops a column surfaces as an `IndexError` from `sqlite3.Row.__getitem__` under test — not a silent default value. (`sqlite3.Row` raises `IndexError` for both integer-out-of-range and string-key-not-found, per CPython's `Modules/_sqlite/row.c`. Counterintuitive — most dict-shaped types raise `KeyError` — but documented.) `row_to_document` and `row_to_edge` are essentially pure projection. `row_to_hit` and `row_to_traversal_hit` also carry contained transformations (JSON parse, summary fallback, list copy) that the SQL writer can't reasonably produce from a single column.

### `row_to_document`

Maps a `document` row to the `Document` dataclass.

**SQL contract.** Row must carry: `path` (str), `resolved` (int — SQLite has no bool), `content_hash` (str | None), `minhash` (bytes | None).

```python
def row_to_document(row: sqlite3.Row) -> Document:
    return Document(
        path=row["path"],
        resolved=bool(row["resolved"]),
        content_hash=row["content_hash"],
        minhash=row["minhash"],
    )
```

`id` is not projected by `row_to_document` — `Document` is path-keyed in the dataclass. Callers that need both the id and the dataclass use `row_to_document_with_id`:

```python
def row_to_document_with_id(row: sqlite3.Row) -> tuple[int, Document]:
    return row["id"], row_to_document(row)
```

The compose-on-the-base pattern keeps `row_to_document` focused; the with-id form is a named API surface rather than ambient lore about "read `row['id']` yourself."

`resolved` widens from int to bool via `bool(...)`. This relies on the schema's `resolved INTEGER NOT NULL` constraint — if the column ever held a string `"0"`, `bool("0")` is `True` and the widening would silently lie. The constraint is load-bearing for this projection.

### `row_to_edge`

Maps an `edge` row to the `Edge` dataclass. The schema stores `src`/`dst` as integer FKs to `document.id`, but `Edge.src`/`dst` are path strings. The factory expects the row to carry path strings, joined from `document`.

**SQL contract.** Row must carry: `src_path` (str), `dst_path` (str), `kind` (str), `confidence` (float). The caller's SQL joins `edge` to `document` twice to surface paths:

```sql
SELECT e.kind, e.confidence,
       src_doc.path AS src_path,
       dst_doc.path AS dst_path
FROM edge e
JOIN document src_doc ON src_doc.id = e.src
JOIN document dst_doc ON dst_doc.id = e.dst
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

The `src_path`/`dst_path` naming (not `src`/`dst`) deliberately mismatches the table columns so the join intent is explicit at every call site. If a query writes `SELECT src, dst, ...` and tries to feed those rows to the factory, the `IndexError` fires immediately and points at the missing join.

**Gap worth owning.** This catches the *missing-alias* case but not the *miswritten-alias* case. A query that writes `SELECT e.src AS src_path, e.dst AS dst_path, ...` aliases integer FKs to the expected column name; the factory cheerfully constructs `Edge(src=<int>, dst=<int>, ...)` and the frozen dataclass performs no runtime type check (Python doesn't enforce dataclass annotations at runtime). Integers then silently propagate anywhere paths get compared, joined, or rendered. The deliberate name mismatch is half a defense, not a full one. Mitigations considered:

- Runtime `isinstance` assertion inside the factory — contradicts the "no defensive coding" rule and pays cost on every row.
- Take typed scalars instead of a Row (`src_path: str, ...`) — pyright catches the call site, but the factory loses its current shape and `graph_sqlite.py` becomes verbose.
- Trust the integration test that lands in step 4 to catch the bug end-to-end.

Day-one: take the third option. Acknowledge the gap; rely on tests that round-trip real edges through `relatives` queries to surface int-as-path mistakes.

### `row_to_hit`

Maps a `where`-query row to the `Hit` dataclass — a document plus its summary, tags, and BM25 score.

**SQL contract.** Row must carry: `path` (str), `summary` (str), `tags` (str — a JSON array as text), `score` (float). Summary comes directly from the `fts` virtual table — title and summary live in FTS only, not in `document_property`, so the FTS row's `summary` column is the single source of truth. Tags are aggregated from `document_property` via `json_group_array`:

```sql
SELECT d.path,
       fts.summary,
       (SELECT json_group_array(value) FROM (
          SELECT value FROM document_property
          WHERE id = d.id AND key = 'tags' ORDER BY rowid
        )) AS tags,
       bm25(fts) AS score
FROM fts
JOIN document d ON d.id = fts.rowid
WHERE fts MATCH ?
ORDER BY score
LIMIT ?
```

**Why summary isn't in `document_property`.** FTS5 already stores the original text of each indexed column (unless declared `contentless`), and `fts` carries one row per document by construction. Duplicating title/summary into `document_property` as `(id, 'summary', <text>)` rows would mean two sources of truth and a schema-uniqueness problem we'd need a partial unique index to fix. The current design sidesteps the whole problem: walker writes `title` and `summary` to FTS only, `document_property` holds every other frontmatter key (`document.tags`, `document.aliases`, `document.status`, `document.priority`, and arbitrary user-defined keys).

**Tags is not architecturally special.** Any list-valued frontmatter field has the same EAV shape: list elements fan out into multiple rows. On the document side, the destination is `document_property` keyed by `(id, key, value)`:

- `document.tags: [hoplite, note]` → `(id, 'tags', 'hoplite')`, `(id, 'tags', 'note')`.
- `document.collaborators: [alice, bob]` → `(id, 'collaborators', 'alice')`, `(id, 'collaborators', 'bob')`.

The element is the value, stored verbatim. No referential constraint — `tags` and `collaborators` accept arbitrary kebab-case strings.

`edge.<stereotype>: [...]` follows the *same list-decomposition shape* but adds a referential constraint on each element. Each element must be a document reference — a `docs/...` path or a `ghost/<slug>`. The walker validates each element at insert time (same gate the wikilink resolver applies at `graph.py:327-329`); a malformed element appends a warning and the element is skipped, no row written. A valid `docs/...` element resolves to a real `document.id`; a `ghost/...` element materializes a ghost document if absent. Either way, each element becomes one `edge` row pointing at that resolved id, plus one `edge_property` row carrying the stereotype label.

So the list-decomposition pattern is the same in structure on both sides; the contract on what a list element *means* differs. Document-side list-properties take opaque slugs; edge-side stereotype lists take document references and pay the resolver cost.

The `json_group_array(... ORDER BY rowid)` sub-select is the general shape for *materializing* a list-property back out of the EAV store — tags is the first one the `Hit` dataclass surfaces by name. A future query that wants `document.collaborators` composes the same sub-select with a different `key=` literal. A query that wants stereotypes on a node's outbound edges composes the same shape against `edge_property` joined to `edge`, with the labels post-grouped per `(src, dst)` pair.

**Tag order is pinned by `rowid`.** Bare `json_group_array(value)` returns elements in implementation-defined order — SQLite makes no stability guarantee without an inner `ORDER BY`. Today's `graph.py` walker inserts tags in frontmatter declaration order, and `Hit.tags` is a `list[str]` that users may reasonably expect to be ordered. The inner `SELECT value FROM ... ORDER BY rowid` wrapper preserves insertion order, which under the walker's `executemany(INSERT, rows_in_frontmatter_order)` matches frontmatter declaration order. Without the wrapper, parity against `graph.py` would diverge under any operation that reshuffles rowids (re-inserts, VACUUM).

The `ORDER BY rowid` inside an aggregate sub-select is the portable form. SQLite 3.44+ supports `aggregate(expr ORDER BY ...)` directly, but Python 3.11's bundled SQLite version is older; the wrapped-select form works on all SQLite builds we ship against.

```python
def row_to_hit(row: sqlite3.Row) -> Hit:
    return Hit(
        path=row["path"],
        summary=row["summary"] or "",
        tags=parse_tags(row["tags"]),
        score=row["score"],
    )
```

`summary` may be `None` for documents whose FTS row was indexed without a frontmatter summary; fall back to empty string. Ghosts and URL nodes never reach this code path — they have no FTS row, so the `JOIN fts` filters them out before the factory runs. `tags` parses from a JSON-array string — see the list-property section below.

### `row_to_traversal_hit`

Maps a `relatives`-query row plus its edge list to the `TraversalHit` dataclass.

**SQL contract.** Row must carry: `path` (str), `summary` (str), `tags` (str — JSON array), `distance` (int). `via_edges` arrives as a fully-assembled `list[Edge]` from the caller; the factory copies it.

```python
def row_to_traversal_hit(row: sqlite3.Row, via_edges: list[Edge]) -> TraversalHit:
    return TraversalHit(
        path=row["path"],
        summary=row["summary"] or "",
        tags=parse_tags(row["tags"]),
        distance=row["distance"],
        via_edges=list(via_edges),
    )
```

**The `list(via_edges)` copy is load-bearing.** `TraversalHit` is `frozen=True, slots=True`, but freezing applies to the attribute *bindings*, not to the mutable lists held on them. If the caller passes a per-row buffer that gets cleared and refilled across iterations, every `TraversalHit` would end up pointing at the same final list. The shallow copy isolates the dataclass from caller-side mutation. `tags` is accidentally safe because `parse_tags` always returns a fresh `list`; `via_edges` is the asymmetric case that needs explicit handling.

## List-property representation (tags is the first example)

The contract between the SQL writers and the factories is: any list-valued property arrives as a **JSON-array-formatted string** in a column whose name describes the property (`tags`, `collaborators`, etc.). One public helper parses any such column:

```python
def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [str(item) for item in json.loads(raw)]
```

The helper is named `parse_tags` because tags is the only list-property `Hit` currently surfaces — but the parser is just "JSON-array of strings to `list[str]`." If a second list-property query lands and the name starts feeling wrong, rename to `parse_list_property` (or similar) in one move. The function body doesn't change.

The choice of JSON over comma-separated is grounded in one practical fact: `json_group_array` is a built-in SQLite aggregate, so the SQL stays one line and the format is self-describing. Tag slugs are kebab-case lowercase and wouldn't ambiguate under comma-joining either, so this isn't a format-safety argument — it's a "which line of SQL the writer types" argument. Performance was *not* the deciding axis; `json.loads` of a short string is microseconds, but if a query returns hundreds of hits each with dozens of tags it does become measurable. Comma-split would be faster but tag values would need escaping. Noted, not optimized.

The contracted SQL shape — `(SELECT json_group_array(value) FROM (SELECT value FROM document_property WHERE ... ORDER BY rowid))` — returns `'[]'` for the zero-row case, not `NULL`. The `if not raw` branch in `parse_tags` is therefore unreachable under the documented contract. It stays as a defense for alternative SQL shapes — for example, a `LEFT JOIN ... GROUP BY` where the joined side is absent yields a real `NULL`. Future callers writing different aggregation shapes get the safety net.

The `[str(item) for item in json.loads(raw)]` form is deliberate: `json.loads` returns `Any`, and a previous version used `cast(list[str], json.loads(raw))` which is a typing lie — `json.loads("[1, 2]")` returns `[1, 2]` (list of ints) and the cast lets it pass for `list[str]`. The schema declares `document_property.value TEXT NOT NULL`, so values arrive as strings in practice, but the JSON-array-of-strings shape is enforced by the walker rather than by SQL. The `str(...)` coercion is the small runtime cost that keeps the type honest if the walker invariant ever cracks. Malformed JSON propagates as `json.JSONDecodeError`; that's a real walker bug worth surfacing loudly, not catching.

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
        tags=parse_tags(row["tags"]),
        score=row["score"],
    )


def row_to_traversal_hit(row: sqlite3.Row, via_edges: list[Edge]) -> TraversalHit:
    return TraversalHit(
        path=row["path"],
        summary=row["summary"] or "",
        tags=parse_tags(row["tags"]),
        distance=row["distance"],
        via_edges=list(via_edges),
    )


def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [str(item) for item in json.loads(raw)]
```

## Tests

Tests use `:memory:` connections — they're populated via `executescript` of `schema.sql` + a small fixture of insert statements, then read back through the factories. No `FileDatabase` dependency.

Shared fixture shape (one helper per table, kept module-local to the test file):

```python
def _populate_document(conn, *, id, path, resolved=True, content_hash=None, minhash=None): ...
def _populate_property(conn, *, id, key, value): ...
def _populate_edge(conn, *, id, src, dst, kind='mentions', confidence=1.0): ...
def _populate_fts(conn, *, rowid, path, title='', summary='', body=''): ...
```

Each test bullet below assumes these helpers are available; "insert one document row" expands to `_populate_document(conn, id=1, path='docs/notes/foo.md')` etc.

1. `test_row_to_document_projects_all_fields` — insert one document row; SELECT; assert the returned `Document` has the expected path, resolved bool, content_hash, minhash bytes.
2. `test_row_to_document_handles_null_optional_fields` — insert a ghost-shape row (`resolved=0`, `content_hash=NULL`, `minhash=NULL`); assert `Document.content_hash is None` and `Document.minhash is None`.
3. `test_row_to_document_widens_resolved_to_bool` — insert one row with `resolved=1`, one with `resolved=0`; assert `True` and `False` respectively, not `1` and `0`.
4. `test_row_to_document_with_id_composes_on_base` — insert a row with id=5; assert `row_to_document_with_id(row) == (5, row_to_document(row))`. Equality is the contract: the tuple form must compose on the base factory, not duplicate the projection. A test that "spot-checks a few fields" misses the invariant.
5. `test_row_to_edge_projects_path_columns_not_id` — populate `document` with two rows; populate `edge` with one row using integer ids; SELECT with the `src_path`/`dst_path` join; assert the `Edge.src`/`dst` are path strings.
6. `test_row_to_edge_raises_indexerror_on_missing_join` — same data, but SELECT without the join (returning `src` as the integer column); assert the factory raises `IndexError`. Guards against the missing-alias case.
7. `test_row_to_edge_does_not_guard_miswritten_alias` — explicit negative test documenting the known gap: SELECT writes `SELECT e.src AS src_path, ...` so the integer is aliased to the expected column name. The factory constructs `Edge(src=<int>, ...)` without raising. The test asserts `isinstance(edge.src, int)` to make the gap visible — a future reader who tightens this with `isinstance` checks would see this test fail and reconsider the broader contract.
8. `test_row_to_hit_parses_tags_in_insertion_order` — insert document_property tag rows in the explicit order `[('hoplite',), ('note',)]`; SELECT with the wrapped `json_group_array(... ORDER BY rowid)` form; assert `Hit.tags == ['hoplite', 'note']` (list equality, not set). Pins the ordering contract.
9. `test_row_to_hit_handles_empty_tags` — document with no tag property rows; `json_group_array` returns `'[]'`; assert `Hit.tags == []`.
10. `test_row_to_hit_handles_null_summary` — document indexed in FTS with NULL/empty summary; assert `Hit.summary == ''`. Ghosts can't trigger this path (no FTS row to JOIN against); the test exercises the real-FTS-row-with-empty-summary case.
11. `test_parse_tags_coerces_non_string_elements` — `parse_tags('[1, 2, 3]')` returns `['1', '2', '3']`. Documents the contract that the `str(item)` coercion is intentional, not accidental.
12. `test_parse_tags_propagates_malformed_json` — `parse_tags('not-json')` raises `json.JSONDecodeError`. Asserts that the factory does not catch and substitute — malformed JSON is a walker bug that should surface.
13. `test_row_to_traversal_hit_copies_via_edges` — caller passes a `list[Edge]`; assert `traversal_hit.via_edges is not the_input_list` (identity check). Then mutate the caller's list (e.g., `.clear()`); assert `traversal_hit.via_edges` is unchanged. Pins the copy-on-construction contract; future "optimizations" that drop the copy fail this test.
14. `test_row_to_traversal_hit_preserves_edge_order` — caller passes a `list[Edge]` of length 3 in a known order; assert the order on `TraversalHit.via_edges` matches.

Tests #5, #6, and #7 are the load-bearing trio for the edge-projection contract — happy path, missing-alias guard, and the explicit miswritten-alias gap. Test #8 pins the tag-ordering contract. Tests #11 and #12 pin the `parse_tags` contract. Test #13 pins the mutability fix.


**Scope of these tests.** The `:memory:` tests prove the projections work against a freshly-applied schema. They do **not** prove parity with today's `graph.py` — the same Document constructed via `graph.py`'s walker may carry different field values than the same Document materialized via the factory chain. Parity is step 9's job, not step 3's. Don't read green tests here as "row_factories.py produces the right domain objects for the real corpus."

## Why a separate module

Two alternatives to a dedicated `row_factories.py`:

**Alternative A: classmethods on the dataclasses in `models.py`** — e.g., `Document.from_row(row)`. Rejected because:

- `models.py` stays schema-agnostic. Today the dataclasses know about their own fields, not about SQLite, `sqlite3.Row`, or the JSON-array tag encoding. Pulling row-shape logic into `models.py` couples it to the persistence layer. Hoplite has gone through multiple persistence designs (in-memory dicts, persistent SQLite, dump-only SQLite, now persistent file-based again); a clean models module survives those churns.
- Classmethods on frozen dataclasses are awkward syntactically. `@dataclass(frozen=True, slots=True)` plus `classmethod` plus the `sqlite3` import in `models.py` reads as more machinery than the equivalent free function with one import.

**Alternative B: free functions inline at the top of `graph_sqlite.py`** — the SQL queries and the projections sit in the same file, so the SQL writer literally reads the function above the query. Rejected with less conviction because:

- The factories ship as a step-3 artifact validated by `:memory:` tests; `graph_sqlite.py` doesn't land until step 4. If the projections live inside `graph_sqlite.py` from the start, step 3 has no shippable deliverable — the design plan collapses two steps into one.
- The factories have potential consumers beyond `graph_sqlite.py`: a future tag-only query path, a debug-dump tool that reuses `parse_tags`, integration tests that round-trip rows without the full Graph. Inline-in-graph_sqlite forces those consumers to import private helpers.
- Test isolation is real — projection tests don't need a populated graph, just a `:memory:` connection with a fresh schema.

The arguments for inline are also defensible — co-located queries make schema drift harder to introduce, and the "~30 lines of projection logic" doesn't really earn its own file by volume alone. The choice here is "step boundaries beat code-locality optimization" rather than "this is the obviously correct shape." If step 4 wants to inline the factories at construction time, the move is small. The decision is reversible.

## Why explicit projection over reflection

`models.py` dataclasses could in principle be populated via `cls(**dict(row))` if column names matched field names. Two reasons that's wrong here:

1. **The column names don't always match the field names.** `Edge.src` ≠ `edge.src` (the row's `src` is an integer id; `Edge.src` is a path). The reflection approach would either silently put integers into `Edge.src` (Python doesn't runtime-check dataclass annotations) or require the SQL writer to alias columns to dataclass field names — at which point the implicit contract is brittler than the explicit one.

2. **Schema drift surfaces louder with explicit projection.** Renaming a column raises `IndexError` from the exact factory that reads it, pointing at the broken contract. With reflection, the dataclass `__init__` would either receive the wrong arg shape (less precise stack trace) or silently use a default and proceed (no error at all).

The tradeoff is that schema changes touch the factory file as well as the SQL. That's the right tradeoff at Hoplite's scale — five factories plus one helper, ~30 lines of projection logic.

## Risks for the implementer

### Hard rules — don't violate these

- **Don't add defensive coding inside factories.** If a row is missing a column, the `IndexError` is the bug signal. Don't catch it; don't substitute defaults. The test suite asserts this behavior in test #6. Same rule for malformed JSON in `parse_tags` — the `JSONDecodeError` is louder than swallowing.
- **Don't drop the `list(via_edges)` copy in `row_to_traversal_hit`.** Pinned by test #13. Frozen dataclasses don't freeze the lists held on them, and caller-side mutation leaking into the dataclass is the exact bug the copy prevents.
- **Don't reach for naive JSON slicing as a perf shortcut.** A `raw[1:-1].split(", ")` substitution would break on any value with a comma or quote (which `json_group_array` emits JSON-escaped). If you cut JSON, cut it with awareness of the encoding shape.
- **Model-evolution rule.** Adding a field to a dataclass means editing `models.py`, `schema.sql`, and `row_factories.py` together — plus the matching SQL writer in `graph_sqlite.py`. The whole point of centralizing projection here is that the schema-to-dataclass mapping has exactly one home; don't grow a second path that bypasses the factory.

### Known gaps — accepted, documented, not yet fixed

- **`row_to_edge` doesn't guard the miswritten-alias case** (integer FK aliased to `src_path` would pass through unchecked). Captured in test #7. If the integration tests in step 4 surface integer-as-path bugs in practice, revisit the factory shape (typed-scalar arguments instead of a Row).
- **`row_to_edge` doesn't guard scalar type widening either.** `Edge.confidence: float = 1.0` is unenforced at runtime. A query that emits `CAST(confidence AS INTEGER) AS confidence` would yield `Edge.confidence = <int>` without raising. Same class of gap as the miswritten-alias case, same mitigation if it ever bites: typed-scalar args. Not tested today.
- **Schema vs dataclass docstring contradiction (not this module's bug).** `schema.sql` declares `edge UNIQUE (src, dst)` — at most one edge per ordered pair, *regardless of kind*. But `models.py`'s `Edge` docstring says "Each pair of nodes carries at most one edge per kind." The factory is downstream and will appear to work; step 4's walker is where this bites. Resolve in step 4 by widening the constraint to `UNIQUE (src, dst, kind)` or updating the dataclass docstring.
- **The SQL contracts above are the contract — keep them in sync with the queries in `graph_sqlite.py` when they land in step 4.** A mismatch shows up as an `IndexError` in tests, which is good; but the design intent is for SQL writers to read the contracts table near the top before writing the query.
- **`conn.row_factory = sqlite3.Row` is set in [[docs/notes/db-py-design.md]]'s `FileDatabase`.** The factories here require it. A test that constructs a connection directly without going through `FileDatabase` must set the row factory before use.

### Future considerations — forward-pointers

- **`row_to_edge_with_id` if edge-property reads arrive.** Parallel to `row_to_document_with_id`. If a future caller needs the integer edge id to join into `edge_property`, add the sibling factory composing on `row_to_edge`. ~3 lines.
- **`parse_tags` rename to `parse_list_property` if a second list-property query lands.** Function body is generic; only the name encodes the first caller.
- **Tag parsing performance.** `json.loads` of short strings is microseconds per row, fine for typical `where` results. If heavy-tag workloads (hundreds of hits × dozens of tags) push this into measurable territory, switch to a tighter encoding-aware parse.
- **`json_group_array` is SQLite-specific.** If we ever need portable SQL, the tag aggregation has to change shape. Not a near-term concern.

### Editorial / bikeshed

- **`sqlite3.Row` indexing is case-insensitive.** Use lowercase consistently to match the schema; don't introduce case variance for cosmetic reasons.
- **Naming: `row_to_*` reads procedurally; `*_from_row` and `make_*` were considered.** The procedural form was kept for module-internal parallelism — every public function starts with the same verb, easy to scan.
- **`row_to_traversal_hit`'s two-arg signature breaks `map()` symmetry.** In practice all four factories are called inside loops, so the asymmetry is cosmetic. Worth knowing if a future caller wants iterator-style consumption.
