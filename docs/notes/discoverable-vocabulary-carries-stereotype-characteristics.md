---
title: The discoverable vocabulary carries each stereotype's algebraic characteristics
summary: "Hoplite's surveyable vocabulary should record, per stereotype, its OWL-style algebraic characteristics (symmetric, transitive, inverse-of, asymmetric…), not just its name. A small closed set of characteristics governs an open, unbounded stereotype vocabulary — so the agent discovers how a relation behaves, and the reasoner computes edge closure from it instead of the author hand-applying conventions."
tags: [note, hoplite, vocabulary, design]
created: 2026-06-20
document.status: evolving
---

# The discoverable vocabulary carries each stereotype's algebraic characteristics

`docs/hoplite/glossary:stereotype` is open vocabulary — an author coins any verb that reads `<source> <stereotype> <target>`. The surveyable vocabulary in [[docs/hoplite:hoplite]]'s solution section ("the agent discovers the vocabulary… surveys the vocabulary, encoded in the map") today exposes *which* stereotypes exist. It should also expose *how each behaves*.

## The idea

Borrow OWL's move: **don't enumerate relations, characterize them.** OWL governs an unbounded set of relations with a small, closed set of **property characteristics**:

- `SymmetricProperty` — holds both ways (`contrast`, `not-related`).
- `TransitiveProperty` — chains (`is-a`: A→B→C ⊢ A→C).
- `inverseOf` — A→B implies B→A under a *different* name (`has-a` ↔ `part-of`, `cites` ↔ `cited-by`).
- `AsymmetricProperty`, `Reflexive`/`Irreflexive`, `FunctionalProperty` — as needed.

Record these characteristics **on the stereotype in the vocabulary**, alongside its name. Then:

1. **The agent discovers behavior, not just names.** Surveying the vocabulary returns "`is-a` is transitive, `contrast` is symmetric" — the agent knows how a walk over that stereotype composes before issuing it.
2. **The reasoner computes closure.** Per [[the-agent-problem-is-the-agency-problem]]-adjacent reasoning, hoplite already infers (statistical relatedness) and derives (property subgraphs); characteristics give it a *deductive* mode over declared edges — materialize the symmetric inverse, chase the transitive chain — instead of storing every implied edge by hand.
3. **A closed set governs an open one.** Coin any verb; classify it by a fixed handful of characteristics. Infinite vocabulary, finite governance.

## This formalizes a rule we already hand-built

The glossary skill's edge-stereotype rule — *"direction follows dependency; only symmetric edges reciprocate"* — is a two-element subset of OWL property characteristics (`symmetric` vs `directional`). We rediscovered it independently. Manually reciprocating a `contrast::` edge (adding the reverse edge + bullet by hand) is the author doing, at write time, what a reasoner does from `SymmetricProperty` at query time. Recording characteristics in the vocabulary supersedes the hand-application.

## Adopt standard names for the backbone

Where a recognized relation already exists, use its name rather than coining:

- **SKOS** (W3C, the standard for exactly this kind of concept vocabulary): `broader`/`narrower` ≈ `is-a`, `related` ≈ associative, `prefLabel`/`altLabel`/`hiddenLabel` ≈ canonical/`aliases`/`document.retired`, `definition`/`scopeNote`/`example` ≈ `summary`/Also/Examples. The glossary is structurally a SKOS concept scheme.
- **WordNet**: hypernym/hyponym (is-a), meronym/holonym (part-of), antonym (≈ `contrast`), synonym (≈ aliases).
- **Winston, Chaffin & Herrmann (1987)**: the named six-way part-whole taxonomy, if `has-a`/part-of needs splitting.
- **OBO Relation Ontology / BFO**: a curated, reusable by-name relation set.

So the model is hybrid: **standard names for the recognized few, open coinage for the tail — and every stereotype, named or coined, is governed by its declared characteristics, not by enumeration.**

## Open seams

- **Where characteristics live.** The stereotype vocabulary is interned in `schema.sql` (`stereotype` table, today just `id, label`). Characteristics would be columns or a companion table — a closed enum of characteristic flags per label. Design when the deductive layer is built.
- **Which characteristics earn day-one support.** `symmetric` and `transitive` are already implied by the glossary rule; `inverseOf` needs a paired-name convention. Start with the two we use; add as real stereotypes demand.
- **Reasoner scope.** This is the deductive third mode for hoplite (alongside inductive relatedness and deterministic property subgraphs). Closure over declared stereotype edges — transitive `is-a`, symmetric `contrast` — is the first target.
