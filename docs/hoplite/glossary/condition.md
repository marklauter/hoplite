---
title: condition
summary: "A test of a node or edge, true or false; the corpus narrows to those it holds for."
tags: [hoplite, glossary]
created: 2026-06-30
status: evolving
---

A test of a node or edge, true or false; the corpus narrows to those it holds for.

## Kinds

- a crisp [[filter]] condition — in or out, no score.
- a scoring [[semantic-search]] condition — also attaches a relevance score, which [[projection]] orders by.

Conditions compose into a [[search-expression]], which [[match]] evaluates. A condition is built from one or more [[condition-atom]]s, each a single [[vocabulary]] uri.
