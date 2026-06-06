---
title: Reviewer family, doc skills, and the multi-pass discipline
summary: Github-issues, reviewing-code, and doc skills land over two days through stacked editorial passes; the multi-pass rhythm — coherence, copy, signal alignment, citation, test coverage — settles in as the way new skills get authored here.
tags: [journal, skills, reviewing, bash, milestone]
created: 2026-05-13
---

# Reviewer family, doc skills, and the multi-pass discipline

Github-issues, reviewing-code, and doc skills land over two days through stacked editorial passes; the multi-pass rhythm — coherence, copy, signal alignment, citation, test coverage — settles in as the way new skills get authored here.

## Intent

Extend the plugin past authoring skills into reviewing skills. The agent should know how to ship code reviews, manage GitHub issues, and write documentation, and each of those is a SKILL.md plus a bash-script set with tests. Use the editorial discipline established in the first plugin entry: draft, then several tightening passes before declaring done.

## What landed

Day one (2026-05-12 night):

- `github-issues` and `reviewing-code` skills draft.
- Polish new skills.

Day two (2026-05-13 morning, 01:42 through 03:46):

- Doc-skills draft. Two consecutive "draft new skills" commits a few seconds apart — first draft followed by a fast amend.
- Pass 1: coherence + line on doc skills.
- Pass 3: document `summarize.sh` stderr-warning behavior. (Pass 2 collapsed into the prior commit without its own marker.)
- Pass 4: copy — Oxford commas and language tags on fenced blocks.
- Final scan: align per-lens signals with register flexibility.
- Fix awkward "tagged Type documentation" phrasing in frontmatter.
- Post testing, code review, editorial review — three-mode wrap pass.
- Content-only SKILL.md intros; drop writing-architecture deferral; queue todo notes. The intro of each SKILL.md gets stripped of meta-commentary; "this skill teaches X" framing dies.
- Distill skills, add inline citations, cover 9 more scripts with tests.
- Add Evidence-based reviewer principle; close test coverage gaps.

Plus a small note-burst: three follow-up ideas captured.

## Patterns that crystallized

- Numbered passes work. Pass 1, pass 3, pass 4 in the commit log — each pass had a specific lens (coherence, copy, signal alignment). The lens gets named in the commit message; the next pass picks a different lens. Stacking lens-named passes is faster than sweeping for "anything wrong" each time.
- Distillation comes late, not early. The "distill skills" commit at 03:30 shows up after testing, after editorial review, after the content-only intro pass. Distillation works on stable text; doing it first wastes the cut because the surrounding prose is still moving.
- Inline citations matter. The reviewer skills landed with explicit citations to the bash patterns and the test files they refer to. Skills that hand-wave at "the canonical script set" never quite feel pinned down.
- Test coverage gaps are skill-shaped. The "9 more scripts with tests" addition closes coverage holes the reviewer skills exposed by their existence — adding a skill surfaces what isn't yet tested.

## Decisions captured

- Reviewing is a first-class skill family, peer to authoring. The plugin's shape becomes: skills that write things + skills that review things. Both load editorial discipline from the same foundation when it gets factored later.
- Evidence-based reviewer is a foundation principle. Reviewers cite the source they're judging against; verdicts without citations carry no weight.
- Editorial polish is part of the work, not a coda. Six passes on a single skill set inside one session is the norm here, not an outlier.

## Next

Build-gate preflight and `.findings/` placement come up; the reviewer scripts need workspace-aware behavior and a stable location for verdicts.
