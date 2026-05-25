---
title: Apply mechanical-vs-judgment split to reviewing-prose Line and Copy lenses
summary: Once a prose linter (Vale, alex, write-good) is wired in, much of the Line and Copy per-lens signal lists belongs in the linter config, not the reviewer's eye.
tags: [note, todo, skills, documentation, linting]
created: 2026-05-25
aliases: []
---

## Observation

Reviewing-documentation has six lenses; two of them — Line and Copy — contain many signals that are mechanical and could be encoded in a prose linter:

**Line lens (mechanical candidates):**
- Hedges: *might*, *perhaps*, *could be*, *it's worth noting*, *might want to*.
- Filler: *basically*, *simply*, *just*, *actually*, *really*, *quite*, *very*, *in order to*.
- Wordy stock phrases: *at this point in time*, *due to the fact that*, *in the event that*.
- Tense drift: *will*, *would* where present applies.

**Line lens (judgment, stays in reviewer):**
- Voice violations in context (passive vs active depends on subject).
- A sentence that restates the previous sentence in different words.
- Paragraph density / "this paragraph carries multiple ideas that should split".

**Copy lens (mechanical candidates):**
- Em dash typed as `--` instead of `—`.
- Oxford comma missing in a list of three or more.
- Bold (`**...**`) in prose where headings/lists would carry structure.
- Tables (`|---|`) where headings and bullets would serve.
- Sentence-case headings broken (Title-Case where the page uses sentence case).
- Code fence missing its language tag.
- Link text "click here" / "this page".

**Copy lens (judgment, stays):**
- Code, paths, identifiers not in backticks — context-dependent (is `foo` a CLI flag or a variable?).
- Inconsistent capitalization of defined role names — judgment about whether the term is a role.

**Structure / Accuracy / Coherence / References lenses** are mostly judgment-heavy already and don't have the same mechanical opportunity.

## Interpretation

Today the reviewer catches all of these manually. That's appropriate while no prose linter is wired in. Once a linter exists, the mechanical signals belong in its config, not in this SKILL.md.

Candidate tools:
- **Vale** — most mature; rule syntax matches what's here closely; widely used in technical docs.
- **alex** — narrower focus (inclusive language); could supplement Vale.
- **write-good** — simpler but less configurable.

When the linter lands, the parallel work is:
1. Add a `build-gate.sh`-equivalent for prose (run the linter, fail on configured rules).
2. Add a "Mechanical before judgment" Philosophy bullet to reviewing-prose mirroring the reviewing-csharp one.
3. Compress the Line and Copy lens signal lists to only the judgment-heavy entries.
4. The reviewer assumes mechanical signals are caught by the linter.

## Next

- Skill stays as-is until a prose linter is wired in.
- When the steward decides to add one — likely Vale based on rule-syntax parity — file a note (or this note evolves) capturing the linter choice and the rule mappings.
- Then apply the four-step change above.
