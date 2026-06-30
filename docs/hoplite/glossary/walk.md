---
title: walk
summary: "To traverse chosen edges from seed nodes, gathering a neighborhood to a given depth."
tags: [hoplite, glossary]
created: 2026-06-19
status: evolving
---

To traverse chosen edges from seed nodes, gathering a [[neighborhood]] to a given depth.

## Notes

- Seeds come from a [[match]]; a further match picks the subset to walk from.
- Walk follows an edge [[predicate]] — only the chosen stereotypes or kinds, not every edge. Depth zero is no walk.
- Walk is polymorphic over both graphs: the corpus graph and the vocabulary graph. [[survey]] is walk over the vocabulary graph.
