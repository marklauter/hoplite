---
title: Edge predicates are glossary-governed, reduced like noun terms
summary: "An edge predicate (né stereotype) goes through the same glossary reduction as a noun term — a word plus the smallest phrase that unpacks it, locked. The glossary governs the verb vocabulary as it governs the noun vocabulary; that discipline is the antidote to predicate sprawl, paid instead of a closed enum or an ungoverned free-for-all."
tags: [note, decision, hoplite, predicates, glossary]
created: 2026-07-01
status: evolving
---

# Edge predicates are glossary-governed, reduced like noun terms

An edge [[docs/hoplite/glossary/predicate.md]] is a relationship label — the RDF-predicate sense, made a first-class model element rather than a bare triple slot. It is governed the same way a noun term is: it emerges freely from use, and when it settles it earns a glossary entry, reduced to a word plus the smallest phrase that unpacks it, then locked. The glossary already governs the noun vocabulary; this extends it to the verb vocabulary.

Emergence stays open — a new predicate is a doc change, not a schema migration, and the parser does not warn on unknown values (see [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]], which records the mechanism under the retired name). Governance is the reduction applied *after* a predicate proves itself, on the capture-greedily, lock-lazily timing (see [[docs/notes/capture-greedily-decide-lazily.md]]). Governance is not a closed set.

## Alternatives

- **Closed enum of predicates.** Predefine the relationship types in the schema. Rejected: it contradicts the self-organizing-schema thesis — the vocabulary is not known up front, so the enum cannot be written ahead of the edges that need it. It also turns every new relationship into a migration.
- **Ungoverned open vocabulary.** Let predicates accrete purely by use, like tags, with no reduction step. This was the status quo, and its own note flags the failure: synonym drift (`supports` vs `endorses` vs `agrees-with`) accumulates undetected, and the vocabulary rots into an unqueryable bag of near-duplicate predicates. That is the exact death of every ontology project.
- **Keep the UML name `stereotype` instead of `predicate`.** Rejected 2026-07-01: the read-side term that held the word was renamed to [[docs/hoplite/glossary/condition.md]], freeing `predicate`, and the default predicate on a bare link makes the typing total — every edge carries at least one — so the RDF mapping is exact and the standard's word carries its load. Scope is edges only: property keys keep `property`, matching RDF's own split (`owl:ObjectProperty` vs `owl:DatatypeProperty`). `stereotype` is retired into `predicate` with an alias; the glossary README carries the crosswalk.

## Why

The trade-off is curation cost against a queryable vocabulary.

- **It buys** the drift antidote the ungoverned model lacks. A predicate reconciled through the glossary the way noun synonyms are — merged, aliased, or contrasted — keeps the vocabulary small and meaningful, so a query by relationship means something. It buys this without pre-committing to a schema, so the self-organizing thesis survives.
- **It costs** a standing obligation: the glossary reduction now runs over verbs too, so someone must sweep emergent predicates and reduce them, the same drift sweep the noun glossary needs. The schema removed from the DDL comes due here, as governance work.

This is the concrete form of the wider boundary in [[docs/notes/hoplite-is-rdf-at-source-property-graph-at-index.md]]: three columns is a clean knowledge graph only if the predicate layer is governed; skip the governance and it is an undifferentiated bag of triples nobody can query.
