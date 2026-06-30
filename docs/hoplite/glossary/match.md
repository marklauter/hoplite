---
title: match
summary: "To evaluate a predicate expression over the corpus, returning the documents that satisfy it."
tags: [hoplite, glossary]
created: 2026-06-30
status: evolving
---

To evaluate a predicate expression over the corpus, returning the documents that satisfy it.

## Examples

- `find documents where tags contains "todo"` — one crisp [[filter]] predicate.
- `find documents where body semantic-search: "shield wall" and tags contains "todo"` — a scoring [[semantic-search]] predicate and a crisp [[filter]] predicate, composed in one expression.
