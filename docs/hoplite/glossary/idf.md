---
title: idf
summary: "A feature's rarity, scored as the inverse of its document frequency."
tags: [hoplite, glossary]
created: 2026-06-20
document.status: locked
edges: [specializes::docs/hoplite/glossary:ranking-function]
---

A feature's rarity, scored as the inverse of its document frequency.

## Examples

- IDF over a word: a rare term (a content feature) outweighs a common one in the BM25 score.
- IDF over a tag: a rarely-used tag (a metadata feature) outweighs a common one in IDF-weighted Jaccard.
