---
title: Hoplite scales to the cross-repo knowledge graph
summary: Two coupled upgrades make Hoplite usable across the multi-repo personal knowledge corpus — replace MinHash-as-ranker with BM25 cosine over the FTS5 tokens, and replace the single-cwd corpus root with a configurable vault collection sharing one global vocabulary. Two child notes collected here as one tracked deliverable.
tags: [note, hoplite, scale, bm25, corpus, design, todo, epic]
created: 2026-05-27
document:
  priority: high
  effort: high
  status: open
---

# Hoplite scales to the cross-repo knowledge graph

Two coupled upgrades make Hoplite usable across the multi-repo personal knowledge corpus — replace MinHash-as-ranker with BM25 cosine over the FTS5 tokens, and replace the single-cwd corpus root with a configurable vault collection sharing one global vocabulary. Two child notes collected here as one tracked deliverable.

## What ships together

- [[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] — replaces MinHash Jaccard with BM25 cosine for related-edge ranking. MinHash demotes to a candidate filter once n² rerank becomes expensive at scale; at single-corpus scale it disappears entirely.
- [[docs/notes/configurable-corpus-vaults-replace-single-root.md]] — single-cwd corpus root becomes a configurable collection of vaults. Canonical paths gain a vault prefix; per-vault tagging surfaces as synthetic tags on every document the vault contributes.

## Coupling

[Inference] The two upgrades couple at the IDF table. BM25 over a multi-vault corpus needs IDF computed across the union of vaults, not per vault — otherwise vault-local jargon over-weights and cross-vault rare terms under-weight, which kills the cross-vault `related` signal that multi-vault was meant to surface in the first place.

[Inference] Ship order: BM25 first against the existing single-corpus index — proves the scoring function works, leaves the global-IDF question pending. Multi-vault second, with IDF re-anchored across the union when the second ship happens. Either order works conceptually; this order minimizes scope per ship.

## Why both ship together (eventually)

[Inference] At the multi-repo target scale, neither upgrade alone solves the problem. BM25 on one repo is a quality lift, but the user's notes still live across silos. Multi-vault on MinHash ranking surfaces noisy pairs across the wider corpus because MinHash Jaccard's signal collapses on prose without rare-term weighting. Both together close the loop: BM25 with global IDF ranks pair similarity meaningfully across the full personal knowledge graph.

## What is out of scope

- Per-vault refresh granularity. `refresh()` re-walks the entire corpus today; partial reindex on filesystem change is a follow-up after the basic multi-vault structure works.
- Watch-mode reindex on filesystem events. Currently a manual `refresh()` call.
- LSH banding for MinHash candidate generation. Only earns its keep at corpora well beyond the current target.
- Hybrid retrieval ranker on `where` results — tracked at [[docs/notes/rerank-bm25-candidates-with-graph-signals.md]], an orthogonal concern about how `where` ranks candidates against a focus node.

## Dependencies

[Inference] Independent of the stereotype cluster at [[docs/notes/ship-the-stereotype-edge-annotation-layer.md]]. Different code paths; different tests. Stereotype semantics work the same regardless of pair-similarity scoring function. Ship order between the two clusters is free.

## See also

- [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]] — the cycle that closed before this scale-readiness work; established the `confidence` first-class column the BM25 swap rides on.
- [[docs/notes/ship-the-stereotype-edge-annotation-layer.md]] — the other parent todo from this session. Different cluster, free ship order.
