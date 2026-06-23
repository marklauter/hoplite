---
title: vocabulary
summary: "The set of keys and values of properties and stereotypes of edges asserted within the knowledge graph."
tags: [hoplite, glossary]
created: 2026-06-19
status: locked
---

The set of keys and values of [[property|properties]] and [[stereotype|stereotypes]] of [[edge|edges]] [[asserted]] within the knowledge graph.

## Examples

- a property key — `status`, `created`.
- a value expressed under a key — `locked`, or the tag `hoplite` under `tags`.
- a stereotype — `is-a`, `cites`.

## Discussion

A property key partitions the corpus. Asserting `status` on a document places it
in the class of documents that carry a status; a journal entry, which asserts no
`status`, stays outside that class. A key is not a slot a document fills — its
presence is a claim of class membership.

This is what makes the vocabulary surveyable. Discovering a key reveals a class
to filter on, and walking the key to its values subdivides that class. Surveying
the vocabulary is how an agent composes a predicate.
