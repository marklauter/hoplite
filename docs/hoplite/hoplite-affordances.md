---
title: Features give rise to affordances; signifiers advertise them
summary: The concept layer over the read and write surfaces. An affordance is an action possibility the corpus offers the agent; features give rise to affordances; they split into write (assert features) and read (query features); and a signifier — an MCP description or an ambient skill — is what makes an affordance perceivable, since one the agent cannot see is dead.
tags: [hoplite, affordances, spec]
created: 2026-06-04
document.status: wip
---

# Features give rise to affordances

An affordance is an action possibility a thing offers a capable actor — a relationship between the features of the thing and the capabilities of the actor. In Hoplite the thing is a document; the actor is the agent in one of two roles — the author who writes, the researcher who reads; and a feature is anything Hoplite knows about a document ([[docs/hoplite/hoplite-feature-taxonomy.md]]).

## The affordances

Affordances come in two kinds, by actor: the author asserts over features, the researcher queries over features. The available feature set for read operations includes both authored and inferred features, so it is inherently richer than the author's feature set.

Write affordances — authoring ([[docs/hoplite/hoplite-authoring.md]]):

- a title affords distilling the whole document into one unifying phrase, so others recognize its value at a glance.
- a summary affords compressing the document to a lede, so others judge it without reading the body.
- tags afford sorting the document into shared categories, so others gather it with its kind.
- the document's schema affords composition — the author chooses which named axes it holds and coins new keys, tags, or stereotypes, so the holding itself becomes ranked, queryable signal.
- a property affords setting the document's value on an axis it holds, so others filter, order, and rank by the value.
- an alias affords keeping the document reachable under an old name, so references survive a rename.
- a wikilink affords binding this document to another, so the relationship is traversable, not merely mentioned.
- a stereotype affords typing that link — cites, supersedes, contradicts — so others query by what it means, not just that it exists.

Read affordances — navigation ([[docs/hoplite/hoplite-navigation.md]]):

- a title or summary affords judging a document's relevance before reading its body.
- a tag affords filtering the corpus to a concept by set membership, wherever it is filed.
- the schema affords meta queries — surveying which axes the corpus defines, and filtering by the presence of one, the tracked set apart from untracked.
- a property affords filtering, ordering, and ranking the corpus by a value on an axis.
- an alias affords resolving a document by any of its identities.
- a wikilink affords walking to a neighbor the directory tree cannot show.
- a stereotype affords filtering edges by relationship — walking only what supersedes or contradicts a document.
- an edge's kind affords choosing authored links or inferred relatives — the discovered ones reach relatives no one declared.
- content affords searching by meaning rather than by literal string.
- a creation date affords ordering and ranging the corpus by time.
- a result set affords projecting its hits — ordering and ranking them, and choosing which values each returns — so the researcher reviews the most relevant findings first.

## Signifiers — the cue that makes an affordance perceivable

A signifier is the perceptible cue that advertises an affordance. Read affordances signify through MCP tool descriptions; write affordances signify through ambient info-injection skills. The signifier carries a fidelity contract — it must advertise the affordance the mechanism actually offers, no more — and the build-time mail-merge keeps the two in sync, so a description never promises a move the mechanism does not make. A signifier the agent cannot perceive leaves the affordance dead, which is why the signifiers stay implicit in the surfaces the agent already reads rather than living as a separate layer.


## open questions

1. Sync the README map. This file is now the concept doc, not navigation; `hoplite-navigation.md` is the read half; `hoplite-authoring.md` is the write half. The Map and Documents list still describe the old shape.
2. Signifiers may earn their own section once the MCP descriptions and ambient skills are written — the fidelity contract between an affordance and its signifier is the seam to formalize.
3. Carry the schema-ranking seam into the ranking model. The schema affordance now owns the meta layer here — compose it on write, query it on read (like reflection over a type rather than its runtime values). What remains for the ranking spec: IDF-weighted ranking, a core ranking feature, acts on the presence of a property — the holding, not only the value — so the schema layer ranks, not only filters. The mechanism (how presence enters the IDF-Jaccard score) belongs in [[docs/hoplite/hoplite-feature-taxonomy.md]].
