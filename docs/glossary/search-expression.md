---
title: search expression
summary: "A boolean composition of conditions; the input match evaluates over the corpus."
tags: [glossary]
created: 2026-07-01
status: evolving
has-a: "[[condition]]"
---

A boolean composition of [[condition|conditions]]; the input [[match]] evaluates over the corpus.

## Examples

- `tags contains "todo"` — a single crisp condition.
- `body semantic-search: "shield wall" and tags contains "todo"` — a scoring condition and a crisp condition, composed.
