---
title: Hoplite roadmap
summary: Features deferred past day one — embeddings, Sonnet tag enrichment, file-watcher reindex, MinHash LSH, persistent MinHash cache, multi-writer, pagination, unified query DSL, columnar projection.
tags: [hoplite, mcp, roadmap, spec]
created: 2026-05-25
status: wip
---

# Hoplite roadmap

Features deferred past day one — embeddings, Sonnet tag enrichment, file-watcher reindex, MinHash LSH, persistent MinHash cache, multi-writer, pagination, unified query DSL, columnar projection.

The day-one shape in [[docs/hoplite/hoplite-architecture.md]] and [[docs/hoplite/hoplite-tool-api.md]] holds unchanged for everything below — these features extend the runtime without breaking the public surface.

## Server-side enrichment — embeddings

Day one has no batch enrichment beyond MinHash. MinHash signatures and derived `discovered` edges compute at startup from the corpus content; no out-of-band model calls.

The one feature that wants server-side compute: vector embeddings via local Ollama (`nomic-embed-text` candidate, 768-dim, ~270MB, CPU-fast). With embeddings, `where` can switch from BM25-only to combined BM25 + cosine similarity, and embedding-derived `discovered` edges supplement MinHash for cases where lexical similarity doesn't catch the connection.

Embedding compute is heavier than MinHash — 50-500ms per document depending on model and hardware. The walker can't afford this on every reindex at 1000-doc scale. Two trigger models:

- Manual CLI — operator runs an embed pass when they want it. Output cached in `.hoplite/cache.db` keyed by `source_hash`.
- Lazy on first query — `where` with embedding-similarity scoring computes signatures on demand for any documents whose `source_hash` doesn't have a cached embedding.

Deferred until the BM25-only signal proves insufficient.

## Server-side enrichment — Sonnet-driven tag suggestions

An opt-in flag on `refresh(enrich_tags=True)` spawns a Sonnet sub-agent that reads document bodies and suggests tag additions. The agent supplies tags explicitly day one; this future feature offloads the suggestion-of-tags burden to an LLM pass when the corpus has drifted out of tag coverage.

Deferred. The "agent supplies all tags" baseline is the default; enrichment is opt-in.

## Auto-reindex — file-watcher

Day one, file changes between queries surface only on explicit `refresh()` calls.

Two aspirational upgrades:

- **Per-query stat-check.** Every `where` and `relatives` walks the corpus and `stat()s` every file; mtime or content_hash mismatch triggers refresh of the affected document. ~5ms per 1000 files per query — small. Picks up Obsidian hand-edits transparently without explicit reindex.
- **Watchdog file-watcher.** Background thread (Python `watchdog` package) watches the corpus directory; file events trigger immediate refresh. Instant detection; adds one dependency.

Per-query stat-check is the next-most-likely upgrade. Watchdog is the further reach for very-large corpora where per-query stats become noticeable.

## Persistent MinHash cache

At day-one scale (hundreds to low thousands of documents), MinHash cold-start (~50ms × N) is acceptable. At 5000+ documents, startup cost (~5min) becomes painful.

Mitigation: a persistent `.hoplite/cache.db` SQLite file holds `(path, source_hash, signature)` rows. At startup, the walker checks each `.md` body's hash against the cached row. Match → load cached signature; mismatch or missing → recompute and update the cache row.

This is decision-reversible — adding the cache later doesn't change the rest of the architecture. Deferred until corpus scale demands it.

## MinHash LSH bucketing

Day-one pairwise MinHash for `discovered` edges is O(N²). At 1000 docs this is ~100ms (cheap); at 10⁵+ docs it becomes minutes.

Mitigation: LSH (Locality-Sensitive Hashing) buckets signatures by sub-signature chunks, narrowing the comparison set so each document compares only against documents in matching buckets. Standard MinHash + LSH refinement; ~50 lines of additional code.

