---
title: infer
summary: "To derive a feature from evidence."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
retired: [discover, deduce]
---

To derive a [[glossary/feature]] from evidence.

## Mechanism

Inference feeds [[glossary/assert|assertion]]. The engine infers a candidate
edge and its [[glossary/confidence|confidence]]. It asserts the edge only when that confidence clears
the threshold. Inference is unconditional: the sub-threshold findings are
inferred and never asserted.
