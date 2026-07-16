---
title: Ship the stereotype edge-annotation layer
summary: One coordinated work cycle delivering the open-vocab stereotype model on the mentions edge plus the two v1 instances (contradicts, not-related). Three child notes collected here as one shippable unit.
tags: [note, hoplite, edges, stereotypes, design, todo, epic]
created: 2026-05-27
priority: medium
effort: medium
status: open
---

# Ship the stereotype edge-annotation layer

One coordinated work cycle delivering the open-vocab stereotype model on the `mentions` edge plus the two v1 instances (`contradicts`, `not-related`). Three child notes collected here as one shippable unit.

## What ships together

- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] — parent design. Owns the schema (`edge_property` rows keyed by `"stereotype"`), the dual frontmatter shape (dot-flat and nested-mapping), the inline wikilink syntax, the canonical seed vocabulary, and the open-vocab policy.
- [[docs/todos/add-contradicts-as-an-authored-edge-kind.md]] — first canonical instance. Rhetorical-negative asserted disagreement.
- [[docs/todos/add-not-related-as-a-structural-negative-edge-kind.md]] — second canonical instance. Structural-negative; subtracts from inferred `related` via the existing mention-skip path.

The third and fourth seed stereotypes — `supports` and `supersedes` — surface in the parent design and in `plugins/hoplite/components/hoplite/mcp-reference.md` once the layer lands. They do not need dedicated design notes for v1.

## Why one shippable unit

The parent owns the parser rules — flat frontmatter properties (a node property is a scalar; an edge is a `<stereotype>: "[[target]]"` wikilink value) and inline stereotype comments (`[[target]]<!--stereotype-->`). Without it, neither child can be implemented. The two children prove the model works on different semantic categories (rhetorical-negative and structural-negative), so shipping the parent without at least both instances leaves the seed vocabulary unvalidated.

Splitting the children into separate ships would force premature decisions on the open questions in each — default traversal behavior for stereotyped mentions in particular. One coordinated implementation pass resolves them together.

## What is out of scope

Called out in the parent design and worth restating here:

- Migration of property keys. Done — the property keys settled on the flat, Obsidian-native contract in [[docs/specs/frontmatter.md]] (`tags`/`created` bare, edges as `<stereotype>: "[[target]]"`). The stereotype *emit path* is still part of this epic; no key rename is pending.
- Edge-level properties beyond stereotype (tagging an existing edge). Frontmatter addresses stereotype edges cleanly; non-stereotype edge properties have an unsolved addressing problem.
- Default traversal behavior for stereotyped mentions in `relatives()`. Deferred to the expression-language redesign — see the parent design's open questions.

## Dependencies

This is independent of the scale-readiness cluster at [[docs/todos/hoplite-scales-to-the-cross-repo-knowledge-graph.md]]. Stereotype semantics work the same regardless of corpus size or pair-similarity scoring function. Ship order between the two clusters is free.

## See also

- [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]] — the cycle that established the mention-skip pattern this layer inherits.
- [[docs/todos/hoplite-scales-to-the-cross-repo-knowledge-graph.md]] — the other parent todo from this session. Different code paths; concurrent or sequential, free order.
