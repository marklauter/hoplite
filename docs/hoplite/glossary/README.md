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

- [[node]] ≈ an RDF resource — a term in any position of a statement.
- [[predicate]] ≈ the RDF predicate — the middle *position* of a statement, which an edge or a property fills. UML calls the edge-label sense a stereotype — the retired name.
- [[edge]] ≈ OWL `ObjectProperty`: a pure relation, one of the two kinds licensed for the predicate position.
- [[property]] ≈ OWL `DatatypeProperty`: a key, the other licensed kind. RDF's own schema layer names the literal-valued predicates *properties*, so Hoplite's edge/property split mirrors the standard's.
- [[statement]] ≈ the RDF statement: the reified [[claim]] — [[assert]] is the act, the statement is the artifact it leaves, and `confidence` is the degree of attestation.
- [[condition]] ≈ the leaf of a SQL `<search condition>`. SQL's grammar calls the leaf a predicate; Hoplite cedes that word to RDF.
- [[search-expression]] ≈ the SQL `<search condition>` — the whole boolean expression a `WHERE` clause holds.

## See also

- [[docs/hoplite/hoplite]] — problem statement and scope.
- [[docs/hoplite/hoplite-feature-taxonomy]] — the feature taxonomy: the two origins (intrinsic, asserted) and the IDF-weighted Jaccard relatedness over the unified feature set.
- [[docs/hoplite/hoplite-affordances]] — the affordances concept: features give rise to affordances; the write/read split; signifiers.
- [[docs/hoplite/hoplite-graph]] — the structure: nodes, edges, properties, predicates, vocabulary.
- [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs]] — the two-graph and namespace-address model.
- [[docs/hoplite/README]] — the document map.
