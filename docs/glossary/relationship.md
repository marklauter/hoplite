---
title: relationship
summary: "A semantic association between two resources."
tags: [glossary]
created: 2026-06-21
status: evolving
retired: [edge]
is-a: "[[statement]]"
has-a: "[[confidence]]"
contrast: "[[claim]]"
---

A semantic association between two resources.

## Structure

A relationship's label names the kind of association — `cites`, `supports`, `contradicts` — a member of the `relationship` namespace (`relationship:cites`), licensed for the predicate position. The [[confidence]] measures how far to trust it: an authored relationship carries 1.0, an inferred one less.

## Contrasts

- `claim` — a relationship relates two resources; a claim states a value about one document.
