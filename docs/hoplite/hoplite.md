---
title: Hoplite - Map your corpus; discover latent signal
summary: Hoplite turns a markdown corpus into a graph an agent searches by topic and walks by relationship — surfacing the declared, described, and latent signal a directory tree can't express.
document:
  tags: [hoplite, overview, spec]
  created: 2026-05-30
---

# Hoplite - Map your corpus; discover latent signal

<introduction>

## The problem

- grep finds direct text matches with regex, not semantic matches by topic
- glob finds files by name, but the whole idea can't be contained in a name
- exploration
  - reading unrelated files burns tokens for nothing
  - reading unrelated files injects bias into every future turn
- directory hierarchy doesn't match real-world relationships between concepts
- a concept that matters in many places is filed in one folder; hierarchy forces a single home
- relationships between documents are invisible — the links you drew, the kinship of shared tags, the similarity no one wrote down; the filesystem shows containment, never connection
- matches are unranked and arrive unordered, so the agent can't tell what's central from what barely qualifies
- the same idea gets rewritten across several notes; the agent reads redundant copies or never sees they converge
- a document shows what it points to, never who points back; the filesystem has no inbound view
- references to not-yet-written documents vanish — the backlog of intended work is invisible — no ghosts
- the agent re-derives or contradicts a past decision because bounded context hides the prior art

## The solution

progressive disclosure — the agent selects only the content it needs, cutting token waste and the bias from unrelated content. the mechanisms beneath it:

- semantic search (BM25 via FTS) matches documents by topic, not literal text
- ranked hits carry summaries, so the agent judges from the lede what to read or follow next
- walk follows declared links and discovered similarity to gather a neighborhood the directory can't show
- predicate scoping narrows to a classification instead of a folder
- discovery surfaces latent signal — relationships nobody authored
- discovered similarity clusters near-duplicates into one neighborhood instead of N strangers
- directed edges walk both ways — `direction: in` reveals who references this document
- ghost nodes make the unwritten enumerable, so open loops stay visible
- find surfaces prior art by topic; walk reaches the decision's rationale before the agent repeats it
- tags crosscut folders — find by classification gathers a concept wherever it lives

## Latent signal

- signal no one authored as a relationship, yet real and useful — the connection you never wrote down
- it emerges from what you did write: the dates, the tags, the words — not from links you drew
- arcs — documents created close in time tend to share the intent of whatever was underway; the design arc (genesis → build → refactor) is one shape, every activity traces its own; never declared, it falls out of time
- topical kinship — two documents about the same thing with no link between them; similarity surfaces the relationship the author missed
- classification kinship — documents sharing a tag relate by kind even when their topics diverge
- the differentiator — grep, FTS, and an LLM reading files all harvest the explicit; latent signal is what only the graph surfaces

## Map and discover

## Read

## Write

## The substrate (the graph)

## Use cases
