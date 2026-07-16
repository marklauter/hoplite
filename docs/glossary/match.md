---
title: match
summary: "To evaluate a search expression over the corpus, returning the documents that satisfy it."
tags: [hoplite, glossary]
created: 2026-06-30
status: evolving
---

To evaluate a [[search-expression]] over the corpus, returning the documents that satisfy it.

## Examples

- `find documents where tags contains "todo"` — one crisp [[filter]] condition.
- `find documents where body semantic-search: "shield wall" and tags contains "todo"` — a scoring [[semantic-search]] condition and a crisp [[filter]] condition, composed in one expression.
