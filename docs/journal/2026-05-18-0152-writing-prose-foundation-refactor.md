---
title: Writing-prose foundation refactor
summary: writing-prose replaces the old writing-documentation skill as the universal prose spine; the downstream rhetorical-context contract crystallizes; reviewing-documentation renames to reviewing-prose; foundation defaults for the ten rhetorical-context slots inline; Register becomes bundled shorthand atop the defaults.
tags: [journal, skills, writing-prose, foundation, milestone]
created: 2026-05-18
aliases: []
---

# Writing-prose foundation refactor

`writing-prose` replaces the old `writing-documentation` skill as the universal prose spine; the downstream rhetorical-context contract crystallizes; `reviewing-documentation` renames to `reviewing-prose`; foundation defaults for the ten rhetorical-context slots inline; Register becomes bundled shorthand atop the defaults.

## Intent

The skill family had drift. `writing-documentation` was the de facto editorial spine for the prose-producing skills, but it carried a genre commitment (documentation specifically) that didn't fit notes, journal entries, wikis, or reviews. Every downstream skill ended up re-importing or restating the editorial rules. The refactor needed to:

1. Rename the foundation to `writing-prose` so the genre-specific name stops constraining its scope.
2. Declare an explicit foundation/downstream contract — what the foundation commits to, what downstream skills inherit, what downstream skills override.
3. Inline the defaults for the ten rhetorical-context slots (writer, voice, ethos, stance, audience, subject, genre, tone, register, intent) so a downstream skill knows what it gets for free and what it has to override.
4. Make Register a bundled shorthand atop the other slots, not a competing dimension.
5. Carry the rename through every downstream skill including the reviewer side.

## What landed (chronological)

- Draft writing-prose replacement (18:28). First pass at the new shape.
- Tightening the draft (22:11). Editorial pass on the new foundation.
- Backfill deep (00:25 next day). Pull every relevant pattern from the old documentation skills into the new foundation.
- Completed refactor (00:31). Foundation lands.
- Fix references broken by writing-prose swap (01:09). The rename cascaded — sibling skills referenced the old name; grep-and-update closed the gap.
- Declare downstream rhetorical-context contract (01:26). The foundation states what downstream skills inherit and where they declare their own override.
- Foundation defaults for the ten rhetorical-context slots (01:28). Defaults written in; "ask the user" defaults for audience, subject, genre, intent; named defaults for the others.
- Register is bundled shorthand atop defaults (01:39). The relationship between Register and the other nine slots got named explicitly.
- Rename reviewing-documentation to reviewing-prose; inline rhetorical-context defaults (01:48). The reviewer-side rename, plus the reviewer learns its own rhetorical context.

## The contract that crystallized

Foundation/downstream coupling is one-way and explicit:

- The foundation owns universal editorial rules: positive framing, active voice, present tense, second person, em-dashes, Oxford commas, etc. Plus the rhetorical-context machinery (ten slots, named registers, derivation procedure, defaults).
- Downstream skills inherit all the editorial rules without restating them. They override slots when their genre demands it. `taking-notes` overrides Genre to `note`. `journaling` overrides Voice to plainspoken and Audience to "future self." Et cetera.
- The override is declared in a `## Rhetorical context` section in the downstream SKILL.md. The presence of that section signals "this skill is a downstream of writing-prose"; its content names which slots got reshaped.

## Decisions captured

- Foundation names should be genre-agnostic. `writing-documentation` constrained scope by name. `writing-prose` doesn't.
- Defaults beat absence. The foundation declares ten slot defaults rather than leaving them undefined; downstream skills override when needed. Undefined defaults force every consumer to re-derive.
- Register is bundled shorthand, not a tenth orthogonal axis. Two engineers can agree "this is reference register" and converge on the same dozen sub-decisions. The named-register catalog acts as shared vocabulary atop the slots.
- Renames cascade. Every reference to the old skill name had to update in the same change-set; partial renames create dead links and confused consumers. The fix-references commit at 01:09 was load-bearing.

## What this enables

- Skills compose against a stable editorial backbone. Every prose-producing skill in the plugin now has a foundation it can defer to, and an explicit slot for the parts where it diverges.
- The downstream-contract pattern generalizes. Three days later this same shape — foundation declaring a contract, downstream declaring overrides — gets reused for the inject-composition discovery. The architectural pattern wasn't named "foundation + downstream" yet, but it was already the shape the skills were settling into.

## Next

Taking-notes refactors into a writing-prose downstream the following day (2026-05-19); the refactor exposes shared utility like slugify across notes and journal, and the cracks that will demand the inject-composition pivot two days later start to show.
