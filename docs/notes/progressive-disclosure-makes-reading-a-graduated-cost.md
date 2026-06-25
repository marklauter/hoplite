---
title: Progressive disclosure makes reading a graduated cost
summary: "hoplite.md prices reading as expensive and earns every read by ranking meaning — but that treats a read as binary, take it or skip it. The read surface is finer: it is a ladder of progressive disclosure, an affordance where each rung reveals a little and costs a little. The agent climbs only as far as the reward pays — survey, filter, projection, body; walk shallow, then deep — so cost is proportional to the depth it needs, not the size of the corpus."
tags: [note, hoplite, affordances]
created: 2026-06-25
status: evolving
---

# Progressive disclosure makes reading a graduated cost

[[docs/hoplite/hoplite.md]] prices reading as expensive against a budget that never refills, and earns every read by ranking meaning so the agent reads only what pays. That treats a read as binary — take it or skip it. The read surface is finer than that: it is **progressive disclosure**, and disclosure is graduated. The agent pays in rungs, reveals a little at each, and stops climbing when the next rung stops paying.

Progressive disclosure is an [[docs/hoplite/glossary/affordance.md]]: the presence of the lede features — `title`, `summary`, the projection — makes possible the action of judging before paying for the body. "Reveal a little, pay a little" is the whole read surface's grammar, not one trick.

## The rungs

The ladder repeats at every scale:

- **Document** — `title` → `summary` → body.
- **Corpus** — survey the vocabulary → filter by predicate → ranked hits → projection (lede + tags) → full read.
- **Graph** — walk depth 1 → walk deeper.

Each rung costs more tokens and reveals more meaning. The agent climbs only as far as the reward justifies, so what it pays is proportional to the depth it needs, not the size of the corpus.

## Why it sharpens the economics

The map of meaning wins by making reads *earned*; progressive disclosure makes them *graduated*. The map is usable precisely because you never load all of it to act — you pay rung by rung. This is the read-side dual of the write side, where the author asserts features one at a time. One rung — a key faulting in its full content — is the mechanism in [[docs/notes/abstraction-is-summary-keyed-random-access-memory.md]]; progressive disclosure generalizes that single fault-in into the full ladder.
