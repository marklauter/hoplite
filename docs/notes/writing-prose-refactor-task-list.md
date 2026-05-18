# writing-prose refactor task list

Tags: todo,project,task-list,writing-prose,refactor
Canonical task list driving the writing-prose foundation/downstream restructure; both completed and pending tasks captured; maintained as work proceeds.

## Context

writing-prose is being restructured from a single skill (Philosophy/Guidance/Validation with bullet pairs) into a foundation for prose-artifact skills. The new shape is Rhetorical context / Composition / Grammar-structure-referential-integrity / Validation. Downstream skills (taking-notes, journaling, writing-wiki, reviewing-wiki, and a future reviewing-prose) compose on top of the foundation. The work spans the SKILL.md itself, the `positive-transforms.md` sidecar, the per-principle `deep/` expansion directory, the reviewer scripts under `plugins/skills/scripts/`, and the paired reviewing-* skills.

This note is the canonical task list. The conversation task system is transient; this note is durable and updated as work proceeds.

## Milestones

- **SKILL.draft.md → SKILL.md swap completed.** The new SKILL.md is live.
- **Broken-references sweep landed via Opus sub-agent.** `summarize.sh` now parses the new structure; `reviewing-documentation` and `reviewing-wiki` rubric language uses "principle name" instead of "Philosophy anchor"; `writing-prose/SKILL.md` line 86 corrected to `reviewing-documentation`. All 212 tests pass.

## Completed

- **#1 Rewrite writing-prose frontmatter description** — landed the foundation/downstream contract in the description.
- **#2 Draft Philosophy section summary** — H2 summary fused into the heading.
- **#3 Draft Guidance section summary** — H2 summary fused into the heading.
- **#4 Draft Validation section summary** — H2 summary fused into the heading.
- **#5 Restructure writing-prose into Rhetorical context / Composition / Validation** — full restructure with merged Philosophy+Guidance into Composition; new Grammar/structure/referential-integrity section between Composition and Validation; principle mapping applied; bullets-with-blurbs format. Swap to live SKILL.md completed.
- **#8 Update summarize.sh for the new writing-prose section structure** — `read_canonical_prose()` parses principle bullets from Composition, Grammar/structure/referential integrity, and Validation's judgement subsection. Original `read_canonical()` retained for writing-csharp and writing-wiki. Three new tests added; all 212 pass.
- **#9 Update reviewing-documentation rubric citations** — four references in `reviewing-documentation/SKILL.md` and five in `reviewing-wiki/SKILL.md` updated from "Philosophy anchor / heading / section" to "principle name." Reviewer skills' own `## Philosophy` H2 sections left intact (their internal structure has not been ported to the new spine; revisit when #6 lands).
- **#12 Extract named registers to sidecar reference doc** — was completed; subsequently the `registers.md` sidecar was *removed* and the named-registers catalog was re-inlined in the SKILL.md (the catalog is needed every load, so on-demand was the wrong call). `positive-transforms.md` remains as the sole sidecar.
- **#14 Establish writing-prose deep/ expansion convention** — convention statement added to Composition intro; `deep/` directory created with 48 placeholder files; shared `bash plugins/skills/scripts/slugify.sh` utility written with 21 passing tests; convention round-trip verified against every principle bullet.

## Partially completed

- **#6 Rename reviewing-documentation to reviewing-prose** — only the one-word `reviewing-prose` → `reviewing-documentation` patch in writing-prose line 86 has landed (a temporary downgrade to match reality). The full rename across the codebase has not started.
- **#13 Sweep path:line citation guidance** — writing-prose family is clean (the `Source is the authority` bullet teaches stable-reference citation; `deep/source-is-the-authority.md` reinforces). `writing-wiki/SKILL.md` lines 76 and 159 still teach `path:line` as the citation form, and the `reviewing-wiki` Accuracy lens is designed around `path:line` citations in wiki prose — those two are structurally coupled. The narrow part of the sweep is done; the wiki couple is deferred pending a decision (see Open questions).
- **#15 Seed deep/ expansions** — 30 of 48 deep files have content extracted from the original SKILL.md. The remaining 18 are new principles with no original to extract (active voice, present tense, second person, systems behave, verbs over nominalizations, strong verbs, concrete over abstract, substance over superlatives, assertions over commentary, English over Latin, Global English, one idea per sentence, parallel construction, cohesion across documents, action-oriented headings, plus a few Validation checks). Fill lazily as patterns and examples emerge.

## Pending

- **#6 (remainder)** — full reviewing-documentation → reviewing-prose rename across the codebase. Includes filename rename, frontmatter `name:` field, every reference in other SKILL.md files, notes, scripts. Bundled rename, not piecemeal.
- **#7 Refactor downstream skills as foundation consumers** — taking-notes, journaling, writing-wiki, reviewing-wiki should explicitly load writing-prose, declare their rhetorical-context slots, and name their overrides. Largest scope task. No remaining blockers — agent run finished.
- **#10 Decide writing-csharp structural alignment** — does the code skill follow the prose family's structure (Rhetorical context doesn't port; merging Philosophy+Guidance does)? **Needs user input — see Open questions.**
- **#11 Design the rhetorical-context memo contract** — where per-directory or per-artifact rhetorical context lives. **Design proposal sketched — see Open questions.**
- **#13 (remainder)** — writing-wiki citation guidance and reviewing-wiki Accuracy lens. **Needs user input — see Open questions.**

