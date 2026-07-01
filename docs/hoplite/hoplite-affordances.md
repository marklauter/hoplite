---
title: Features give rise to affordances
summary: "The concept layer over the write and read surfaces, and the enumeration of every affordance the corpus offers the agent — the build's todo list. An affordance is an action possibility a document offers the agent in one of two roles: the author who asserts features, the researcher who queries them. Features give rise to affordances; the doc lists them all, write and read; a signifier — an MCP description or an ambient skill — advertises an affordance and trails its mechanism, since one the agent cannot perceive is dead."
tags: [hoplite, affordances, spec]
created: 2026-06-04
status: evolving
---

# Features give rise to affordances

An affordance is an action possibility a thing offers a capable actor — a relationship between the features of the thing and the capabilities of the actor. In Hoplite the thing is a document, or the corpus the documents compose; the actor is the agent in one of two roles — the author who writes, the researcher who reads; and a feature is anything Hoplite knows about a document ([[docs/hoplite/hoplite-feature-taxonomy.md]]).

## The affordances

Affordances come in two kinds, by actor: the author asserts over features, the researcher queries over them. The author asserts only one origin of feature; the researcher ranges over all three — asserted, intrinsic, and inferred ([[docs/hoplite/hoplite-feature-taxonomy.md]]) — so the read surface is inherently richer than the write surface.

Write affordances — authoring ([[docs/hoplite/hoplite-authoring.md]]):

- a title affords distilling the whole document into one unifying phrase, so others recognize its value at a glance.
- a summary affords compressing the document to a lede, so others judge it without reading the body.
- tags afford sorting the document into shared categories, so others gather it with its kind.
- the document's schema affords composition — the author chooses which named axes it holds and coins new properties, tags, or stereotypes, so the holding itself becomes ranked, queryable signal.
- a property affords setting the document's value on an axis it holds, so others filter, order, and rank by the value.
- an alias affords keeping the document reachable under an old name, so references survive a rename.
- a uri affords filing and naming the document, so others find it among its neighbors and reach it by a stable address.
- a wikilink affords binding this document to another, so the relationship is traversable, not merely mentioned.
- a stereotype affords typing a wikilink — cites, supersedes, contradicts — so others query by what the link means, not just that it exists.
- a ghost link affords naming a document before it is written, so the unwritten work stays an open loop instead of lost.
- an external link affords citing a resource outside the corpus, so the citation becomes a node others reach and backlink.
- a transclusion affords composing the document from parts — embedding another's content — so shared material lives in one home and reads in many.
- a block anchor affords naming a target inside the document, so others link to a section, not just to the file.

Read affordances — navigation ([[docs/hoplite/hoplite-navigation.md]]):

- a title or summary affords judging a document's relevance before reading its body.
- a tag affords filtering the corpus to a concept by set membership, wherever it is filed.
- the schema affords meta queries — surveying which axes the corpus defines, and filtering by the presence of one, the tracked set apart from untracked.
- a property affords filtering, ordering, and ranking the corpus by a value on an axis.
- an alias affords resolving a document by any of its identities.
- a uri affords reaching a document by its address and finding its neighbors — documents sharing a directory are likely related.
- a section affords retrieving part of a document and addressing it by anchor — its outline surveyed before reading — so a hit returns the relevant section, not the whole file.
- centrality affords ranking documents by authority — the most-referenced first — and finding the orphans no document points to.
- size affords budgeting the read — sorting by cost and spending tokens where the signal per token is highest.
- a code block affords filtering the corpus to documents carrying examples, by language.
- frontmatter completeness affords surfacing under-described documents that rank poorly because they are thin.
- task state affords surfacing documents with open work and gathering the live backlog.
- a wikilink affords walking to a neighbor the directory tree cannot show.
- a stereotype affords filtering edges by relationship — walking only what supersedes or contradicts a document.
- an edge's kind affords choosing asserted links or inferred relatives — the inferred ones reach relatives no one asserted.
- a ghost affords enumerating the corpus's unwritten work — the backlog of open loops.
- an external reference affords enumerating a document's outbound citations.
- a mention affords walking to every document that names an entity — a file, a symbol, a ticket — each entity standing as its own node.
- content affords searching by meaning rather than by literal string.
- similarity affords finding a document's near-duplicates — the overlapping work to merge.
- a creation date affords ordering and ranging the corpus by time.
- a last-modified time affords ranking by recency and surfacing stale or fresh work.
- an author affords gathering documents written by the same hand.
- co-change affords reaching documents edited in the same commits — related by shared history.
- churn affords judging a document's maturity, settled or still changing.
- a result set affords projecting its hits — ordering and ranking them, and choosing which values each returns — so the researcher reviews the most relevant findings first.

## Signifiers — the cue that makes an affordance perceivable

A signifier is the perceptible cue that advertises an affordance. Read affordances signify through MCP tool descriptions; write affordances signify through ambient info-injection skills. The signifier carries a fidelity contract — it must advertise the affordance the mechanism actually offers, no more — and the build-time mail-merge keeps the two in sync, so a description never promises a move the mechanism does not make. A signifier the agent cannot perceive leaves the affordance dead, which is why the signifiers stay implicit in the surfaces the agent already reads rather than living as a separate layer.


## Open questions

1. Sync the README map. This file is now the concept doc, not navigation; `hoplite-navigation.md` is the read half; `hoplite-authoring.md` is the write half. The Map and Documents list still describe the old shape.
2. Signifiers may earn their own section once the MCP descriptions and ambient skills are written — the fidelity contract between an affordance and its signifier is the seam to formalize.
3. Carry the schema-ranking seam into the ranking model. The schema affordance now owns the meta layer here — compose it on write, query it on read (like reflection over a type rather than its runtime values). What remains for the ranking spec: IDF-weighted ranking, a core ranking feature, acts on the presence of a property — the holding, not only the value — so the schema layer ranks, not only filters. The mechanism (how presence enters the IDF-Jaccard score) belongs in [[docs/hoplite/hoplite-feature-taxonomy.md]].
4. This enumeration is the build's todo list — nothing here is materialized yet; the proof-of-concept remnants are being refactored away. As each affordance ships, its signifier — the MCP tool description or ambient skill — gets authored to match, never ahead: the fidelity contract means a signifier advertises only a move the mechanism already makes. The doc drives the build; the signifiers trail it.
5. Group the read list by feature origin — asserted, intrinsic, inferred ([[docs/hoplite/hoplite-feature-taxonomy.md]]) — to dogfood the provenance trinity. Deferred: reordering a 26-item list asserts a structure, a lock-time decision, not a wip one. Left unstructured until discovery closes.
