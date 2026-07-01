---
title: Edge stereotypes are glossary-governed, reduced like noun terms
summary: "An edge stereotype is a relationship predicate, and it goes through the same glossary reduction as a noun term — a word plus the smallest phrase that unpacks it, locked. The glossary governs the verb vocabulary as it governs the noun vocabulary; that discipline is the antidote to predicate sprawl, paid instead of a closed enum or an ungoverned free-for-all."
tags: [note, decision, hoplite, stereotypes, glossary]
created: 2026-07-01
status: evolving
---

# Edge stereotypes are glossary-governed, reduced like noun terms

An edge [[docs/hoplite/glossary/stereotype.md]] is a relationship predicate — the RDF-predicate sense, made a first-class model element rather than a bare triple slot. It is governed the same way a noun term is: it emerges freely from use, and when it settles it earns a glossary entry, reduced to a word plus the smallest phrase that unpacks it, then locked. The glossary already governs the noun vocabulary; this extends it to the verb vocabulary.

Emergence stays open — a new stereotype is a doc change, not a schema migration, and the parser does not warn on unknown values (see [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]]). Governance is the reduction applied *after* a stereotype proves itself, on the capture-greedily, lock-lazily timing (see [[docs/notes/capture-greedily-decide-lazily.md]]). Governance is not a closed set.

## Alternatives

- **Closed enum of stereotypes.** Predefine the relationship types in the schema. Rejected: it contradicts the self-organizing-schema thesis — the vocabulary is not known up front, so the enum cannot be written ahead of the edges that need it. It also turns every new relationship into a migration.
- **Ungoverned open vocabulary.** Let stereotypes accrete purely by use, like tags, with no reduction step. This is the status quo, and its own note flags the failure: synonym drift (`supports` vs `endorses` vs `agrees-with`) accumulates undetected, and the vocabulary rots into an unqueryable bag of near-duplicate predicates. That is the exact death of every ontology project.
- **Rename the term to `predicate` for RDF alignment.** Rejected: `predicate` is already locked as the read-side query condition ([[docs/hoplite/glossary/predicate.md]]), and RDF's "predicate" is coarser than Hoplite's vocabulary — it buckets stereotype, property key, and query constraint into one word. The RDF correspondence belongs in the glossary crosswalk, not in a rename.

## Why

The trade-off is curation cost against a queryable vocabulary.

- **It buys** the drift antidote the ungoverned model lacks. A stereotype reconciled through the glossary the way noun synonyms are — merged, aliased, or contrasted — keeps the predicate vocabulary small and meaningful, so a query by relationship means something. It buys this without pre-committing to a schema, so the self-organizing thesis survives.
- **It costs** a standing obligation: the glossary reduction now runs over verbs too, so someone must sweep emergent stereotypes and reduce them, the same drift sweep the noun glossary needs. The schema removed from the DDL comes due here, as governance work.

This is the concrete form of the wider boundary in [[docs/notes/hoplite-is-rdf-at-source-property-graph-at-index.md]]: three columns is a clean knowledge graph only if the predicate layer is governed; skip the governance and it is an undifferentiated bag of triples nobody can query.
