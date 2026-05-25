# Roadmap

[Roadmap] Features designed and named but not in day one. Each lands when the use case justifies the build. Contracts in [data-model.md](data-model.md), [tool-api.md](tool-api.md), [behavior.md](behavior.md), and [SKILL.md](../../plugins/hoplite/skills/hoplite/SKILL.md) hold unchanged for everything below — the day-one shape leaves room for these without contract breakage.

## Server-side enrichment — embeddings

Day one has no batch enrichment beyond MinHash. MinHash signatures and derived `related` edges compute at startup from the corpus content; no out-of-band model calls.

The one feature that wants server-side compute: vector embeddings via local Ollama (`nomic-embed-text` candidate, 768-dim, ~270MB, CPU-fast). With embeddings, `hoplite_match_nodes` can switch from BM25-only to combined BM25 + cosine similarity, and embedding-derived `related` edges supplement MinHash for cases where lexical similarity doesn't catch the connection.

Embedding compute is heavier than MinHash — 50-500ms per document depending on model and hardware. The walker can't afford this on every reindex at 1000-doc scale. Two trigger models:

- Manual CLI — operator runs an embed pass when they want it. Output cached in `.hoplite/cache.db` keyed by `source_hash`.
- Lazy on first query — `hoplite_match_nodes` with embedding-similarity scoring computes signatures on demand for any documents whose `source_hash` doesn't have a cached embedding.

Deferred until the BM25-only signal proves insufficient.

## Server-side enrichment — Sonnet-driven tag suggestions

An opt-in flag on `hoplite_reindex(enrich_tags=True)` spawns a Sonnet sub-agent that reads document bodies and suggests tag additions. The agent supplies tags explicitly day one; this future feature offloads the suggestion-of-tags burden to an LLM pass when the corpus has drifted out of tag coverage.

Deferred. The "agent supplies all tags" baseline is the default; enrichment is opt-in.

## Auto-reindex — file-watcher

Day one, file changes between queries surface only on explicit `hoplite_reindex()` calls.

Two aspirational upgrades:

- **Per-query stat-check.** Every `hoplite_match_nodes` and `hoplite_traverse_nodes` walks the corpus and `stat()s` every file; mtime or content_hash mismatch triggers refresh of the affected document. ~5ms per 1000 files per query — small. Picks up Obsidian hand-edits transparently without explicit reindex.
- **Watchdog file-watcher.** Background thread (Python `watchdog` package) watches the corpus directory; file events trigger immediate refresh. Instant detection; adds one dependency.

Per-query stat-check is the next-most-likely upgrade. Watchdog is the further reach for very-large corpora where per-query stats become noticeable.

## Persistent MinHash cache

At day-one scale (hundreds to low thousands of documents), MinHash cold-start (~50ms × N) is acceptable. At 5000+ documents, startup cost (~5min) becomes painful.

Mitigation: a persistent `.hoplite/cache.db` SQLite file holds `(path, source_hash, signature)` rows. At startup, the walker checks each `.md` body's hash against the cached row. Match → load cached signature; mismatch or missing → recompute and update the cache row.

This is decision-reversible — adding the cache later doesn't change the rest of the architecture. Deferred until corpus scale demands it.

## MinHash LSH bucketing

Day-one pairwise MinHash for `:related` edges is O(N²). At 1000 docs this is ~100ms (cheap); at 10⁵+ docs it becomes minutes.

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

Day one has two discovery tools: `hoplite_match_nodes` (BM25 over the whole corpus, no starting node) and `hoplite_traverse_nodes` (BFS from a known node, no ranking). Each has a clear use case the agent picks between.

A richer query language — Cypher-style `MATCH ... WHERE ... RETURN` — could collapse both into one tool. The expressive power would let queries combine ranking and traversal in one shot ("find documents similar to this phrase that are also reachable from origin within 2 hops, ranked by relevance").

What you'd gain:

- One discovery surface instead of two.
- Combined queries — BM25 plus graph constraints plus tag filtering in one expression — that today require two-call composition.
- Closer to a "real" graph query language; Cypher fluency carries over.

What you'd lose:

- The agent has to learn the DSL to compose valid queries. Two simple tools with one-line descriptions are easier to pick from than one expressive query language.
- Implementation complexity. A query planner that handles ranking + traversal + tag filtering is a larger build than the two simple flows.
- The tag predicate added to both tools day one already covers most of the gap.

A middle option: keep the two simple primitives, add a third tool `hoplite_query` that takes a Cypher-ish expression for cases that need combined ranking + traversal. Easy cases stay easy; expressive queries get their own tool.

Open question — pending a corpus or agentic use case that recurrently wants combined queries.

## Pagination

Day one, neither discovery tool paginates. `hoplite_match_nodes` returns the top `k` results in one shot; `hoplite_traverse_nodes` returns whatever's bounded by `depth` and the predicate.

What you'd gain:

- The agent can ask for the top 5 from a ranking but page through to 50 if needed, without recomputing.
- Large traversal results from hub documents become walkable incrementally instead of all-or-nothing.

What you'd lose:

- `hoplite_match_nodes` becomes more complex than the simple "top-k" the agent picks `k` for. The `k` cap is doing real work as a self-limiting design.
- `hoplite_traverse_nodes` pagination requires either caching the full BFS walk (memory cost) or encoding BFS state in a continuation token (large, awkward).

Two possible shapes if it lands:

- Continuation-token pagination on `hoplite_match_nodes` only — its sorted-score result set suits tokens cleanly.
- Traverse stays unpaginated; bound by `depth` and predicate filtering.

Open question — pending a corpus or use case that recurrently bumps into the day-one caps.

## Migration of legacy corpus

The pre-pivot `docs/notes/` corpus uses an older shape (no frontmatter, pure-markdown body with H1/blank/summary/blank structure). A migration converter walks every note, lifts the H1 and summary into a generated frontmatter block, derives tags from directory structure or filename prefixes, and writes the converted file back.

One-time CLI pass. Day-one development uses a fresh corpus or a hand-curated subset; full migration runs when it's needed.
