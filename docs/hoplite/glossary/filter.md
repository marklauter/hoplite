---
title: filter
summary: "A crisp condition: it tests a node or edge for membership — a tag, a property, a predicate — in or out, with no score."
tags: [hoplite, glossary]
created: 2026-06-19
status: evolving
is-a: "[[condition]]"
contrast: "[[semantic-search]]"
---

A crisp condition: it tests a node or edge for membership — a tag, a property, a predicate — in or out, with no score.

## Examples

- `tags contains "todo"` — set membership over a label.
- `status = "draft"` — a property value.
- `cites` — an edge condition for a [[walk]], naming a predicate by its label.
