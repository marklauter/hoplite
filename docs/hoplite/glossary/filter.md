---
title: filter
summary: "A crisp condition: it tests a resource or edge for membership — a tag, a claim, a predicate — in or out, with no score."
tags: [hoplite, glossary]
created: 2026-06-19
status: evolving
is-a: "[[condition]]"
contrast: "[[semantic-search]]"
---

A crisp condition: it tests a resource or edge for membership — a tag, a claim, a predicate — in or out, with no score.

## Examples

- `tags contains "todo"` — set membership over a label.
- `status = "draft"` — a claim value.
- `cites` — an edge condition for a [[walk]], naming a predicate by its label.
