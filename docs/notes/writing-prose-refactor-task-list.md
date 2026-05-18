# writing-prose refactor task list

Tags: todo,project,task-list,writing-prose,refactor
Canonical task list driving the writing-prose foundation/downstream restructure; both completed and pending tasks captured; maintained as work proceeds.

## Context

writing-prose is being restructured from a single skill (Philosophy/Guidance/Validation with bullet pairs) into a foundation for prose-artifact skills. The new shape is Rhetorical context / Composition / Grammar-structure-referential-integrity / Validation. Downstream skills (taking-notes, journaling, writing-wiki, reviewing-wiki, and a future reviewing-prose) compose on top of the foundation. The work spans the SKILL.md itself, sidecar reference docs (registers.md, positive-transforms.md), the per-principle deep/ expansion directory, the reviewer scripts under plugins/skills/scripts/, and the paired reviewing-* skills.

This note is the canonical task list. The conversation task system is transient; this note is durable and updated as work proceeds.

## Completed

- **#1 Rewrite writing-prose frontmatter description** — landed the foundation/downstream contract in the description.
- **#2 Draft Philosophy section summary** — H2 summary fused into the heading.
- **#3 Draft Guidance section summary** — H2 summary fused into the heading.
- **#4 Draft Validation section summary** — H2 summary fused into the heading.
- **#5 Restructure writing-prose into Rhetorical context / Composition / Validation** — full restructure with merged Philosophy+Guidance into Composition; new Grammar/structure/referential-integrity section between Composition and Validation; principle mapping applied; bullets-with-blurbs format.
- **#12 Extract named registers to sidecar reference doc** — `registers.md` lives at the skill root.
- **#14 Establish writing-prose deep/ expansion convention** — convention statement added to Composition intro; `deep/` directory created; 48 empty placeholder files seeded (29 Composition + 8 Grammar + 11 Validation principles); shared `slugify.sh` script written.

## Pending

- **#6 Rename reviewing-documentation to reviewing-prose** — paired rename of the reviewer skill; full sweep of references across the codebase. Blocks #9.
- **#7 Refactor downstream skills as foundation consumers** — taking-notes, journaling, writing-wiki, reviewing-wiki should explicitly load writing-prose, declare their rhetorical-context slots, and name their overrides. Largest scope task.
- **#8 Update summarize.sh for the new writing-prose section structure** — script currently reads ### under ## Philosophy; new structure has Composition + Grammar. Script needs to union both sections' H3 anchors. Tests likely need updating.
- **#9 Update reviewing-documentation rubric citations** — rubric language references "writing-prose Philosophy anchors"; new section names. Bundle with #6.
- **#10 Decide writing-csharp structural alignment** — does code skill follow the prose family's structure (Rhetorical context doesn't port; merging Philosophy+Guidance does)? Independent decision.
- **#11 Design the rhetorical-context memo contract** — where per-directory or per-artifact rhetorical context lives (frontmatter? sidecar file? CLAUDE.md section?). Currently a hand-waving gap in the foundation.
- **#13 Sweep path:line citation guidance from the codebase** — drift-prone antipattern carried over from original; replace with symbol/heading citation discipline.
- **#15 Seed deep/ expansions for the highest-leverage principles** — empty placeholder files exist; content to be written for the 3-5 principles needing depth most.

A separate note captures features for the future writing-prose self-review script: `add-a-negation-grep-self-review-check-to-writing-prose-validation.md` lists em-dash discipline, hedge/filler grep, tense drift grep, marketing-language grep, Latin-abbreviation grep, bold-and-table grep, plus the negation grep itself.

## Ordering and dependencies

- **#6 → #9** — rename ripple; #9 references writing-prose anchors that will be in the renamed reviewing-prose.
- **#8 ↔ #9** — both touch reviewer-script and rubric language; do together.
- **#5 prerequisite for swap** — the SKILL.draft.md → SKILL.md swap is gated on #6 landing (the draft references reviewing-prose).
- **#7 depends on writing-prose stability** — that's now achieved.
- **#15 depends on #14** — done.
- **#10, #11, #13** are independent; can land any time.

## Suggested order

1. **#6 + #9 + #8** as a bundle (the reviewing-documentation → reviewing-prose rename and its ripples).
2. **Swap SKILL.draft.md → SKILL.md** (depends on #6).
3. **#15** (seed deep/ expansions) in parallel with later steps.
4. **#7** (downstream refactor) — the largest, do last.
5. **#11** (memo contract), **#10** (csharp alignment), **#13** (path:line sweep) as standalone work whenever convenient.
