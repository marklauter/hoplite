---
title: Related edges land, and rank replaces the threshold
summary: Tuned MinHash defaults so related edges emit on the live corpus, promoted confidence to a first-class column on Edge, and replaced the scalar min_confidence predicate with a top_k_related rank cap.
tags: [journal, minhash, related-edges, traversal, decision]
created: 2026-05-27
---

# Related edges land, and rank replaces the threshold

Tuned MinHash defaults so related edges emit on the live corpus, promoted confidence to a first-class column on Edge, and replaced the scalar `min_confidence` predicate with a `top_k_related` rank cap.

## Context

The graph held zero related edges across 54 documents and 1,431 candidate pairs. The day-one defaults — `DEFAULT_K = 128`, `DEFAULT_SHINGLE_SIZE = 5`, `DEFAULT_THRESHOLD = 0.10` — combined to suppress every pair. Confidence lived as a string under key `"confidence"` in `Graph.edge_properties`, not on the `Edge` dataclass. The `TraversePredicate` exposed `min_confidence: float` ∈ [0, 1] as the only related-edge knob, but the field description offered no distributional information, so an agent reaching for `0.5` got nothing back.

## Attempted

Probed pairwise MinHash scores across shingle widths 1, 2, 3, 4, 5 and `K` values 128, 256, 512 on the live corpus.

## Outcome

Observations from the probe:

- At shingle=5 the maximum pair score was 0.023. Prose documents rarely share 5-grams verbatim.
- Real topical pairs — `hoplite-architecture` ↔ `hoplite-tool-api`, the dream-agent note ↔ its `karpathy-llm-wiki` proxy — landed in the 0.005–0.02 band across reasonable shingle widths.
- At K=128 the resolution floor (`1/K = 0.0078`) collided with true Jaccards near that floor, aliasing real pairs to zero or to inflated single-match estimates. Raising K to 512 dropped the floor to 0.002 and surfaced previously-invisible pairs including `hoplite-roadmap` ↔ `hoplite-spec-index`, which K=128 missed entirely.
- mentions and cites edges by construction sit at full confidence (the author declared them). A scalar threshold spanning [0, 1] is incommensurate across edge kinds when authored edges anchor at 1.0 and inferred edges live two orders of magnitude lower.

## Decision

Four decisions, each a consequence of the prior:

1. Confidence is first-class on `Edge`. Promoted from an `edge_properties` string lookup to a `float = 1.0` field on the dataclass and a `confidence REAL NOT NULL` column in the dump schema. mentions and cites default to 1.0; related carries its Jaccard score directly.
2. The inferred edge skips when an authored edge already exists. `_emit_related_edges` drops any pair already connected by a `mentions` edge in either direction — the author declared the link, so the inferred edge is redundant noise.
3. MinHash defaults retuned. `DEFAULT_K = 512`, `DEFAULT_SHINGLE_SIZE = 4`, `DEFAULT_THRESHOLD = 0.0058` (three hash matches out of 512). The live corpus emits 15 distinct related pairs at scores 0.0058–0.0137.
4. `min_confidence` replaced with `top_k_related: int | None` on `TraversePredicate`. At each BFS node, related edges rank by descending confidence and truncate to the top K. mentions and cites are always followed regardless of the cap. Agents now ask for the K most-related neighbors per hop without needing to know the score distribution. See [[docs/notes/weighted-edge-traversal-ranks-by-accumulated-similarity.md]] for the broader ranking thread this fits into.

## Next

None. Cycle closed. Updated spec lives in [[docs/hoplite/hoplite-architecture.md]] and [[docs/hoplite/hoplite-tool-api.md]].
