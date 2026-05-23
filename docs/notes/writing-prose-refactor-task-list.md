# writing-prose refactor task list

Tags: todo,project,task-list,writing-prose,refactor
Canonical task list driving the writing-prose foundation/downstream restructure; both completed and pending tasks captured; maintained as work proceeds.

## Context

writing-prose is being restructured from a single skill (Philosophy/Guidance/Validation with bullet pairs) into a foundation for prose-artifact skills. The new shape is Rhetorical context / Composition / Grammar-structure-referential-integrity / Validation. Downstream skills (taking-notes, journaling, writing-wiki, reviewing-wiki, and a future reviewing-prose) compose on top of the foundation. The work spans the SKILL.md itself, the `positive-transforms.md` sidecar, the per-principle `reference/` expansion directory, the reviewer scripts under `plugins/skills/scripts/`, and the paired reviewing-* skills.

This note is the canonical task list. The conversation task system is transient; this note is durable and updated as work proceeds.

## Milestones

- **SKILL.draft.md → SKILL.md swap completed.** The new SKILL.md is live.
- **Broken-references sweep landed via Opus sub-agent.** `summarize.sh` now parses the new structure; reviewer rubric language uses "principle name" instead of "Philosophy anchor". All 212 tests pass.
- **Wiki path:line citation antipattern removed.** writing-wiki citation guidance switched to symbol-based form; reviewing-wiki Accuracy lens redesigned with drift detection.
- **Rhetorical-context contract landed.** Downstream skills declare a `## Rhetorical context` section with bulleted `Slot: value` lines; Register is bundled shorthand; defaults inline in writing-prose/SKILL.md.
- **reviewing-documentation renamed to reviewing-prose.** Full sweep across all references (skill directory, frontmatter, sibling SKILL.mds, README, notes). 212 tests pass.
- **taking-notes refactor complete.** Cutover landed (`SKILL.draft.md` → `SKILL.md`; previous live skill preserved as `SKILL.old.md`). Migration pattern captured in `docs/notes/migration-pattern-for-refactoring-writing-skills.md` as a reusable transformation reference for journaling and other downstream refactors.
- **journaling refactor — complete.** Cutover landed (`SKILL.draft.md` → `SKILL.md`; previous live skill preserved as `SKILL.old.md`). Applied the migration pattern with journaling-specific adjustments: 4-step OODA (Observe → Search-last-24h → Compose → Record); `--append` mode added to `record-entry.sh` (no `--overwrite` — entries are historically immutable); cross-agent guardrail (other agents must never modify entries); first-person acceptable per Journal register. Tests green after script update.

## Completed

