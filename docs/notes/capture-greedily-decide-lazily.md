---
title: Capture greedily, decide lazily — defer to keep options open
summary: Good design defers hard-to-reverse decisions until information accrues; greedy capture is what keeps them deferrable.
tags: [note, architecture, design]
created: 2026-06-19
status: evolving
---

Good design defers hard-to-reverse decisions until information accrues; greedy capture is what keeps them deferrable.

## The principle

Robert Martin, *Clean Architecture*: "The way you keep software soft is to leave as many options open as possible, for as long as possible," and "A good architect maximizes the number of decisions not made." The warrant is informational — "the longer you wait to make those decisions, the more information you have with which to make them properly."

## Deferral requires preservation

Deferring a decision only works if the option survives the wait. Martin can defer the database because the architecture materializes the option as a boundary. Defer without preserving and it is amnesia, not deferral. So greedy capture is the precondition: writing the contested term down early is what keeps the decision makeable later. The two halves are one rule. Capture greedily so you can decide lazily.

## The last responsible moment

The rule is not "decide as late as possible" but the last responsible moment (Lean): defer until the cost of staying open exceeds the value of waiting. Past that point, indecision is itself the expense.

## How hoplite implements it

The `status` axis is the deferral mechanism. An `evolving` glossary entry is an option held open; `locked` is a decision spent. The drift sweep is the deadline: accumulating inferred-but-not-asserted overlap signals a deferral that has run past its moment and needs locking. The open-vocabulary edge stereotype is the worked example. The vocabulary is deliberately not fixed into a closed enum; it is left to real edges to populate. See [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]].
