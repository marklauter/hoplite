---
title: confidence
summary: "The strength of an assertion — how likely a statement is to be real."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
retired: [provenance, intrinsic, asserted]
has-a: "[[idf]]"
---

The strength of an [[assert|assertion]] — how likely a [[statement]] is to be real.

Confidence absorbs the retired provenance trinity: an authored or computed statement carries `1.0` — a word vouched in full — and an inferred, algorithmically derived one carries its likelihood. Build precedence follows the weight: full-confidence statements load first and the engine's guesses collide out.

## Mechanism

An authored assertion carries `1.0`: the author vouches in full. An inferred
assertion is graded. Its confidence is the rarity-weighted overlap of the two
documents' features. Each shared feature counts in proportion to its rarity,
`idf = log(N / df)`. A rare shared tag or term outweighs a common one. The
construction is worked out across all channels in
[[docs/notes/score-discovered-edges-by-rarity-weighted-feature-overlap]], and
for the content channel in
[[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard]].
