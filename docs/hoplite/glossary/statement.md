---
title: statement
summary: "A triple asserted into the graph — subject, predicate, object — weighted by confidence."
tags: [hoplite, glossary]
created: 2026-07-03
status: evolving
retired: [fact, feature]
has-a:
    - "[[resource]]"
    - "[[predicate]]"
    - "[[confidence]]"
---

A triple asserted into the graph — subject, predicate, object — weighted by [[confidence]].

Every statement is an assertion; [[confidence]] carries the trust — the author's and importer's word at 1.0, the engine's guess graded below. A statement about one document is a [[claim]]; the retired *fact* was the importer's claim. A document's body is not a statement: content stays text behind the search index, with the fingerprint as the importer's claim standing in. The retired *feature* — anything knowable about a document — was the statement before the model had the word.

## Examples

- `document:x status:todo` — the author's statement, [[assert]]ed at confidence 1.0: a [[claim]].
- a fingerprint on a document — the importer's statement, computed from the bytes. The retired *fact*.
- an inferred neighborhood edge — the engine's statement, graded below 1.0.
