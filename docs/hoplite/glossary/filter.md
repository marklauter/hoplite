---
title: filter
summary: "A crisp predicate: it tests a node or edge for membership — a tag, a property, a stereotype — in or out, with no score."
tags: [hoplite, glossary]
created: 2026-06-19
status: evolving
is-a: "[[predicate]]"
contrast: "[[semantic-search]]"
---

A crisp predicate: it tests a node or edge for membership — a tag, a property, a stereotype — in or out, with no score.

## Examples

- `tags contains "todo"` — set membership over a label.
- `status = "draft"` — a property value.
- `stereotype/cites` — an edge predicate for a [[walk]].