- **#1 Rewrite writing-prose frontmatter description** — landed the foundation/downstream contract in the description.
- **#2 Draft Philosophy section summary** — H2 summary fused into the heading.
- **#3 Draft Guidance section summary** — H2 summary fused into the heading.
- **#4 Draft Validation section summary** — H2 summary fused into the heading.
- **#5 Restructure writing-prose into Rhetorical context / Composition / Validation** — full restructure with merged Philosophy+Guidance into Composition; new Grammar/structure/referential-integrity section between Composition and Validation; principle mapping applied; bullets-with-blurbs format. Swap to live SKILL.md completed.
- **#8 Update summarize.sh for the new writing-prose section structure** — `read_canonical_prose()` parses principle bullets from Composition, Grammar/structure/referential integrity, and Validation's judgement subsection. Original `read_canonical()` retained for writing-csharp and writing-wiki. Three new tests added; all 212 pass.
- **#9 Update reviewing-prose rubric citations** — four references in `reviewing-prose/SKILL.md` and five in `reviewing-wiki/SKILL.md` updated from "Philosophy anchor / heading / section" to "principle name." Reviewer skills' own `## Philosophy` H2 sections left intact (their internal structure has not been ported to the new spine; revisit when #6 lands).
- **#12 Extract named registers to sidecar reference doc** — was completed; subsequently the `registers.md` sidecar was *removed* and the named-registers catalog was re-inlined in the SKILL.md (the catalog is needed every load, so on-demand was the wrong call). `positive-transforms.md` remains as the sole sidecar.
- **#14 Establish writing-prose reference/ expansion convention** — convention statement added to Composition intro; `reference/` directory (originally `deep/`, since renamed) created with 48 placeholder files; shared `bash plugins/skills/scripts/slugify.sh` utility written with 21 passing tests; convention round-trip verified against every principle bullet.
- **#10 Decide writing-csharp structural alignment** — decided: writing-csharp is a special case, structural divergence between prose and code families is accepted, reviewer scripts already handle both shapes. No further work unless friction emerges.
- **#11 Design the rhetorical-context memo contract** — landed. (1) Each downstream skill declares a `## Rhetorical context` section in its own SKILL.md, bulleted list, one `Slot: value` line per slot. No YAML frontmatter, no per-directory override. (2) Foundation defaults live inline in writing-prose/SKILL.md under the Rhetorical context section (was a sidecar; inlined because needed every load). Subject and intent are too artifact-specific to default; every downstream must declare them. (3) Register is bundled shorthand atop the defaults: declaring a named register overrides only the few slots that distinguish it from defaults; the rest stay at default. Inheritance precedence: explicit slot declaration > register bundle > defaults.
- **#6 Rename reviewing-documentation to reviewing-prose** — full sweep landed in one commit. Directory git-mv'd; frontmatter, H1, internal self-references updated; sweep across writing-prose, reviewing-wiki, writing-wiki, README, seven docs/notes/ files. Incidental cross-reference from reviewing-csharp removed. Finding type stays as `documentation` (names the artifact reviewed, not the rubric).
- **#13 Sweep path:line citation guidance** — landed. writing-prose family clean. writing-wiki citation guidance now symbol-based (file plus class/type/method/exported-function name). reviewing-wiki Accuracy lens redesigned around symbol citations with explicit drift-detection workflow and a dedicated symbol-drift signal. Finding location-field convention preserved.

## Partially completed

- **#15 Seed reference/ expansions** — 30 of 48 reference files have content extracted from the original SKILL.md. The remaining 18 are new principles with no original to extract (active voice, present tense, second person, systems behave, verbs over nominalizations, strong verbs, concrete over abstract, substance over superlatives, assertions over commentary, English over Latin, Global English, one idea per sentence, parallel construction, cohesion across documents, action-oriented headings, plus a few Validation checks). Fill lazily as patterns and examples emerge.

## Pending

- **#7 Refactor downstream skills as foundation consumers** — taking-notes, journaling, writing-wiki, reviewing-wiki, **and reviewing-prose** declare their rhetorical-context slots per the contract: a `## Rhetorical context` section in each downstream's SKILL.md, bulleted `Slot: value` lines, slot overrides on top of the foundation defaults. Reviewing-prose is itself a downstream of writing-prose (it produces findings, which are prose artifacts, and judges against the writing-prose rubric). reviewing-csharp is out of scope per #10. Largest remaining task. **In flight:** starting with the markdown-artifact generators — taking-notes first, then journaling, then writing-wiki; corresponding reviewer skills follow.
  - **#7a taking-notes refactor — complete.** Register declared inline (durable note semantics; "Note" catalog entry didn't fit). Rhetorical context section landed with all ten slots. Composition duplication cut; loads `writing-prose` per contract. Frontmatter description retains trigger phrases. Self-review greps run; tests green. Scripts consolidated: `list-notes.sh`/`query.sh` merged into `scan.sh`; `take-note.sh` renamed to `record-note.sh` with `--overwrite` / `--append` modes. Restructured into procedural-OODA shape (Spot → Search → Compose → Record) plus reference sections (`scan.sh`, `record-note.sh`, Notes form a graph, Note format) plus Rhetorical context at end. Migration pattern captured in `docs/notes/migration-pattern-for-refactoring-writing-skills.md`.
  - **#7b journaling refactor — complete.** Cutover landed. Applied the migration pattern with journaling-specific adjustments: 4-step OODA includes Search-last-24h (different from taking-notes' all-time dedup; bounded to the 24-hour same-topic continuation window); `--append` mode added to `record-entry.sh`, no `--overwrite` (immutability principle reinforced); cross-agent guardrail stated; Journal register declared by catalog name; first-person acceptable; CAODN template as one shape among many. SKILL.old.md preserved as the before-half of the worked record.
  - **#7c writing-wiki refactor — pending.** Already declares "Loads alongside writing-prose" in frontmatter; needs the `## Rhetorical context` section added per the #11 contract.
  - **#7d reviewer skills — deferred.** reviewing-wiki and reviewing-prose follow once the generator skills land.