Deferred until corpus growth makes the pairwise pass noticeable.

## Multi-writer support

Day one assumes a single writer. The MCP server's single-threaded request handler is the lock; concurrent writes to the in-memory graph aren't supported.

Multi-agent is the actual target. Lifting single-writer involves:

- Per-document file locking when an agent writes a `.md` file (since multiple agents writing the same file race).
- A lock on the in-memory graph during reindex.
- Coordination between server processes if multiple Hoplite servers run against the same corpus.

Not a day-one concern; the personal-corpus pattern with one agent at a time is the common case.

## Collapse match and traverse into a unified query DSL

Day one has two discovery tools: `where` (BM25 over the whole corpus, no starting node) and `relatives` (BFS from a known node, no ranking). Each has a clear use case the agent picks between.

A richer query language — Cypher-style `MATCH ... WHERE ... RETURN` — could collapse both into one tool. The expressive power would let queries combine ranking and traversal in one shot ("find documents similar to this phrase that are also reachable from origin within 2 hops, ranked by relevance").

What you'd gain:

- One discovery surface instead of two.
- Combined queries — BM25 plus graph constraints plus tag filtering in one expression — that today require two-call composition.
- Closer to a "real" graph query language; Cypher fluency carries over.

What you'd lose:

- The agent has to learn the DSL to compose valid queries. Two simple tools with one-line descriptions are easier to pick from than one expressive query language.
- Implementation complexity. A query planner that handles ranking + traversal + tag filtering is a larger build than the two simple flows.
- The tag predicate added to both tools day one already covers most of the gap.

A middle option: keep the two simple primitives, add a third tool `query` that takes a Cypher-ish expression for cases that need combined ranking + traversal. Easy cases stay easy; expressive queries get their own tool.

Open question — pending a corpus or agentic use case that recurrently wants combined queries.

## Pagination

Day one, neither discovery tool paginates. `where` returns the top `k` results in one shot; `relatives` returns whatever's bounded by `depth` and the predicate.

What you'd gain:

- The agent can ask for the top 5 from a ranking but page through to 50 if needed, without recomputing.
- Large traversal results from hub documents become walkable incrementally instead of all-or-nothing.

What you'd lose:

- `where` becomes more complex than the simple "top-k" the agent picks `k` for. The `k` cap is doing real work as a self-limiting design.
- `relatives` pagination requires either caching the full BFS walk (memory cost) or encoding BFS state in a continuation token (large, awkward).

Two possible shapes if it lands:

- Continuation-token pagination on `where` only — its sorted-score result set suits tokens cleanly.
- Traverse stays unpaginated; bound by `depth` and predicate filtering.

Open question — pending a corpus or use case that recurrently bumps into the day-one caps.

## Columnar projection for multi-property predicates

Day-one `document_property` is pure EAV: every property is a row. Single-property lookups (`key='tags' AND value='hoplite'`) use the composite `(key, value)` index and run fast at any scale. Multi-property AND predicates require one self-join per additional clause:

```sql
-- status='draft' AND priority > 3
SELECT n1.path FROM document_property n1
JOIN document_property n2 ON n1.path = n2.path
WHERE n1.key = 'status' AND n1.value = 'draft'
  AND n2.key = 'priority' AND CAST(n2.value AS INTEGER) > 3;
```

At day-one corpus scale (hundreds to low thousands of documents, tens of thousands of property rows), SQLite handles the joins fine. At 10^5+ documents with three or more predicates, the planner's join cost compounds noticeably.

Mitigation: emit a derived **`document_wide`** table at dump time with one column per hot property — `(path, title, summary, status, priority, due, ...)`. Multi-predicate queries collapse to single-table scans. The wide table is a hot-path cache rebuilt each dump; `document_property` stays the canonical source for arbitrary keys.

Open question — pending a corpus that hits the cliff. The schema-mod is decision-reversible; the canonical EAV form keeps every property addressable.
