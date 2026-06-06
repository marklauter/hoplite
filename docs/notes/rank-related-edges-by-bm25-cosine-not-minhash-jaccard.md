---
title: Rank related edges by BM25 cosine, not MinHash Jaccard
summary: MinHash Jaccard over shingles weights every shingle equally, suppressing the rare-term signal that identifies topical adjacency. Compute pair similarity with BM25 cosine over the FTS5 tokens already indexed, and keep MinHash only as a sub-quadratic candidate filter once n² rerank gets expensive.
tags: [note, hoplite, mcp, related-edges, bm25, ranking, design, todo]
created: 2026-05-27
document:
  priority: high
  effort: high
  status: open
---

# Rank related edges by BM25 cosine, not MinHash Jaccard

MinHash Jaccard over shingles weights every shingle equally, suppressing the rare-term signal that identifies topical adjacency. Compute pair similarity with BM25 cosine over the FTS5 tokens already indexed, and keep MinHash only as a sub-quadratic candidate filter once n² rerank gets expensive.

## The signal problem with MinHash Jaccard

[Observation] Tuning MinHash defaults so `related` edges emit produced 15 distinct pairs at confidence scores in the 0.005–0.02 band — see [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]] for the cycle. The band is narrow, and the ordering inside it is coarse: the strongest pair (0.0137) is one journal entry that shares a few 4-grams of stub-review vocabulary with another.

[Inference] Jaccard over shingles treats every shingle as one vote. The shingle `the cache stores` votes the same as `MinHash signatures` or `as discussed above`. Topical adjacency turns on rare distinctive terms; Jaccard washes those out against the common register.

## What BM25 gives that MinHash does not

[Observation] BM25 weights rare terms via IDF, smooths term frequency, and length-normalizes. The IDF component is built in — saying "BM25" subsumes it.

[Inference] On the same corpus, BM25 cosine between two documents ranks pairs by shared *rare* vocabulary. Topical adjacency surfaces; common register sinks. The confidence number becomes a meaningful rank key, not a hash-collision count.

[Observation] FTS5 tokenization already runs. `where(text=...)` uses BM25 against the same body and summary index that powers free-text retrieval. The vocabulary, the per-term frequencies, and the IDF live in one place. Reranking `related` candidates with BM25 is mostly bookkeeping.

## Construction options

BM25 is a query-document score, not symmetric. Two ways to derive a doc-doc similarity:

1. Symmetrized BM25 — score `BM25(A as query, B as doc)` and `BM25(B as query, A as doc)`, average. Reuses FTS5's native `bm25()` directly; no new vectors to materialize.
2. BM25-weighted term vectors with cosine. Each document becomes a sparse vector whose weight at term `t` is `BM25(t, doc)`. Cosine between vectors is symmetric by construction.

[Guess] (1) is the faster path to a working prototype because the score function already exists. (2) composes more naturally with [[docs/notes/rerank-bm25-candidates-with-graph-signals.md]] — that note describes BM25 candidate retrieval for `where`, and BM25-weighted vectors give one representation reusable for both jobs.

## MinHash's revised job

[Inference] Once BM25 ranks pair similarity, MinHash is no longer the score function — it is a candidate filter. Its job shifts from "is this pair similar?" to "is this pair worth checking?" The threshold loosens (recall over precision), the shingle width can shorten without hurting ranking quality, and LSH banding becomes the relevant optimization once the corpus reaches the scale where pairwise BM25 cost is the bottleneck.

[Inference] At small scale (≤ 1000 docs), the candidate-gen step adds no value — compute BM25 cosine across every pair. The hybrid pays off at the multi-vault scale described in [[docs/notes/configurable-corpus-vaults-replace-single-root.md]].

## Where the score lives

[Observation] `Edge.confidence` is a first-class float column today, populated with the MinHash Jaccard for `related` edges and `1.0` for authored kinds. Swapping the score function leaves the column shape unchanged; the value becomes the BM25-derived similarity, normalized to `[0, 1]` if needed, with `1.0` continuing to mean "authored / full confidence by construction."

[Inference] The `top_k_related` predicate field keeps working — it ranks by `confidence`, and the new score is a more meaningful rank key. The emit-time threshold (`DEFAULT_THRESHOLD` in `minhash.py`) gets replaced with a BM25-scale threshold or a top-K cap at emit time; the exact value lands once we measure the distribution on a real corpus.

## Open questions

- Symmetrize-and-average vs. BM25-weighted cosine — decide on a working prototype.
- Where the threshold lives. BM25 scores live on a different scale than Jaccard; the right floor needs measurement on a target-scale corpus.
- Whether MinHash stays at all for small corpora, or comes back only when LSH becomes load-bearing.

## See also

- [[docs/notes/rerank-bm25-candidates-with-graph-signals.md]] — adjacent rerank pattern for `where` queries; the BM25-weighted vector representation is shared.
- [[docs/notes/weighted-edge-traversal-ranks-by-accumulated-similarity.md]] — once `related.confidence` carries a BM25-derived similarity, path-product accumulation in that proposal rides cleaner signal.
- [[docs/notes/configurable-corpus-vaults-replace-single-root.md]] — the scale that makes the hybrid pattern earn its keep.
- [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]] — the MinHash-tuning cycle that surfaced the signal-quality limitation.
