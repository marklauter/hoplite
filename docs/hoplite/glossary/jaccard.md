---
title: Jaccard
summary: "The ratio of two sets' intersection to their union."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
is-a: "[[glossary/ranking-function]]"
contrast: "[[glossary/bm25]]"
---

The ratio of two sets' intersection to their union.

## Examples

- Hoplite scores two documents' relatedness by the Jaccard overlap of their feature bags — the inferred similarity edge.

## Contrasts

- `bm25` — Jaccard measures document↔document set overlap, symmetric; `bm25` scores a query→document lexical match, asymmetric. Both get spoken of as "relatedness."
