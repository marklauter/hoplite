---
title: statement
summary: "A triple asserted into the graph — subject, predicate, object — weighted by confidence."
tags: [glossary]
created: 2026-07-03
status: evolving
retired: [fact, feature]
has-a:
    - "[[resource]]"
    - "[[predicate]]"
    - "[[confidence]]"
---

A triple asserted into the graph — subject, predicate, object — weighted by [[confidence]].

## Kinds

- a [[claim]] states a value about one document.
- a [[relationship]] relates two resources.

## Examples

- `document:x status:todo` — the author's statement, [[assert]]ed at confidence 1.0: a [[claim]].
- a fingerprint on a document — the importer's statement, computed from the bytes. The retired *fact*.
- an inferred neighborhood relationship — the engine's statement, graded below 1.0.

## Notes

- A document's body is not a statement: content stays text behind the search index, with the fingerprint as the importer's claim standing in.
- The retired *fact* was the importer's claim; the retired *feature* — anything knowable about a document — was the statement before the model had the word.
- *Triple* names the shape — three positions; *statement* names the weighted row.
