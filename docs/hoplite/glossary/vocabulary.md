---
title: vocabulary
summary: "The meta labels (property keys and edge predicates) and bounded property values mapped within the knowledge graph."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
---

The meta labels ([[property]] keys and [[edge]] [[predicate|predicates]]) and bounded property values mapped within the knowledge graph.

## Examples

- a property key — `status`, `created`.
- a value expressed under a key — `locked`, or the tag `hoplite` under `tags`.
- a predicate — `is-a`, `cites`.

## Discussion

A property key partitions the corpus. Asserting `status` on a document places it
in the class of documents that carry a status; a journal entry, which asserts no
`status`, stays outside that class. A key is not a slot a document fills — its
presence is a claim of class membership.

This is what makes the vocabulary surveyable. Discovering a key reveals a class
to filter on, and walking the key to its values subdivides that class. Surveying
the vocabulary is how an agent composes a [[condition]].
