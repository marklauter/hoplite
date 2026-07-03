---
title: statement
summary: "A triple asserted into the graph — subject, predicate, object — weighted by confidence."
tags: [hoplite, glossary]
created: 2026-07-03
status: evolving
retired: [fact]
has-a:
    - "[[resource]]"
    - "[[predicate]]"
    - "[[confidence]]"
---

A triple asserted into the graph — subject, predicate, object — weighted by [[confidence]].

Every statement is an assertion; provenance names whose. The retired *fact* — an intrinsic feature — was a statement named by its provenance; a frontmatter statement about a document is a [[claim]].

## Examples

- `document:x status:todo` — the author's statement, [[assert]]ed at confidence 1.0: a [[claim]].
- a fingerprint on a document — the importer's statement, computed from the bytes. The retired *fact*.
- an inferred neighborhood edge — the engine's statement, graded below 1.0.
