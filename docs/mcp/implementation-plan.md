# Implementation plan

[Plan] Day-one delivery sequence for `hoplite_mcp`. Five phases, dependency-ordered, mapped onto the [contracts](readme.md) and the [SQLite-hybrid implementation spec](implementation-sqlite-hybrid.md).

## Current state

Pure components shipped:

- `parser.py` — label-expression recursive-descent parser, compiles to a `Callable[[set[str]], bool]`.
- `filtering.py` — candidate filter that applies a compiled predicate to label sets.
- `minhash.py` — MinHash signatures and Jaccard estimator. 64-bit hashes over Mersenne prime M_61, ~1024-byte blob per node.
- `wikilinks.py` — `[[id]]` extractor. Returns unique ids in document order; the write flow consumes the list to emit `:mentions` edges.
- `ids.py` — id validator, corpus-relative path resolver, and `slugify_text`. Owns every id-shape concern in one place. `tools.py` re-exports `slugify_text` so the agent surface is unchanged.

Scaffolding:

- `models.py` — frozen dataclasses for the six entities plus four response types.
- `server.py` — FastMCP wiring skeleton, no lifespan or init-mode gate yet.
- `tools.py` — echo-style stubs for the eleven agent-facing tools. `slugify_text` is the one real implementation; the others return shaped fakes so the `/hoplite` skill can exercise wire shapes.
- `test_smoke.py`, `test_slugify.py` — placeholder coverage of the stub surface.

What remains is the four other pure components, the storage layer, and the orchestrators that compose them.

## Phase 1 — Finish the pure-component corridor

Four siblings of the existing pure modules. All text-in, value-out, no I/O, no storage. Each lands as a single `src/hoplite/<name>.py` with a matching `tests/test_<name>.py`.

1. `wikilinks.py` — extract every `[[id]]` from a body and return unique ids in document order. Regex `\[\[([^\]]+)\]\]`. Tests cover empty body, single link, repeated link dedup, multiple distinct links, and links embedded in fenced code blocks. The indexer emits a `:mentions` edge regardless of code-fence context.
2. `ids.py` — id validator and corpus-relative path resolver. Validates the `<segment>(/<segment>)*.<ext>` rule from [behavior.md](behavior.md#slug-and-id-rules), rejects path traversal, resolves an id to a `pathlib.Path` rooted under `<corpus>/docs/`. Absorbs `slugify_text` from `tools.py` so every id concern sits in one module; `tools.py` re-exports from the new home.
3. `labels.py` — auto-derived label extractor. Given an id, return the set of labels the indexer adds automatically: leading path segment when present, ISO date when the filename matches `<iso>-<slug>.<ext>`. Parametrized tests cover every example in [behavior.md](behavior.md#label-vocabulary).
4. `body.py` — body-shape validator and summary extractor. Asserts the line-1-H1 / line-2-blank / line-3-summary / line-4-blank contract and returns the parsed summary. Raises `ValueError` on a malformed body so the write flow can surface a constraint error to the caller.

Outcome: every input the write flow validates has a tested pure module behind it. Total work is small — roughly 75 lines of source across the four modules, plus tests.

## Phase 2 — Storage spine

I/O enters the codebase. One PR's worth of work.

5. `storage.py` — SQLite connection management. Opens `<corpus>/.hoplite/graph.db`, sets WAL, applies the schema DDL from [implementation-sqlite-hybrid.md](implementation-sqlite-hybrid.md#schema): `nodes`, `edges`, `labels`, `label_membership`, and the `nodes_fts` FTS5 virtual table. Exposes a context-managed connection and a schema-version check. Tests use a temp-directory corpus and assert tables exist, FTS5 mirrors the nodes table, and WAL is on.
6. Lifespan handler in `server.py` — at startup, look for `<cwd>/.hoplite/graph.db`. Found: open it and attach the connection to the FastMCP context. Missing: enter uninitialized mode where every tool except `hoplite_init_corpus` returns a constraint error directing the caller to init.
7. Real `hoplite_init_corpus` — replaces the stub. Creates `<cwd>/.hoplite/`, applies the schema, seeds the three day-one framing-axis envelope rows from the constants already living in `tools.py`. Idempotent: a second call on an initialized corpus returns success with no changes.

## Phase 3 — Write flow

The orchestrators land. Each one sequences already-tested pure modules and runs one SQLite transaction. Logic lives in the phase-1 modules and the storage layer; these tools sequence.

8. `hoplite_insert_node` — validate id (`ids.py`) → validate body shape and extract summary (`body.py`) → derive auto-labels (`labels.py`) → merge with author labels and enforce framing-axis exclusivity ([behavior.md](behavior.md#rejected-writes)) → parse wiki-links (`wikilinks.py`) → compute MinHash signature (`minhash.py`) → scan other nodes' signatures for matches at or above the threshold → write node row, label memberships, authored edges, `:mentions` edges, and bidirectional `:related` edges in one transaction. Reject when the id already exists.
9. `hoplite_update_node` — same pipeline as insert against an existing id, with edge reconciliation per [behavior.md](behavior.md#edge-reconciliation-on-update): `:mentions` re-parsed from the new body, authored edges replaced, `:related` recomputed against the current corpus.
10. `hoplite_delete_node` — remove the node row, its label memberships, its outbound edges, and the symmetric `:related` edges keyed on the deleted id. One transaction.
11. `hoplite_index_node` — metadata-only path. Re-derives labels and edges and recomputes the signature without rewriting the body. Closes the loop for hand-edited corpora and stale cached metadata.

## Phase 4 — Read and query surface

Storage in, composed responses out. Pulls envelope composition rules from [behavior.md](behavior.md#envelope-composition) and label-expression filtering from the phase-1 modules.

12. `hoplite_read_node` — load node and outbound edges, attach the fixed `CONTENT_ENVELOPE`. No label-based composition.
13. `hoplite_invoke_node` — load node and outbound edges, pick the framing-axis label's envelope (default `reference` when none is present), gather other labels' envelope bodies as `primes` sorted alphabetically.
14. `hoplite_apply_framing` — upsert an envelope body for a given label. Replaces any prior body for that label.
15. `hoplite_match_nodes` — FTS5 BM25 query for candidates, then `parser.parse_predicate(node_labels)` and `filtering.filter_candidates(...)` to narrow. Returns a `Landing` list sorted by score.
16. `hoplite_traverse_nodes` — iterative breadth-first walk over the edges table honoring `edge_types`, `min_confidence`, `direction`, and `depth`. Same post-filter pipeline as `match_nodes`.

## Phase 5 — Integration and polish

17. End-to-end smoke — extend `test_smoke.py` from the stub surface to a real `init → insert → match → invoke → update → traverse → delete` round-trip against a temp-directory corpus. This is the test that proves orchestration.
18. Manual MCP exercise — run the server under the `/hoplite` skill, walk the protocol with an agent, fix any wire-level surprises.
19. MinHash performance check — insert N=500 synthetic nodes and time the pairwise scan. Linear scan ships if it holds at the expected corpus size; a banded LSH index lands as a follow-up if it doesn't.

## Recommended next slice

Item 3 (`labels.py`) and item 4 (`body.py`) as one PR — both are small, share no code but share the "extract structured fact from text" shape, and landing them together completes Phase 1. Storage spine follows as one larger PR.

## Out of scope

[Roadmap](roadmap.md) features remain deferred: embedding-derived `:related` edges, multi-writer locking, cross-file transactional semantics, source files as graph nodes, external web references as first-class nodes, aspirational edge types, and legacy-corpus migration.
