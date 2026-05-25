---
title: Implementation plan
summary: "[Plan] Day-one delivery sequence for `hoplite_mcp`. Four dependency-ordered phases mapped onto the contracts and the implementation spec."
tags: [hoplite, mcp, plan]
created: 2026-05-25
aliases: []
---

## Current state

Pure components shipped:

- `parser.py` — predicate parser, compiles tag expressions to a `Callable[[frozenset[str]], bool]`.
- `filtering.py` — candidate filter that applies a compiled predicate to a tag set.
- `minhash.py` — MinHash signatures and Jaccard estimator. 64-bit hashes over Mersenne prime M_61, ~1024-byte signature per document.
- `wikilinks.py` — `[[target]]` extractor. Returns unique targets in document order; needs extending in Phase 2 to also return line/column positions.

Scaffolding (now needs rewrite to match the post-pivot surface):

- `models.py` — pre-pivot dataclasses (Node, Label, Envelope, etc.) that will be replaced with the new entity types (`Document`, `Tag`, `Edge`).
- `server.py` — FastMCP wiring skeleton currently registering 11 tools; will reduce to 4.
- `tools.py` — echo-style stubs for 11 tools; collapses to 4 query handlers.
- `test_smoke.py` — placeholder coverage; rewrites for the 4-tool surface.

What remains: rewrite the scaffolding modules against the new contracts, write the new `graph.py` module that holds the in-memory `Graph` and the corpus walker, extend `wikilinks.py` for source positions, and rewrite the smoke test.

## Phase 1 — Rewrite scaffolding for the new surface

Goal: get the build gate green with the new entity types and the trimmed 4-tool surface. Stub bodies are fine; this phase is about shape, not behavior.

1. **`models.py`** — replace contents with new dataclasses per [data-model.md](data-model.md): `Document` (with `resolved` flag and nullable content fields), `Tag`, `Edge`, plus result types `Hit`, `TraversalHit`, `WriteResult`. Drop `Node`, `Label`, `Envelope`, `FetchedNode`, `Landing`, `Prime`. All entity types frozen + slots.
2. **`tools.py`** — replace 11 stubs with 4 handler functions: `match_nodes`, `traverse_nodes`, `reindex`, `dump_index`. Bodies return stub data shaped like the real returns; predicate parsing uses the existing `parser.parse_predicate`.
3. **`server.py`** — replace tool registrations: 4 entries with appropriate `ToolAnnotations`. Drop the uninitialized-mode gate.
4. **`test_smoke.py`** — temporarily skip or xfail; will be rewritten in Phase 4.

Gate G1: build gate green; smoke test skipped.

## Phase 2 — Extend wikilinks for positions

Goal: `wikilinks.extract` returns `list[tuple[str, int, int]]` (target, line, column). The walker uses the target for mentions-edge creation; line and column are discarded after a later schema simplification dropped per-occurrence Edge metadata.

5. **`wikilinks.py`** — extend `extract()` signature in place. Track line and column during the regex sweep.
6. **`tests/test_wikilinks.py`** — update tests for the new return shape. Add a multi-line test that exercises position tracking.

Gate G2: build gate green.

## Phase 3 — Graph and walker

Goal: build the in-memory `Graph` from the corpus at server startup. Real query results, not stubs.

7. **`graph.py`** (new module) — `Graph` dataclass (`documents`, `tags`, `out_edges`, `in_edges`, `aliases`, `casefold_index`, `fts: sqlite3.Connection`) and the corpus walker:
   - Pass 1 (identity collection) — glob `**/*.md`, parse frontmatter, build document skeletons, register aliases, populate casefold index.
   - Pass 2 (body load + edges + indexes) — read bodies, parse wikilinks (with positions), materialize `mentions` and `member` edges with ghost creation on misses, populate FTS5, compute MinHash signatures.
   - Aggregate pass — pairwise MinHash for `related` edges above threshold.
   - `dump_index(path)` method — open destination SQLite, run DDL (verbatim from [implementation.md](implementation.md#hoplite_dump_index-schema)), bulk-insert from in-memory dicts, return `WriteResult` with row counts.
8. **`tools.py`** — wire the 4 handlers to a real `Graph` instance instead of stubs.
9. **`server.py`** — initialize the singleton `Graph` in the lifespan hook by running the walker against `Path.cwd()`.

Gate G3: build gate green; smoke test still skipped.

## Phase 4 — Integration and verification

Goal: end-to-end smoke test that exercises the real 4-tool surface against a real corpus.

10. **`test_smoke.py`** — rewrite:
    - Build a temp vault via the `tmp_path` fixture: 2-3 `.md` files with frontmatter, at least one wikilink between them, at least one wikilink to a missing target (forward reference → ghost), at least one tag shared across two documents.
    - Spawn the MCP server with `cwd=tmp_path`.
    - Assert the tool surface is exactly `{hoplite_match_nodes, hoplite_traverse_nodes, hoplite_reindex, hoplite_dump_index}`.
    - Call `hoplite_match_nodes` with text and tag predicates; assert expected paths in the result.
    - Call `hoplite_traverse_nodes` from one document, depth 1; assert reaching the wikilinked target.
    - Call `hoplite_dump_index` to a temp file; open it with `sqlite3`, assert documents table has expected real rows plus one ghost row.
11. **Manual MCP exercise** — run the server under the `/hoplite` skill in Claude Code, walk a small real corpus, fix any wire-level surprises.
12. **MinHash perf check** — generate 500 synthetic documents, time the cold-start MinHash + pairwise pass, confirm it's within the cold-start budget from [implementation.md](implementation.md#cold-start-budget).

Gate G4: build gate green; smoke un-skipped and passing. Gate G5: specs done; readme cross-references verified.

## Out of scope

[Roadmap](roadmap.md) features remain deferred: embedding-derived `:related` edges, multi-writer locking, file-watcher auto-reindex, LSH bucketing for MinHash, Sonnet-driven tag enrichment.
