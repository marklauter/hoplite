---
title: "Every document emits a set of features: intrinsic facts and asserted claims"
summary: "The feature taxonomy that grounds the rest of the spec: features split by origin into intrinsic (recovered from the bytes and their history) and asserted (supplied by the author), crossed by the dimension they measure, with relatedness scored as IDF-weighted Jaccard over the unified set."
tags: [spec, features]
created: 2026-06-08
status: evolving
---

# Every document emits a set of features: intrinsic facts and asserted claims

A feature is anything Hoplite knows about a document.

Two cuts partition the same feature set, and they are orthogonal. Origin asks who supplied a feature: intrinsic features are recovered from the document and its history; asserted features come from the author — the meaning the bytes do not carry on their own. Dimension asks what a feature measures: content, metadata, neighborhood, and history — the vision's unified set. A feature has exactly one origin and one dimension, and neither determines the other. A shingle is intrinsic content; a tag is asserted metadata; created-time is intrinsic history; a wikilink is asserted neighborhood. Ranking ignores both cuts: every feature contributes tokens to one bag, and relatedness is their rarity-weighted overlap.

Edges carry a third distinction, which is a relationship origination and not a feature cut. An edge originates as declared, property-derived, or inferred. A declared edge is a wikilink the author wrote. A property-derived edge falls out deterministically from shared metadata — every document tagged `todo`, every document whose `status` holds the same value, forms a subgraph; the holding of a property and each of its values cut their own graphs. An inferred edge is scored rather than derived: IDF overlap across features, semantic nearness, shared intent or topic, proximity in time, folder, or git author. Declared is the author's assertion; property-derived is mechanism, reproducible exactly from the asserted properties; inferred is judgment. Only the declared edge is an input feature, because the author supplied it. Property-derived and inferred edges are outputs of relatedness, computed from the bags and never tokens in them. This is the line graph.md crosses when it lists inferred as a feature kind.

## Intrinsic features — recovered from the bytes and their history

Intrinsic features are recovered without the author asserting anything; they fall out of the document and its commit history.

- content carries two features. Shingles are the lexical surface — overlapping token windows, the only feature grep reaches. A vector embedding is the semantic surface — meaning that survives paraphrase, reachable by no lexical tool.
- history carries two features. created-time is the document's genesis. git provenance is the commit and authorship trail — the same edit recorded as an authorial act in the commit graph.

Two of these sit on a seam worth naming now. created-time is intrinsic by nature — a recovered fact about when the document began — yet it is transcribed into frontmatter, which is the asserted surface. git provenance is the mirror: it looks intrinsic because it is recovered rather than written, yet a commit is an authorial act, and it lives in the commit graph outside the document bytes. The deciding line is not who caused the feature but whether the author wrote it into the document as an assertion of meaning. By that line both are intrinsic — the author transcribes `created` for portability without asserting it as meaning, and a commit records history without being written into the page. This is why the intrinsic gloss reaches past the bytes to the commit graph.

## Asserted features — supplied by the author

Asserted features are supplied by the author — the meaning the bytes do not carry until the author writes it. They are what the write-side affordances assert: the surface [[docs/specs/hoplite-authoring.md]] describes and [[docs/specs/hoplite-frontmatter.md]] reifies, and the contract the indexer reads.

- tags — unnamed set membership that classifies the document.
- properties — named axes carrying a value, such as `status` or `severity`; both the holding of the property and its value are assertable signal.
- title and summary — the first-class fields; the summary is the projection the agent judges before reading the body.
- declared edges — wikilinks, the neighborhood dimension's only asserted input feature.

This list is the enumeration frontmatter closes over. When it changes, frontmatter and the indexer's input contract change with it; nothing else in the spec adds an asserted feature.

## Relatedness — IDF-weighted Jaccard over the unified feature set

A document is a bag of feature tokens drawn from every dimension at once, and relatedness is the rarity-weighted overlap of two bags. IDF supplies the weight — the improbability of the coincidence — so a rare shared feature counts for more than a common one. Shared shingles, a shared tag, a shared `status` value, a common wikilink target, the same created-time, the same folder or author each contribute a token, and the property-derived and inferred subgraphs fall out of those coincidences rather than entering as separate signals. The graph neighborhood is one feature among many here, not its own pipeline. This is what collapses graph.md's three independent channels and its separate walk into a single ranked space.

Meaning arrives in two layers over this bag. The first is the inferred subgraph structure — the relatedness the overlap itself surfaces. The second is semantic nearness from vectors, which no discrete token captures; it rides alongside the Jaccard score rather than inside it. How the two combine into one ranking is a mechanism the indexer spec owns, not this taxonomy — the seam to name here is that both are in scope.

# mining stock — relocate from hoplite-graph.md

The "Discover — inferring latent, emergent structure" section at the bottom of [[docs/specs/hoplite-graph.md]] is feature-and-relatedness content lifted from the vision draft. It belongs here. Pull it in when this doc is locked; the unified-feature-set model above supersedes its "three independent feature spaces" framing.

# open seams

The orthogonality reframe and the three-valued edge origination are folded into the framing above. What remains for the lock:

- Fingerprint. content_hash serves identity and change detection, not relatedness — MinHash over shingles is the content estimator. It is deliberately absent from the feature list above; confirm that call when the indexer lands rather than reviving it as a feature.
- The vector and Jaccard combination. The relatedness section names semantic nearness as a second layer but defers how it folds into an IDF-Jaccard score. That belongs to the indexer and ranking spec; carry the seam there.
- graph.md reconciliation. graph's three channels are the dimension cut; this taxonomy is the origin cut; the two are orthogonal axes, not competitors. Pull the "Discover" section in — see mining stock — and rewrite its "three independent feature spaces" framing to match.
