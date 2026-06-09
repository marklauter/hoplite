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

# document review

A content and fidelity review of this stub against the locked vision ([[docs/hoplite/hoplite.md]]). The carve-out is faithful, with one coherence gap that is load-bearing even at stub stage.

## The orthogonality gap

Origin and dimension are two independent cuts of the same feature set, and this stub runs them together. The vision ranks over a set cut by dimension — content, metadata, neighborhood, history (hoplite.md line 35). This document re-cuts the same set by origin — intrinsic against asserted. The stub implies the origin cut supersedes the dimension cut, but two dimensions fall through:

- Neighborhood has no home in either bucket. The relatedness lede leans on it ("the graph neighborhood is one feature among many"), yet the member lists name only "wikilinks (declared edges)" under asserted. That equates the author's declared edge with the engine-recovered structural feature — co-citation, shared connectors — which is the feature-relationship blur this document exists to fix.
- Metadata splits across both buckets: tags assert, created-time is intrinsic. The `created` seam note treats this as a one-off when it is the general case.

The resolution is the insight itself: origin says where a feature came from; dimension says what it measures; the two are orthogonal, and ranking ignores both — every token lands in one rarity-weighted bag. State that, give the structural feature an origin home distinct from the declared wikilinks it is computed from, and the carve is coherent. This also governs the graph.md reconciliation: graph's three channels are the dimension cut, this taxonomy is the origin cut, and the two coexist as orthogonal axes rather than competing.

## Nits for the full write

- Fingerprint double-counts. MinHash is the estimator for the content feature; content_hash serves identity and change detection, not relatedness. The vision lists "content," not "content and fingerprint." Drop it or annotate it.
- Git provenance is the mirror of the `created` seam. `created` looks asserted — it sits in frontmatter — yet is intrinsic; git provenance looks intrinsic — recovered, not written — yet a commit is an authorial act living in the commit graph, outside the document bytes. Widen the intrinsic gloss from "the bytes" to "the bytes and the commit graph." The deciding line is whether the author wrote the feature into the document, not whether a person caused it.
- Discovered edges are outputs of relatedness, never input features. The asserted bucket's edge members are the declared subset by construction. The model holds; make this explicit when the section lands.

## What holds

- The two-axes move — feature origin against edge origin, with inferred demoted from a feature kind to a relationship origination — is correct and repairs the conflation in [[docs/hoplite/hoplite-graph.md]], whose title and opening still place inferred on the feature axis.
- "Collapses the three channels and the separate walk into one ranked space" is authorized by the vision and correctly marks graph.md as the stale doc.
- Title and summary belong in asserted. Economics and thesis carry no drift.

## Recommendation

Fold the orthogonality reframe into the stub now — the two-axes paragraph and the relatedness lede — while the section bodies stay to be written. It changes how the whole document gets written and it is the hinge for reconciling graph.md, so it earns its place before the full pass. The nits wait for that pass.