A separate note captures features for a future writing-prose mechanical self-review script: `add-a-negation-grep-self-review-check-to-writing-prose-validation.md` lists em-dash discipline, hedge/filler grep, tense drift grep, marketing-language grep, Latin-abbreviation grep, bold-and-table grep, plus the negation grep itself.

## Open questions

These are decisions paused at end-of-session, waiting for direction.

### Q1 — #11 memo contract (where does rhetorical context get persisted?)

Proposal: four-layer precedence chain, most-specific wins:

```
artifact frontmatter → directory .rhetorical-context.md → downstream SKILL.md frontmatter → writing-prose default
```

Rationale: most artifacts inherit from their skill (skill-level frontmatter declares slot values for its artifact type). Directory sidecars (`.rhetorical-context.md`) handle special collections — e.g., `docs/wiki/getting-started/` has tutorial register while the rest of the wiki is reference. Per-artifact frontmatter handles outliers — a single how-to inside a tutorial directory. The four-layer chain covers every case.

Same memo shape across all three layers (YAML frontmatter or stand-alone front matter file):

```yaml
rhetorical-context:
  writer: <e.g., contributor>
  voice: <e.g., declarative-terse>
  ethos: <e.g., expert>
  stance: <e.g., neutral>
  audience: <e.g., next-engineer-onboarding>
  subject: <e.g., the auth flow>
  genre: <e.g., reference>
  tone: <e.g., professional>
  register: <one of the named registers from writing-prose>
  intent: <e.g., teach the reader how the auth flow works>
```

Empty slots inherit from the next layer up. Writing-prose's Rhetorical context section needs one new sentence pointing at the contract (probably as a clause in the existing Register subsection).

**Decisions needed:**

- Confirm or revise the four-layer precedence design.
- Pick a name for the sidecar file: `.rhetorical-context.md`, `RHETORICAL-CONTEXT.md`, `rhetorical-context.md`, or something else.
- Decide whether to write a `deep/rhetorical-context.md` companion that expands the contract for downstream skill authors.

### Q2 — #10 writing-csharp alignment

Option 1: Port the new structure to writing-csharp. Drop the Rhetorical context section (code doesn't have audience-and-register the same way prose does). Merge Philosophy + Guidance into Composition. Pros: consistent across the writing-* family; same principle-bullet convention; same reviewer scripts work; same `deep/` pattern available. Cons: requires restructure work on writing-csharp.

Option 2: Keep writing-csharp on the Philosophy/Guidance/Validation shape. Pros: zero work. Cons: structural inconsistency between prose and code families; reviewer scripts handle two shapes (the recent agent run kept `read_canonical()` for writing-csharp specifically); future writing-* skills have to pick.

Recommendation: Option 1, but it's your call.

### Q3 — #13 wiki path:line citation (remainder)

`writing-wiki/SKILL.md` lines 76 and 159 teach `path:line` as the citation form for source-code claims in wiki prose. The `reviewing-wiki` Accuracy lens is designed around those citations existing. Three paths:

- A. **Narrow**: leave writing-wiki and reviewing-wiki as-is. The path:line antipattern lives on for wiki ↔ source citation specifically, justified by the Accuracy lens's verification discipline.
- B. **Medium**: update writing-wiki citation guidance to prefer symbol/identifier citation, with path:line as the narrow accuracy-anchor form the Accuracy lens checks. The lens stays as-is; authors are nudged toward stable references where possible.
- C. **Full**: redesign the reviewing-wiki Accuracy lens to check symbol-based citations. Bigger work; couples to wiki authors' habits and existing wiki pages.

Recommendation: B.

## Ordering and dependencies

- All immediate blockers are resolved. #6, #7, #13-remainder, #15 are all unblocked.
- #11 and #10 need user decisions before execution.
- #7 (downstream refactor) is the largest remaining task; tackle once #11 lands (downstream skills need to know how to declare their rhetorical context).

## Starter prompt for next session

Paste this at the top of a fresh session to pick up:

```
Resume the writing-prose foundation/downstream refactor. Canonical state is in
docs/notes/writing-prose-refactor-task-list.md — read that first.

Quick orientation:
- writing-prose/SKILL.md is live with the new structure (Rhetorical context /
  Composition / Grammar / Validation). 48 deep/ expansion files exist; 30 have
  content, 18 are placeholders for new principles.
- summarize.sh, reviewing-documentation, and reviewing-wiki have been updated
  to reference the new structure. 212 tests pass.
- positive-transforms.md and registers (inline in SKILL.md) are the sidecars.
- bash plugins/skills/scripts/slugify.sh derives deep-file slugs deterministically.

Three decisions are paused waiting for input (see the Open questions section
of the task-list note). Read those and decide direction before proceeding.

Pending work after decisions:
- #11 memo contract (waiting on Q1)
- #10 writing-csharp alignment (waiting on Q2)
- #13 wiki path:line remainder (waiting on Q3)
- #7 downstream refactor (largest; do after #11)
- #6 full reviewing-documentation → reviewing-prose rename (do once everything
  else stabilizes)
- #15 lazy seed of remaining 18 deep/ expansions (no rush; fill as needed)

The conversation task system is transient — the note is the canonical record.
Update the note as work proceeds.
```
