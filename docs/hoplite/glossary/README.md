---
title: Hoplite glossary
summary: Index of the Hoplite domain-term nodes under docs/hoplite/glossary/. Links every term and keeps the synonym crosswalk.
tags: [hoplite, glossary, reference]
created: 2026-06-05
status: evolving
---

# Hoplite glossary

The Hoplite domain terms, one node per term. This page links them and keeps the synonym crosswalk; the canonical model lives in the docs under [See also](#see-also).

## Terms

- [[affordance]]
- [[assert]]
- [[asserted]]
- [[bm25]]
- [[claim]]
- [[condition]]
- [[condition-atom]]
- [[confidence]]
- [[corpus]]
- [[document]]
- [[edge]]
- [[fact]]
- [[feature]]
- [[filter]]
- [[fingerprint]]
- [[frontmatter]]
- [[ghost]]
- [[graph]]
- [[idf]]
- [[infer]]
- [[intrinsic]]
- [[jaccard]]
- [[knowledge-graph]]
- [[match]]
- [[minhash]]
- [[neighborhood]]
- [[node]]
- [[predicate]]
- [[projection]]
- [[property]]
- [[provenance]]
- [[ranking-function]]
- [[relationship]]
- [[search-expression]]
- [[semantic-search]]
- [[slug]]
- [[summary]]
- [[survey]]
- [[tags]]
- [[title]]
- [[uri]]
- [[vocabulary]]
- [[walk]]

## Crosswalk

Where a Hoplite term maps onto an external standard. A mapping is listed only where it is exact; near-fits import confusion instead of leverage.

- [[node]] ≈ an RDF resource — a subject or object.
- [[predicate]] ≈ the RDF predicate; OWL `ObjectProperty`. UML calls it a stereotype — the retired name.
- [[property]] ≈ OWL `DatatypeProperty`. RDF's own schema layer names the literal-valued predicates *properties*, so Hoplite's predicate/property split mirrors the standard's.
- [[edge]] ≈ a reified RDF statement: the subject–object pair with its weight; one triple per predicate the edge carries.
- [[condition]] ≈ the leaf of a SQL `<search condition>`. SQL's grammar calls the leaf a predicate; Hoplite cedes that word to RDF.
- [[search-expression]] ≈ the SQL `<search condition>` — the whole boolean expression a `WHERE` clause holds.

## See also

- [[docs/hoplite/hoplite]] — problem statement and scope.
- [[docs/hoplite/hoplite-feature-taxonomy]] — the feature taxonomy: the two origins (intrinsic, asserted) and the IDF-weighted Jaccard relatedness over the unified feature set.
- [[docs/hoplite/hoplite-affordances]] — the affordances concept: features give rise to affordances; the write/read split; signifiers.
- [[docs/hoplite/hoplite-graph]] — the structure: nodes, edges, properties, predicates, vocabulary.
- [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs]] — the two-graph and namespace-address model.
- [[docs/hoplite/README]] — the document map.
