---
title: Every document is a bag of intrinsic and asserted features
summary: "The feature taxonomy that grounds the rest of the spec — features split into intrinsic (recovered from the bytes) and asserted (supplied by the author), and a document's relatedness is IDF-weighted Jaccard over the unified feature set."
tags: [hoplite, features, spec]
created: 2026-06-08
document.status: stub
---

# Every document is a bag of intrinsic and asserted features

Stub. The feature taxonomy that grounds the rest of the spec — the umbrella term for everything Hoplite knows about a document, split by who supplied it. The model is locked in the vision ([[docs/hoplite/hoplite.md]]); this document carves it out of [[docs/hoplite/hoplite-graph.md]], which currently blurs features with relationship origination, and it feeds [[docs/hoplite/hoplite-frontmatter.md]], the reification of the asserted half.

Two axes that this document keeps separate, because graph.md currently runs them together: a feature is intrinsic or asserted (who supplied it); an edge is declared or discovered (who asserted the relationship). Inferred is a relationship origination, not a feature kind.

## Intrinsic features — recovered from the bytes

To be written. Features that fall out of the document and its history: content (shingles), fingerprint, created-time, git provenance. Cheap to recover, though grep reaches only the content. (Seam to resolve: `created` is written in frontmatter yet names an intrinsic attribute — genesis time — so it sits on the asserted surface but classifies as intrinsic.)

## Asserted features — supplied by the author

To be written. Features the author supplies beyond what the bytes carry: wikilinks (declared edges), tags, properties, stereotypes, title and summary. These are the write-side affordances — the surface [[docs/hoplite/hoplite-declare-and-describe.md]] describes and [[docs/hoplite/hoplite-frontmatter.md]] reifies. This list is the contract the indexer reads and the frontmatter doc closes over.

## Relatedness — IDF-weighted Jaccard over the unified feature set

To be written. A document is a bag of rarity-weighted feature tokens across every dimension at once; relatedness is the rarity-weighted overlap of two bags. IDF supplies the weighting — the improbability of the coincidence — so a rare shared feature counts for more than a common one. This collapses the old "three channels" and the separate walk into one ranked space; the graph neighborhood is one feature among many, not its own pipeline.

# mining stock — relocate from hoplite-graph.md

The "Discover — inferring latent, emergent structure" section at the bottom of [[docs/hoplite/hoplite-graph.md]] is feature-and-relatedness content lifted from the vision draft. It belongs here. Pull it in when this doc is locked; the unified-feature-set model above supersedes its "three independent feature spaces" framing.
