---
title: relationship
summary: "A semantic association between two documents expressed by an edge."
tags: [hoplite, glossary]
created: 2026-06-21
status: locked
is-a: "[[claim]]"
has-a:
    - "[[predicate]]"
    - "[[edge]]"
    - "[[confidence]]"
---

A semantic association between two [[document]]s expressed by an [[edge]].

## Structure

A relationship has three parts. The [[edge]] — a bare attachment between two resources — binds it to the graph. The [[predicate]] names the kind of association: `cites`, `supports`, `contradicts`. The [[confidence]] measures how far to trust it: an authored relationship carries 1.0, an inferred one less.
