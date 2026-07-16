---
title: Reconcile hoplite-navigation to the read model
summary: "hoplite-navigation.md still teaches the five-move taxonomy (survey, filter, walk, project, read) and pre-rename vocabulary. Reconcile it against hoplite-read-model.md after the RDF-aligned terms are reviewed and locked."
tags: [note, hoplite, todo]
created: 2026-07-02
status: open
priority: medium
effort: medium
---

# Reconcile hoplite-navigation to the read model

[[docs/specs/hoplite-navigation.md]] predates the read model and the RDF terminology alignment. Its move taxonomy — survey / filter / walk / project / read, flagged in its own open question 4 — conflicts with the operations/condition split in [[docs/specs/hoplite-read-model.md]], and its prose still uses "predicate" in the retired read-side sense that is now [[docs/glossary/condition.md]].

Trigger: run this after the RDF-aligned terms — [[docs/glossary/predicate.md]], [[docs/glossary/condition.md]], [[docs/glossary/search-expression.md]], and the rest of the evolving read-side cluster — are reviewed and locked. Reconciling against unreviewed terms risks doing the sweep twice; the lock pass is deliberately held until that review.
