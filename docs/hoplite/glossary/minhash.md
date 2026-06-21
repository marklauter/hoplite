---
title: MinHash
summary: "A compact sketch of a set that estimates its Jaccard similarity to another."
tags: [hoplite, glossary]
created: 2026-06-19
document.status: locked
edges: [estimates::docs/hoplite/glossary:jaccard]
---

A compact sketch of a set that estimates its Jaccard similarity to another.

## Mechanism

A document is a set of shingles. Exact Jaccard means intersecting every shingle of two sets — costly. MinHash compresses each set to a fixed-size signature instead:

1. Hash every shingle with `k` independent hash functions (e.g. 128); for each function, keep only the **minimum** hash over the set. The signature is the vector of those `k` minimums — `k` numbers, whatever the document's size.
2. For one hash function, `P(min(h(A)) == min(h(B))) == Jaccard(A, B)`: the shingle hashing to the global minimum over `A ∪ B` is equally likely to be any union member, and the two minimums coincide exactly when it lies in `A ∩ B`.
3. Estimate Jaccard by comparing two signatures position-by-position; the fraction of matching positions converges to the true value, with error shrinking like `1/√k`.

A lone signature is meaningless — similarity is the pairwise match-fraction of two signatures.

## Examples

- Hoplite stores one signature per document (the `document.minhash` blob) and compares signatures to estimate Jaccard cheaply, never materializing the full set intersection.
- The inferred similarity edges come from MinHash-estimated Jaccard, not exact overlap.
