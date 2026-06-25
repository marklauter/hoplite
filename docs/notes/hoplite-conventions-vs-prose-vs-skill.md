---
title: Graph-imposed conventions belong to hoplite, not writing-prose or skills
summary: Skip-bold/tables, wikilink syntax, and epistemic badges follow from how the hoplite graph ranks, links, and vouches for content — so they belong in the hoplite authoring spec, not in writing-prose (comprehension regenerates that) or in any single skill.
tags: [note, hoplite, skills, design]
created: 2026-06-19
status: evolving
---

Skip-bold/tables, wikilink syntax, and epistemic badges follow from how the hoplite graph ranks, links, and vouches for content — so they belong in the hoplite authoring spec, not in writing-prose or any single skill.

## The three homes for a rule

- **writing-prose** — if a comprehending writer regenerates it. Active voice, front-loading, one-idea-per-sentence follow from concision-after-comprehension; you needn't state them.
- **a skill** — if it's that skill's task. "Collapse synonyms into `aliases`" is the glossary skill's job, no one else's.
- **a hoplite convention** — if the graph imposes it: true for every artifact in this corpus because of how hoplite ranks, links, or vouches for content. Not derivable from good writing, not owned by one skill.

The test for the third: would it hold for every writer of every artifact here, *because of how hoplite works*? Then it is hoplite's.

## Why these three are hoplite's

- **Skip bold and tables.** A table shreds prose into cells that shingle and embed poorly, so Hoplite's BM25-and-embedding ranking scores it worse; bold adds markdown noise. A fact about the index, not about clear prose.
- **Wikilink / ghost / proxy syntax.** A `[[docs/<path>.md]]` wikilink materialises a `declared` edge; the full repo-relative path is required because query results return that path; `[[ghost/<slug>]]` marks an intentional open loop; a durable external URL earns a proxy note under `docs/proxies/`. Graph-edge mechanics, not style.
- **Epistemic badges.** Marking a claim observation / inference / guess keeps a knowledge base from passing guesses as fact. Comprehension produces the *separation*; the badge is the corpus's honesty standard — held independent of any writer's skill.

## Home

These belong in the hoplite authoring spec (`docs/hoplite/hoplite-authoring.md`), referenced by skills and writing-prose rather than copied into them — one home, linked, not duplicated.
