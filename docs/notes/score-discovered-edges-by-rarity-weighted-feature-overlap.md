---
title: Score discovered edges by rarity-weighted feature overlap
summary: A discovered edge's confidence is one rarity-weighted Jaccard over a single feature set that unions every dimension — tags, properties, stereotypes, graph neighbors, binned proximity — so overlap across dimensions accumulates into one rank. Generalizes the content-only BM25 move to all channels.
tags: [note, hoplite, related-edges, ranking, signal, todo]
created: 2026-06-07
status: open
---

# Score discovered edges by rarity-weighted feature overlap

An inferred edge's confidence can be one rarity-weighted Jaccard over a single feature set that unions every dimension — tags, properties, property values, stereotypes, graph neighbors, and binned proximity — rather than a separate similarity computed per channel. Each shared feature contributes in proportion to its rarity, and overlap across dimensions accumulates into one rank.

## The construction

Represent each document as a set of feature tokens drawn from every relatedness dimension:

```
docA → { tag:note, tag:minhash, prop:status=design,
         stereotype:supersedes->docX, neighbor:docY,
         folder:docs/hoplite, created-month:2026-06 }
```

Weight each token by its rarity — `idf(f) = log(N / df(f))`, where `df(f)` is the number of documents carrying the feature. The score between two documents is the rarity-weighted overlap of their token sets — weighted Jaccard, or weighted-set cosine. A shared `tag:note` (high `df`) adds almost nothing; a shared `tag:minhash` or a co-mentioned rare entity (`df = 2`) adds a lot.

Because every dimension lives in one set, sharing across dimensions accumulates with no explicit combination rule. Two documents that share a rare tag, a neighbor, and a property value outrank two that share only one of the three. The cross-dimensional boost falls out of the union. It is a property of the score, not a tuned weighted sum of per-channel scores.

## It generalizes a principle the corpus already holds

[[docs/notes/relatedness-signals.md]] states the unit: a signal's strength is the self-information (rarity) of the shared feature — pointwise mutual information. It enumerates the channels: shared tag graded by tag rarity, shared property by value rarity, co-citation, common neighbors, and proximity. That note is the territory, and it lists the channels as separate signals.

[[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] applies the same rarity weighting to the content channel alone — BM25 cosine over FTS tokens, where IDF supplies the rare-term weight that plain MinHash Jaccard washes out by voting every shingle equally.

This note is the synthesis of those two. Take the rarity principle from the first and the IDF-weighting move from the second, then apply them across all channels at once by folding every feature into a single weighted set. Content stops being privileged. Text shingles become one more feature dimension, and structural and metadata features are the rest. One score, every channel.

## The discrete-versus-continuous wrinkle

Jaccard is set membership. It captures "rare shared feature" cleanly but not "narrow shared window." Time and space are continuous — two documents created three minutes apart are close, not set-equal. Two ways to fold proximity in:

- Bin the continuous value into a feature token (`created-month:2026-06`, `created-day:2026-06-07`). This fits the unified model but loses sharpness at bucket boundaries — `23:59` and `00:01` fall in different bins.
- Keep proximity as a separate distance kernel multiplied into the score. This is sharper but breaks the single-Jaccard elegance.

The relatedness-signals note already names both modes — a rare shared feature, or the tightest window that contains both. This is where they diverge mechanically.

## Implementation rides the existing tables

Structured features need no MinHash. Per-document structured feature sets are small — dozens of tokens — so an inverted index (feature to posting list of documents, each posting carrying the feature's IDF weight) computes exact weighted overlap cheaply. `node_property` supplies tag and property features; `edge` supplies neighbor features. The features are derivable from tables that already exist, so this carries no schema change.

MinHash earns its keep only on the content dimension, where shingle sets are large and the sketch avoids materializing them. The split: content reaches similarity through MinHash or BM25 cosine; structured features reach it through exact weighted Jaccard over an inverted index; the two combine into one `Edge.confidence`.

The destination is already named in the glossary stub at [[docs/hoplite/hoplite-glossary.md]] — "weighted minhash, weighted aggregation of intrinsic and asserted features." Weighted MinHash (consistent weighted sampling) is the sketch form if the unified feature set ever outgrows exact computation. At current corpus scale, exact computation suffices.

## Open questions

- How content similarity (BM25 cosine or MinHash) and structured-feature similarity (weighted Jaccard) combine into one score — concatenate into a single weighted set, or score the two separately and blend.
- Proximity handling — bin into features, or apply a separate distance kernel.
- Where per-feature `df` and IDF live, and whether they recompute on every drop-and-recreate or cache between rebuilds.
- Whether this reframes the three-channel structure in [[docs/hoplite/hoplite.md]] Discover into a single unified-feature similarity, with the channels demoted to feature groups.

## See also

- [[docs/notes/relatedness-signals.md]] — the channel enumeration and the rarity/PMI principle this operationalizes; that note is the territory, this note is the scoring construction over it.
- [[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] — the content-channel special case; IDF weighting for text, which this generalizes to all features.
- [[docs/notes/rerank-bm25-candidates-with-graph-signals.md]] — adjacent: combines text and graph signals as a query-time rerank, where this note combines them at edge-construction time.
- [[docs/notes/weighted-edge-traversal-ranks-by-accumulated-similarity.md]] — once the edge score is a unified rarity-weighted similarity, path accumulation rides cleaner signal.
