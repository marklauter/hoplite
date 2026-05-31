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

The glob-grep-read loop is the wrong tool for the job.

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

## The solution

Mapping content via explicit, semtantic, and emergent relationships and meta descriptions exposes new affordances for the agent that allow progressive disclosure, reduce token burn-rate and unwanted bias, maximize the smart-zone, and lead to better agent output. The agent can identify and consume only the content it needs.

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

## Latent signal

The corpus holds more connections than anyone wrote into it.

Latent signal is the relationship no author declared — kinship that falls out of what was written rather than what was linked. The explicit is what grep, FTS, and a reading agent harvest; the rest is latent, and the graph alone surfaces it. That's why it's often the most valuable signal in the corpus.

- signal no one authored as a relationship, yet real and useful — the connection you never wrote down
- it emerges from what you did write: the dates, the tags, the words — not from links you drew
- graded by rarity — strength is the rarity of the shared feature, not the fact of sharing; two documents sharing a common word carry almost nothing, two sharing a rare term carry a lot; that's why latent signal can be ranked, and why it can be wrong
- arcs — documents created close in time tend to share the intent of whatever was underway; the design arc (genesis → build → refactor) is one shape, every activity traces its own; never declared, it falls out of time
- topical kinship — two documents about the same thing with no link between them; similarity surfaces the relationship the author missed
- classification kinship — documents sharing a tag relate by kind even when their topics diverge
- structural kinship — signal read off the links themselves, not the values
  - co-citation — two documents pointed to by the same third
  - bibliographic coupling — two documents that point to the same third
  - shared citation — two documents that cite the same external source
  - hubs — a document many point to is central to the corpus, not to one peer
- provenance — git history relates what content can't
  - change coupling — documents changed in the same commit, often a stronger signal than content
  - co-modification — edited in the same session
  - same author
- the tradeoff — latent signal buys recall at the cost of precision: it finds the connection the author missed, and sometimes one that isn't there; the threshold is the knob

## Map and discover

## Read

## Write

## The substrate (the graph)

## Use cases
