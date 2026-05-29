---
title: Double "draft new skills" commits at 01:42
summary: Two commits 9 seconds apart with the same message — first the doc-skills draft, then a fast amend with small frontmatter fixes the first pass missed. Same author, same session, no agent context switch.
document:
  tags: [journal, skills, git, observation]
  created: 2026-05-13
---

# Double "draft new skills" commits at 01:42

Two commits 9 seconds apart with the same message — first the doc-skills draft, then a fast amend with small frontmatter fixes the first pass missed. Same author, same session, no agent context switch.

## What happened

The reviewer-family session ([[docs/journal/2026-05-13-0346-reviewer-family-doc-skills-multi-pass-discipline.md]]) had a peculiar shape in its commit log: two commits at the same minute with the same message.

- `17332a3 2026-05-13 01:42:08 -0400 draft new skills`
- `e9cda8c 2026-05-13 01:42:17 -0400 draft new skills`

Nine seconds apart. Same commit message. Both touched the doc-skills draft files.

## What the gap was

The first commit landed the draft. Within seconds the author noticed two small frontmatter defects — a missing `aliases: []` line on one SKILL.md, an awkward phrasing in another. Rather than amending the first commit (which would have replaced it in the log), the author committed the fixes as a separate commit with the same message. Two commits told the truth of the work: a draft landed, a fast fix-up followed.

This shape recurred over the project — small fix commits stacked onto initial-drop commits when the next pass surfaced something obvious enough to fix without writing a new commit message. The cost is a slightly noisier log; the benefit is a more honest record of how the work actually happened.

## Decisions captured

- Amend versus follow-up commit is a per-cycle choice. Amending is cleaner for typo-shape fixes; following up is more honest when the fix-up reflects a real second pass on the work. Both shapes show up in the log; neither is consistently correct.
- Same-minute, same-message commits are a signal pattern. They mean a draft landed and a small fix-up followed within the natural editing rhythm. Reading the log, they cluster as one event.
- Cheap moves stay cheap. The cost of the second commit was zero; the benefit was preserving the original commit's hash for the original work. Other commits or notes that referenced 17332a3 by hash kept their reference; an amend would have invalidated it.

## Observation

The pattern itself is small. Worth recording because it shows up enough times in the log to be a habit, and because a future reader scrolling through commit timestamps will see clusters like this and wonder what they mean. The answer is: not much, except that the work flowed and a small fix landed alongside.

## Cross-references

- `[[journal/2026-05-13-0346-reviewer-family-doc-skills-multi-pass-discipline]]` — the broader session this pair lived inside.
