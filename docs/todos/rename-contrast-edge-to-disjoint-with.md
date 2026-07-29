---
title: Rename the contrast edge to disjoint-with
summary: the glossary skill now names the symmetric sibling edge disjoint-with; the corpus entries, domain-modeling, and the demo material still say contrast.
tags: [todo, glossary, skills, corpus]
created: 2026-07-25
priority: medium
status: open
---

# Rename the contrast edge to disjoint-with

`plugins/hoplite-skills/skills/glossary/SKILL.md` renamed the symmetric edge from `contrast` to `disjoint-with`. Everything outside that skill still carries the old key.

## Why

`contrast` read as disambiguation, as in "you might have confused this with Y". The edge asserts more than that. Two terms share a genus and no instance belongs to both. `disjoint-with` is the ontology term for that relation, and it makes the coherence walk precise, since a term disjoint with a class it descends from is unsatisfiable.

## Sites

- `docs/glossary/bm25.md`, `jaccard.md`, `claim.md`, `relationship.md`, `filter.md` carry `contrast:` in frontmatter.
- `plugins/hoplite-skills/skills/domain-modeling/SKILL.md` names the edge.
- `plugins/hoplite-skills/references/expressing-edges.md` line 106 and `plugins/hoplite-skills/hooks/test_edge_grammar.py` use `contrast` as demo material for block-list syntax. The edge grammar is open-vocabulary, so neither depends on the name. Swap both for an inert key rather than the live one.

## Shape of done

- No frontmatter key named `contrast` outside `quary/`.
- `filter` gains the reciprocal edge on `semantic-search`, which the symmetric rule requires and it lacks today.
- The `## Contrasts` body section is dropped. The relation is an edge, and the boundary it draws is already carried by the differentiae.
