---
title: Provenance is a tree — fact vs claim, split by assertion
summary: "Feature provenance is a two-level tree, not a flat axis. The top split is fact vs claim, decided by whether anyone asserts the feature; claims split again by originator into declared (author) and inferred (engine). `assert` is the genus both author and engine perform."
tags: [note, glossary, features]
created: 2026-06-19
status: evolving
---

# Provenance is a tree — fact vs claim, split by assertion

Feature provenance is a two-level tree, not a flat three-valued axis. Two splits, each decided by one question:

```
feature
├── fact          ← asserted by no one; given by the document's existence   [provenance: intrinsic]
└── claim         ← asserted by someone                                      [provenance: asserted]
    ├── declared  ← the author asserts, by authoring        (declare = author's species)
    └── inferred  ← the engine asserts, from evidence       (infer/discover = engine's species)
```

1. Asserted at all? → `fact` vs `claim`. This is the `intrinsic` / `assert` line.
2. Within claims, which originator? → `declared` (author) vs `inferred` (engine).

## `assert` is the genus

`assert` is the genus, to make a claim, performed by both the author and the engine. `declare` is the author's species (assert by authoring); `infer`/`discover` is the engine's species (assert from evidence). Hoplite still asserts based on its inference: inference is the engine's way of making a claim, the same kind of feature as the author's, because both have an originator who could be wrong. A `fact` has no originator.

## Consequences for the glossary (status: evolving, not locked)

The glossary cluster (`fact`, `claim`, `assert`, `infer`, `intrinsic`) nearly encodes this, but needs a cascade of edits:

- `fact.md` — rewrite off the genus. The current "A feature intrinsic to a document" is circular with `intrinsic.md` (fact → intrinsic → fact) and defines by location, not essence. Replace it with "A feature asserted by no one; given by the document's own existence." That defines it by the same axis (`assert`) as `claim`, with no pointer loop.
- `assert.md` — re-cut as the genus. It is currently `category: authoring act`, `aliases: [authored, declare, declared]`. Drop the `declare` alias and broaden the category to "act": the engine asserts too, so `declare` is not a synonym of the genus.
- `declare` — promote to its own node. It is the author's species of `assert`, currently buried as an alias. This is the term the model is missing.
- `claim.md`, `infer.md`, `intrinsic.md` — nearly intact. `claim` stays "a feature someone asserts"; `infer`/`discover` is the engine's leaf; `intrinsic` keeps owning the provenance ("originated by no one") while `fact` names the kind.

## Consequences for the in-flight specs

Both `wip` concept drafts are mis-cut against this tree and must defer to the glossary:

- `docs/specs/hoplite-feature-taxonomy.md` — the binary is mis-stated. It locks origin as the binary intrinsic / asserted and pushes `inferred` off the feature axis entirely ("inferred edges are outputs... never tokens"). The binary is `fact` vs `claim`, and `inferred` sits on the claim side, not off-axis. What taxonomy was actually protecting — "only declared is an input feature; inferred edges are outputs" — is a real input/output distinction, but a separate axis from provenance. Taxonomy fused the two and used "not a feature" to mean "not an input." That fusion is the bug to fix on its lock.
- `docs/specs/hoplite-affordances.md` — the trinity is mislabeled. Line 15 and OQ5 write the provenance trinity as "asserted, intrinsic, inferred," mixing the genus (`asserted`) with a leaf (`inferred`). The three leaves are `intrinsic` / `declared` / `inferred`; the affordances' "asserted" should read `declared` (the author leaf).

## Open seam

`assert` as genus is agreed; the glossary rework is the next real step (after today's skills rework). Record each node change through `/glossary`, one node at a time. Carry the input/output axis, which is distinct from provenance, into the taxonomy/ranking spec rather than reviving it as a provenance value.
