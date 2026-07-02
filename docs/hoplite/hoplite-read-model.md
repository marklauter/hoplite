---
title: Read model — match, walk, projection, survey
summary: The read side reduced to structure — a few operations over the corpus and one input they share. Match evaluates a search expression; walk expands its result into a neighborhood; projection shapes a result set; survey reads the vocabulary. Filter and semantic-search are kinds of condition, not operations. Sparse by intent; mechanism and expression structure are deferred.
tags: [hoplite, navigation, spec]
created: 2026-06-30
status: evolving
---

# Read model

The read side reduces to a few operations and one input they share. This doc holds the structure; the per-term kernels live in the [[docs/hoplite/glossary/README.md|glossary]], and the mechanism is deferred.

## Operations

- [[docs/hoplite/glossary/match.md|match]] — evaluate a [[docs/hoplite/glossary/search-expression.md|search expression]] over the corpus, return the documents that satisfy it.
- [[docs/hoplite/glossary/walk.md|walk]] — expand a match's seeds along edge conditions into a [[docs/hoplite/glossary/neighborhood.md|neighborhood]].
- [[docs/hoplite/glossary/projection.md|projection]] — order, cap, and select fields on a result set.
- [[docs/hoplite/glossary/survey.md|survey]] — match and walk over the vocabulary graph.

Read — the handoff to full content — is not an operation here. The agent crosses to its own Read tool once a projection survives.

## Condition

Match and walk both consume a [[docs/hoplite/glossary/condition.md|condition]]; conditions compose into the [[docs/hoplite/glossary/search-expression.md|search expression]] match evaluates. Two kinds:

- [[docs/hoplite/glossary/filter.md|filter]] — crisp membership, in or out.
- [[docs/hoplite/glossary/semantic-search.md|semantic-search]] — matches by meaning and attaches a relevance score.

## Deferred

- The search-expression structure itself — how conditions compose and pass — is undefined. It waits on the real data importer; expressions are written against real data, not ahead of it.
- Mechanism — FTS, vectors, the index that carries a walk — stays in [[docs/hoplite/hoplite-graph.md]].

## See also

- [[docs/hoplite/hoplite-navigation.md]] — the affordance-framed walkthrough of these moves; its move taxonomy predates this model (its open question 4 — survey/filter/walk/project/read) and needs reconciling against the operations/condition split here.
- [[docs/hoplite/hoplite-affordances.md]] — features give rise to these read affordances.
