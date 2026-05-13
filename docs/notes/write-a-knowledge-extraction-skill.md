# Write a knowledge-extraction skill

Tags: todo,skills,documentation
Pulls notes and journals into a human-targeted wiki — the Karpathy-inspired knowledge-mining counterpart to taking-notes.


## Observation

`docs/notes/` (atomic wiki pages, current state of each idea) and `docs/journal/` (dated narrative, how-we-got-here) are both LLM-targeted reference material that accumulate as the repo learns about itself. No skill today pulls those into a human-targeted wiki — a curated, polished synthesis of what the repo has discovered.

The Karpathy reference: a wiki that teaches rather than catalogs. Less "here is every note we have on caching" and more "here is what we have learned about caching, with the dead ends pruned and the threads woven."

## Interpretation

A `knowledge-extraction` skill (working name) reads the note set and journal, identifies threads, prunes the dead ends, and produces a human-targeted wiki under (probably) `docs/wiki/`. The wiki's audience is humans first; the agent uses it as it would any reference source.

Likely shape:

- Loads `writing-documentation` for the editorial spine — the wiki output is durable prose for humans.
- Adds Guidance specific to extraction-and-synthesis: which threads warrant a wiki page, how to collapse multiple notes into one canonical page, when to retire a note that the wiki now supersedes.
- May load a future `writing-skills` / `writing-adrs` for structural conventions if the wiki ends up with multiple page types.

Open questions:

- Bursty (run periodically) or incremental (after each batch of notes)?
- Does extraction *retire* the source notes when they fold into a wiki page, or leave them as the raw material? Probably the latter — git keeps the history, and the notes remain the working layer.
- Does the wiki link back to its source notes, or stand independent?

## Next

Deferred until the `writing-skills` / `reviewing-skills` pair lands. Extraction-into-wiki implies a writing-skill genre that is itself mature; without it, the knowledge skill is just writing-documentation invoked with a curation prompt — not yet skill-worthy.
