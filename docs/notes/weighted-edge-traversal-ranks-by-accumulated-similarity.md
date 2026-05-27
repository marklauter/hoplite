---
title: Weighted-edge traversal ranks by accumulated similarity
summary: Walking `tuple(related, P)` ranks by the path's product of edge confidences, evaluated best-first. BFS-by-distance fits unweighted edges only. A per-call `rank` strategy (`distance` for BFS, `similarity` for best-first) keeps the choice in the executor, separate from the predicate grammar.
tags: [note, hoplite, mcp, design, architecture, todo]
created: 2026-05-27
aliases: []
---

# Weighted-edge traversal ranks by accumulated similarity

Walking `tuple(related, P)` ranks by the path's product of edge confidences, evaluated best-first. BFS-by-distance fits unweighted edges only. A per-call `rank` strategy (`distance` for BFS, `similarity` for best-first) keeps the choice in the executor, separate from the predicate grammar.

## The mismatch

[Observation] `relatives` returns hits sorted by `distance` — hop count from the origin. `mentions` edges are unweighted, so hop count fits: one wikilink away outranks two.

[Observation] `related` edges carry a `confidence` property — the MinHash Jaccard score between two documents. The edge weight differs per pair.

[Inference] For traversal over `related`, hop count lies. Two strong-similarity edges along a path (`0.9 × 0.85 = 0.765`) outweigh one weak-similarity edge at `0.42`, but BFS orders the 1-hop neighbor ahead. The returned `distance` ignores edge weight.

## Two rank strategies

A `rank` parameter on `relatives` picks the executor strategy:

- `distance` — BFS, today's behavior. Hop count is the score. Works for any edge mix, including `mentions`-only and combined walks. Default.
- `similarity` — best-first / Dijkstra-style on weighted edges. Each path accumulates a score; the frontier pops in best-score order. Result is ranked by path quality, not hop count.

[Inference] The accumulation function for `similarity` is the product of edge confidences along the path — `c₁ × c₂ × c₃ …`. Multiplicative decay is the standard probabilistic interpretation, equivalent to summing `−log(confidence)` and minimizing. Sum would favor longer paths for free; minimum gives bottleneck semantics, sometimes intuitive but unusual. Product is the right default.

## Coupling: similarity rank restricts edges

[Inference] `rank=similarity` only makes sense over weighted edges. `mentions` carries no confidence, so accumulation requires either an assigned weight or an exclusion rule. Three handling options:

- Error if the caller asks for `similarity` with `mentions` in the edge set. Honest and surfaces the model. Recommended.
- Silently restrict to `related`. Convenient but hides the constraint; the caller may miss that the `mentions` filter was dropped.
- Treat `mentions` as cost-free hops — walk wikilinks for free, accumulate only `related` weights along the path. Defensible (the wikilink graph as freely navigable structure), surprising as a default.

## Depth semantics shift between modes

[Observation] In `distance` mode, `depth` is a relevance bound — distance 1 outranks distance 2 by construction.

[Inference] In `similarity` mode, `depth` becomes a budget — how far the search looks — because a 3-hop strong path can outrank a 1-hop weak neighbor. The natural finer bound is `min_similarity`, a cumulative threshold. Defer to a follow-up.

## Where this sits

Ranking is a post-grammar concern. The PDL proposal at [[docs/notes/hoplite-predicates-are-pdl-rewrites-over-typed-relations.md]] defines the predicate language for `where` and `relatives`; the grammar leaves evaluation strategy to the executor. Two strategies satisfy the same `tuple(related, P)` expression, picked at call time.

Same shape as the graph-prior rerank at [[docs/notes/rerank-bm25-candidates-with-graph-signals.md]] — both are ranking layers between predicate evaluation and result return. Different purposes: the rerank reorders `where` candidates by topology relative to a focus node; weighted-traversal ranking reorders `relatives` hits by accumulated edge confidence. Both stay orthogonal to the leaf-identity work in [[docs/notes/predicate-leaves-should-carry-relation-identity.md]], which restores relation identity to the predicate evaluator.

The result schema gains a `score` field whose interpretation depends on `rank` — hop count for `distance`, accumulated confidence for `similarity`. Comparable within a single call. Cross-call comparison is meaningless, same caveat as BM25 scores from `where`.

## Dependency: related edges have to fire

[Observation] [[docs/notes/related-edges-rarely-fire-in-current-corpus.md]] reports that `related` edges seldom materialize at current MinHash thresholds. Until that resolves, `similarity` mode runs over a sparse subgraph, and the rank distinction stays mostly theoretical. The work here remains worth specifying — the executor split is the right architecture regardless of how often `related` fires — but the practical payoff arrives with the edge-firing fix.
