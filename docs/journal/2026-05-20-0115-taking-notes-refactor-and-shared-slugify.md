---
title: Taking-notes refactor and the shared slugify
summary: Taking-notes refactors as a writing-prose downstream; the script set gets reorganized; slugify gets shared across notes and journal so two skills converge on one canonical kebab-case rule.
tags: [journal, skills, taking-notes, slugify, milestone]
created: 2026-05-20
aliases: []
---

# Taking-notes refactor and the shared slugify

`taking-notes` refactors as a `writing-prose` downstream; the script set gets reorganized; slugify gets shared across notes and journal so two skills converge on one canonical kebab-case rule.

## Intent

`writing-prose` had just landed as the foundation. `taking-notes` was the first downstream that needed real exercise. The refactor had three goals:

1. Make `taking-notes` declare its rhetorical-context override and inherit the rest from `writing-prose`.
2. Reorganize the `taking-notes` script set so the supporting scripts have clean names and clean responsibilities.
3. Pull `slugify` out of `taking-notes` and share it with `journaling`. Two skills that produce filenames with kebab-case slugs should not carry two implementations of the slug rule.

## What landed (chronological)

- 2026-05-19 01:40 — Initial refactor pass on `taking-notes`.
- 2026-05-19 10:10, 11:50 — Two first-draft commits as the new shape settled.
- 2026-05-19 12:24 — Refactored `taking-notes` scripts.
- 2026-05-19 12:50 — Refactor script name; rename.
- 2026-05-19 23:16 — Refactor scripts and tests; share `slugify` across notes and journal.
- 2026-05-20 00:24, 00:40 — Refinement passes; rename.
- 2026-05-20 01:15 — Renamed, refactored, deleted; stubbed.

## Decisions captured

- Shared utilities live above the consumer skills. The slugify rule belongs in a shared script that both `taking-notes` and `journaling` invoke, not in a private utility under one of them. The script's location matters less than the fact that it is referenced from both, with no second implementation lurking.
- One canonical kebab-case rule. Lowercase, whitespace to hyphens, strip non-alphanumeric except hyphens. The rule lives in one place; downstream skills cite it by reference. Drift between two slugify implementations would split the corpus by author tool.
- Tests follow scripts. The refactor's test pass was a peer commit to the script refactor, not a follow-up note. Renaming a script without renaming its test creates the same kind of drift the audit-mode miss surfaced; the same-commit pattern is the defense.
- "Stubbed" is a real state. The 01:15 wrap commit ends with stubs for follow-on work the session ran out of time for. Stubs are honest; they declare "this slot exists, content pending" rather than implying completion.

## What this exposed

The refactor surfaced a problem that the inject-composition pivot resolves the next day. `taking-notes` declared its rhetorical-context override per the foundation contract — but the editorial principles from `writing-prose` still had to be duplicated, restated, or referenced by hand. The foundation/downstream coupling was conceptual; the mechanism was still "read the foundation alongside the downstream." A real injection mechanism was missing.

The discoveries note about skill composition lands the following evening (2026-05-21), and the `!cat` injection adoption follows hours later. See `[[2026-05-21-0403-injection-composition-pivot]]`.

## Next

The pre-injection state of `taking-notes` carries forward briefly. Within 36 hours the prose skills get rebuilt around the `!cat` injection mechanism, and `taking-notes` becomes the canonical exemplar of a consumer that injects rather than restates.