- **#15 (remainder)** — lazy seed of the 18 empty `reference/` files for new principles with no original source. Fill as patterns and examples emerge in practice. Never blocking.
- **Wiki backfill follow-up** — existing project wikis that cite source by `path:line` will be flagged by the redesigned Accuracy lens on next review. Worth a single sweep across active wikis once #13's lens redesign is exercised.

A separate note captures features for a future writing-prose mechanical self-review script: `add-a-negation-grep-self-review-check-to-writing-prose-validation.md` lists em-dash discipline, hedge/filler grep, tense drift grep, marketing-language grep, Latin-abbreviation grep, bold-and-table grep, plus the negation grep itself.

## Ordering and dependencies

- All decisions resolved. #6, #7, #15 remainder, and the wiki-backfill follow-up are unblocked.
- #7 (downstream refactor) is the largest remaining task. It applies the #11 contract: each downstream gets a `## Rhetorical context` section declaring its slot values (overrides from `default-rhetorical-context.md`).
- #6 (full rename) is mechanical sweep work; can land any time.
- #15 remainder fills lazily.

## Starter prompt for next session

Paste this at the top of a fresh session to pick up:

```
Resume the writing-prose foundation/downstream refactor. Canonical state is in
docs/notes/writing-prose-refactor-task-list.md — read that first.

Quick orientation:
- writing-prose/SKILL.md is live with the new structure (Rhetorical context /
  Composition / Grammar / Validation). 48 reference/ expansion files exist; 30 have
  content, 18 are placeholders for new principles. positive-transforms.md now
  lives at reference/positive-transforms.md.
- Rhetorical-context contract: each downstream declares a `## Rhetorical
  context` section in its SKILL.md (bulleted Slot: value lines). Unmentioned
  slots fall back to writing-prose/default-rhetorical-context.md. Subject
  and intent have no default; every downstream must declare them.
- summarize.sh parses the new section structure. reviewing-prose
  and reviewing-wiki rubric language updated. Wiki Accuracy lens now uses
  symbol-based citations with explicit drift detection. 212 tests pass.
- positive-transforms.md and default-rhetorical-context.md are the sidecars
  (positive-transforms.md sits under reference/ alongside the principle expansions).
- bash plugins/skills/scripts/slugify.sh derives reference-file slugs deterministically.

Remaining work (no decisions needed; pick by leverage):
- #7 downstream refactor — taking-notes, journaling, writing-wiki, reviewing-wiki
  load writing-prose and declare their rhetorical-context slots per the contract.
  Largest scope; biggest leverage.
- #6 full reviewing-prose → reviewing-prose rename — mechanical sweep
  across the codebase. Includes filename rename, frontmatter name: field,
  references in other SKILL.md files, notes, scripts.
- #15 lazy seed of remaining 18 reference/ expansions — fill as patterns and
  examples emerge.
- Wiki backfill — existing project wikis citing path:line will be flagged
  by the redesigned Accuracy lens; sweep when next reviewed.

The conversation task system is transient — this note is the canonical record.
Update the note as work proceeds.
```
