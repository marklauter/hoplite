---
title: infer
summary: "To derive a relationship from evidence."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
retired: [discover, deduce]
---

To derive a [[relationship]] from evidence.

## Mechanism

Inference feeds [[assert|assertion]]. The engine infers a candidate relationship — its [[predicate]] and its [[confidence]]. It asserts the relationship as an [[edge]] only when the confidence clears the threshold. Inference is unconditional: the engine infers every candidate but asserts only those above the threshold.
