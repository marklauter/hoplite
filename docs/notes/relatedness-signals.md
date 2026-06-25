---
title: Relatedness is mutual information observed through many channels
summary: "Every channel two documents can be found related through — declared links, classification, content, graph topology, time, provenance, filesystem, and usage — divided first by whether the author declared the relationship or it emerged from the data, and unified by one principle: a signal's strength is the rarity of the shared feature. Hoplite's deliverable signals are a subset of this territory."
tags: [hoplite, signal, design, note]
created: 2026-05-31
---

# Relatedness is mutual information observed through many channels

Two documents are related when they are not independent — knowing something about one reduces uncertainty about the other. Relatedness is mutual information between documents along some channel, and the unit of relatedness is a shared or linked feature.

A signal's strength is the self-information of the shared feature, not the fact of sharing. Two documents sharing "the" carry almost no bits; two sharing "recursive-CTE traversal" carry many. A co-occurrence is informative in proportion to how improbable the shared feature is on its own — pointwise mutual information. Proximity in time or space is the same principle in continuous form: the shared feature is the tightest window that contains both, and a narrower window is rarer. Every emergent signal below is the co-occurrence of a high-entropy feature, and the threshold knob is, formally, a cut on PMI.

The full enumeration follows from one observation: every feature space over which documents are statistically non-independent is a relatedness channel. The channels divide first by authorship — authored, where the author asserted the relationship, or emergent, where it falls out of the data. Within each, a signal is also directed or undirected, binary or graded.

## Authored channels

The author asserted the relationship; the signal is simply true — ungraded, it can't be wrong, and it reaches only what was typed.

### Declared linkage

- direct reference — A points to B (directed, binary)
- backlink — the same edge read in reverse, who points to B (directed, binary)
- typed edge — the link carries a label like supersedes, derives-from, or contradicts; the kind is itself a feature (directed, binary)
- ghost reference — a link whose target doesn't exist yet, relating the citing document to an intended one (directed, binary)
- transclusion — one document embeds another's content, strictly stronger than reference (directed, binary)

### Declared classification

- shared tag — classification kinship; relate by kind even when topics diverge (undirected, graded by tag rarity)
- shared property — same project, status, or author frontmatter value (undirected, graded by value rarity)
- identifier overlap — shared distinctive name tokens (undirected, graded; emergent when the overlap is coincidental)

## Emergent channels

No one asserted the relationship; it falls out of a feature two documents share — so it is graded, rankable, and fallible, and it reaches connections no author declared.

### Content

- lexical overlap — shared rare terms, exact n-gram coincidence; IDF is self-information made literal (undirected, graded)
- semantic similarity — closeness in distributional-meaning space, catching paraphrase the words miss (undirected, graded by distance)
- topic kinship — a shared latent topic distribution (undirected, graded)
- named-entity co-mention — both reference the same person, system, file, or ticket (undirected, graded by entity rarity)
- verbatim reuse — near-duplicate passages, unattributed copy/paste; the redundancy the "corpus repeats itself" problem describes (undirected, graded)
- shared external citation — both cite the same outside source, bibliographic coupling on external references (undirected, graded)

### Graph topology

Read off the edges, not the values. This family needs no document content at all.

- co-citation — both pointed to by the same third document, shared inbound (undirected, graded by count)
- bibliographic coupling — both point to the same third document, shared outbound (undirected, graded by count)
- common neighbors — overlap of full neighborhoods (undirected, graded)
- geodesic proximity — a short path between them in the graph (undirected, graded by distance)
- community co-membership — falling in the same densely connected cluster (undirected, graded)
- hub role — a document many point to is central; relatedness to the corpus, not to one peer (directed-derived, graded)

### Temporal

- creation proximity — made close in time, sharing the intent then underway; arcs (undirected, graded by elapsed time)
- co-modification — edited in the same window or session (undirected, graded)
- phase alignment — both in the genesis, build, or refactor phase of the same arc (undirected, graded)
- sequence — explicit next and prev, or implicit succession (directed; authored when the order is declared)

### Provenance

The corpus is under git; this channel sits unused today.

- change coupling — changed together in the same commit; logical coupling from repository mining, often a stronger relatedness predictor than content (undirected, graded by co-change frequency)
- same author (undirected, graded by author prolificacy)
- commit-message reference — a commit ties two documents in prose (undirected; authored when the message names them)
- branch co-membership — born or living on the same branch (undirected)

### Spatial

The hierarchy fails as an ontology, yet location is still a weak relatedness signal. The graph demotes the directory from sole organizer to one low-weight channel rather than discarding it.

- same directory — siblings in the tree (undirected, binary)
- path-token overlap — shared path-name tokens (undirected, graded)
- tree distance — steps apart in the directory tree (undirected, graded)

### Behavioral

Not logged today; a real channel, named for completeness.

- co-retrieval — surfaced together by the same query (undirected, graded)
- co-access — read together in the same agent session, access coupling (undirected, graded)

## The cross-cutting axes

Authored versus emergent is the primary division above. Independent of channel, every signal also varies along axes that determine how the graph may use it.

- directed vs undirected — directionality is itself information, reference versus co-citation; collapsing it loses bits
- binary vs graded — only graded signals carry a threshold knob and a recall-precision tradeoff
- symmetric vs asymmetric — embedding distance is symmetric, supersedes is not; PMI is symmetric, conditional probability is not
- transitive vs not — similarity is roughly transitive, which enables clustering; typed edges usually are not
- value-borne vs structure-borne — the signal lives in the content and metadata, or in the shape of the graph; topology is the only family needing no content at all

## The unifying statement

There is one relatedness signal — mutual information — observed through many channels. The authored channels deliver it at full confidence and no reach beyond what was typed. Every emergent channel trades confidence for reach: each is a projection of the documents into a feature space where co-occurrence of a rare feature betrays a dependency no author declared.

## What Hoplite reaches

- have now, from current data — lexical overlap, topic kinship, shared tag, creation proximity, co-citation, bibliographic coupling, shared external citation, hub role, verbatim reuse
- have the data, not yet indexed — the provenance family (change coupling, co-modification, author), drawn from git history
- needs new capability — semantic embeddings, topic models, named-entity extraction, behavioral logging

The differentiator, stated precisely: grep, FTS, and a reading agent harvest only the authored and content channels. Topology, time, provenance, and usage exist only once the corpus is a graph with history. That is the territory unique to Hoplite.

## See also

- [[docs/hoplite/hoplite.md]] — the deliverable subset, framed for the agent
- [[docs/hoplite/hoplite-graph.md]] — the model that stores these signals
