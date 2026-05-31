---
title: Hoplite - Map your corpus; discover latent signal
summary: <summary goes here when document is finished>
document:
  tags: [hoplite, overview, spec]
  created: 2026-05-30
---

# Hoplite - Map your corpus; discover latent signal

<introduction>

## The problem - glob-grep-read loop is the wrong tool for the job

The agent wastes turns and context exploring blind alleys, corrupts future turns, and fails to find critical information. All lead to the agent making decisions biased by the wrong input, or rehashing decisions that were one semantic search away. Failures compound.

1. Search matches the wrong way — an agent must find information that matters before it can use it.
   - grep finds direct text matches with regex, not semantic matches by topic
   - glob finds files by name, but the whole idea can't be contained in a name
   - matches are unranked and arrive unordered, so the agent can't tell what's central from what barely qualifies
2. Reading blind is costly — when search comes up wrong, the agent falls back to reading, and reading unranked and unfiltered costs twice.
   - reading unrelated files burns tokens for nothing
   - reading unrelated files injects bias into every future turn
3. The tree is the wrong tool for an ontology — and a directory gives each file one home, though the idea belongs in many.
   - directory hierarchy doesn't match real-world relationships between concepts
   - a concept that matters in many places is filed in one folder; hierarchy forces a single home
4. Connection is invisible — deeper still, even what the tree does hold, it can't connect.
   - relationships between documents are invisible — the links you drew, the kinship of shared tags, the similarity no one wrote down; the filesystem shows containment, never connection
   - a document shows what it points to, never who points back; the filesystem has no inbound view
   - references to not-yet-written documents vanish — the backlog of intended work is invisible — no ghosts
5. The corpus's memory goes unused — so the corpus repeats itself, the agent rewriting and rehashing what's already locked in.
   - the same idea gets rewritten across several notes; the agent reads redundant copies or never sees they converge
   - bounded context hides prior art — the agent can't find the decision already made
     - re-derive — re-solves a solved problem; wasted work, usually the same answer
     - contradict — lands on a different answer and breaks consistency; two conflicting decisions now drift apart

## The solution - mapping the corpus; declare, describe, discover, and read relationships

Mapping content via explicit, semantic, and emergent relationships and meta descriptions exposes new affordances for the agent that allow progressive disclosure, reduce token burn-rate and unwanted bias, maximize the smart-zone, and lead to better agent output. The agent can identify and consume only the content it needs.

### Declare and describe - applying explicit structure

1. Declare and describe content — author the explicit relationships and descriptions; structure that escapes the glob-grep-read loop.
   - declare a relationship — point one document at another
   - describe a document or an edge — properties on a document, a stereotype on a link
2. Find — locate what matters by meaning, not by string or path.
   - semantic search matches documents by topic, not literal text
   - ranked hits carry summaries, so the agent judges from the lede what to read or follow next
   - document properties crosscut folders — find by one to gather a concept wherever it lives
3. Walk — follow the relationships a directory tree can't hold.
   - walk follows declared links and discovered similarity to gather a neighborhood the directory can't show
   - a relationship declared once travels both ways — what a document points to, and who points back
   - ghosts make the unwritten enumerable, so open loops stay visible
4. Discover — surface the signal nobody wrote down.
   - discovery surfaces latent signal — relationships nobody authored
   - discovered similarity clusters near-duplicates into one neighborhood instead of N strangers

Find surfaces prior art by topic. Walk reaches the decision's rationale before the agent repeats it.

### Discover - inferring latent structure

The corpus holds undiscovered relationships — implicit kinship that emerges from shared features — topics, tags, citations, commits, authors, proximity of time and space. A declared relationship is asserted and treated as fact. A latent signal is implied — present only as a pattern, recovered by inference.

Every inferred relationship is graded by the improbability of the coincidence — a rare shared feature, or a narrow shared window. Two documents sharing a common word carry zero signal; two sharing a rare term carry a strong signal. That's why latent signal can be ranked.

1. From what you wrote — the signal already latent in your own content and metadata.
   - topical kinship — two documents about the same thing with no link between them; similarity surfaces the relationship the author missed
   - classification kinship — documents sharing a tag relate by kind even when their topics diverge
   - arcs — documents created close in time tend to share the intent of whatever was underway; the design arc (genesis → build → refactor) is one shape, every activity traces its own; never declared, it falls out of time
2. From how documents connect — beyond the words, signal read off the links themselves, not the values; the more selective the shared connector, the stronger the tie, and a hub couples weakly.
   - co-citation — two documents pointed to by the same third
   - bibliographic coupling — two documents that point to the same third
   - shared citation — two documents that cite the same external source
   - hubs — not a pairwise tie but a node's centrality: a document many point to is central to the corpus; as a shared connector it's the hub that couples weakly above
3. From how documents changed — beyond the corpus itself, git history relates what content can't.
   - change coupling — documents changed in the same commit, often a stronger signal than content
   - co-modification — edited in the same session
   - same author

The tradeoff — latent signal buys recall at the cost of precision: it finds the connection the author missed, and sometimes one that isn't there; the threshold is the knob.

### Read - navigating mapped relationships

<introduce emergent affordances>
