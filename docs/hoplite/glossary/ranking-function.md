---
title: ranking-function
summary: "A function that scores candidates to order them."
tags: [hoplite, glossary]
created: 2026-06-20
document.status: evolving
edge.related: [docs/hoplite/glossary/bm25.md, docs/hoplite/glossary/jaccard.md, docs/hoplite/glossary/weighted-idf.md]
---

A function that scores candidates to order them.

## Examples

- `bm25` scores a document against a lexical query.
- `jaccard` scores the overlap between two documents — the relationship itself, an edge.
- `weighted-idf` scores a feature by its rarity.
