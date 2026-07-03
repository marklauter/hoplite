---
title: Hoplite glossary
summary: Index of the Hoplite domain-term entries under docs/hoplite/glossary/. Links every term and keeps the synonym crosswalk.
tags: [hoplite, glossary, reference]
created: 2026-06-05
status: evolving
---

# Hoplite glossary

The Hoplite domain terms, one entry per term. This page links them and keeps the synonym crosswalk; the canonical model lives in the docs under [See also](#see-also).

## Terms

- [[affordance]]
- [[assert]]
- [[bm25]]
- [[claim]]
- [[condition]]
- [[condition-atom]]
- [[confidence]]
- [[corpus]]
- [[document]]
- [[filter]]
- [[fingerprint]]
- [[frontmatter]]
- [[ghost]]
- [[graph]]
- [[idf]]
- [[infer]]
- [[jaccard]]
- [[knowledge-graph]]
- [[match]]
- [[minhash]]
- [[neighborhood]]
- [[predicate]]
- [[projection]]
- [[ranking-function]]
- [[relationship]]
- [[resource]]
- [[search-expression]]
- [[semantic-search]]
- [[slug]]
- [[statement]]
- [[summary]]
- [[survey]]
- [[tags]]
- [[title]]
- [[uri]]
- [[vocabulary]]
- [[walk]]

## Crosswalk

Where a Hoplite term maps onto an external standard. A mapping is listed only where it is exact; near-fits import confusion instead of leverage.

- [[resource]] — RDF's universal term, adopted outright: a term in any position of a statement. RDF's "node" is merely positional (a subject or object), so the property-graph word retired into resource.
- [[predicate]] ≈ the RDF predicate — the middle *position* of a statement, which a relationship or a claim key fills. UML calls the relationship-label sense a stereotype — the retired name.
- [[relationship]] ≈ OWL `ObjectProperty`: a semantic association between two resources, its label one of the two licensed kinds.
- [[claim]] ≈ OWL `DatatypeProperty`: a statement about a document, its key the other licensed kind. RDF names these *properties* — the retired name here; Hoplite names the statement by what it does.
- [[statement]] ≈ the RDF statement: [[assert]] is the act, the statement is the artifact it leaves, and `confidence` is the degree of attestation — the retired provenance trinity collapsed into that one weight.
- [[condition]] ≈ the leaf of a SQL `<search condition>`. SQL's grammar calls the leaf a predicate; Hoplite cedes that word to RDF.
- [[search-expression]] ≈ the SQL `<search condition>` — the whole boolean expression a `WHERE` clause holds.

## See also

- [[docs/hoplite/hoplite]] — problem statement and scope.
- [[docs/hoplite/hoplite-feature-taxonomy]] — the feature taxonomy: the two origins (intrinsic, asserted) and the IDF-weighted Jaccard relatedness over the unified feature set.
- [[docs/hoplite/hoplite-affordances]] — the affordances concept: statements give rise to affordances; the write/read split; signifiers.
- [[docs/hoplite/hoplite-graph]] — the structure: resources, relationships, claims, vocabulary.
- [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs]] — the two-graph and namespace-address model.
- [[docs/hoplite/README]] — the document map.
