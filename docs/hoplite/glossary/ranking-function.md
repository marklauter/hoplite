---
title: ranking-function
summary: "A function that scores candidates to order them."
tags: [hoplite, glossary]
created: 2026-06-20
document.status: locked
---

A function that scores candidates to order them.

## Examples

- `bm25` scores a document against a lexical query.
- `jaccard` scores the overlap between two documents — the relationship itself, an edge.
- `weighted-idf` scores a feature by its rarity.
- A weighted walk scores only the edges on the current node's frontier — never the whole graph — to choose the next step.
