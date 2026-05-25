---
title: Write writing-skills and writing-bash skills with verification sections
summary: Two new skills to create; each must include a Validation section that names running the existing test suite, so the audit-mode test miss does not repeat.
tags: [todo, skills, writing-skills, writing-bash]
created: 2026-05-25
aliases: []
---

## Observation

- 2026-05-16 audit-mode implementation declared done after a focused smoke test but before running the existing `tests/run-tests.sh` suite. Six tests in `report-finding_test.sh` and `summarize_test.sh` failed against the new `--force`-removed and verdict-copy behavior. A second agent caught the miss.
- The miss: script changes need to grep for `*test*.sh` before declaring done; the existing test suite is the verification baseline.
- Two new skills to create:
  - `writing-skills` — the meta-skill about authoring SKILL.md files (foundation/downstream shape inherited from `writing-prose`, frontmatter contract, intro discipline, downstream declaration of `## Rhetorical context`).
  - `writing-bash` — the skill for the bash scripts that back other skills (bash 3.2+ portability, `--help` convention, output discipline, sourced-vs-executed distinction, the canonical script-set shape).
- Both skills must include a Validation section that explicitly names running the existing test suite as part of the writing loop — encoding the verification step into the skill so future sessions inherit the discipline.

## Interpretation

- The miss happened because the writing-loop discipline does not currently include "run any existing test suite against your change." If the skill encodes that step, future sessions inherit the discipline.
- writing-skills owns the meta-pattern. Its Validation section self-references: when you write a skill, validate it the way the skill says to validate its own outputs — read sibling SKILL.md files, run the test suite for the skill's scripts, verify `--help` on every script.
- writing-bash owns the bash-script pattern used across the reviewer scripts. Validation here is concrete: shellcheck, `tests/run-tests.sh`, the `--help` smoke (every script answers `--help`), and the canonical script-set behavior (silent on success, structured stderr on failure).
- Both skills load `writing-prose` as the universal prose spine and declare their own `## Rhetorical context` per the foundation contract; skill-specific patterns (structural conventions for SKILL.md, bash-portability rules) layer on top.

## Next

- Draft writing-skills as a downstream of `writing-prose`: declare its `## Rhetorical context` section per the contract, then layer skill-authoring conventions (frontmatter shape, intro discipline, downstream contract literacy). Validation section names: read sibling SKILL.md files, run any existing test suite for the skill's scripts, verify `--help` on every script.
- Draft writing-bash with bash-3.2+ portability, `--help` convention, output discipline, sourced-vs-executed distinction, and (load-bearing) "run the existing test suite" as a Validation step.
- Consider whether the existing `taking-notes/scripts/take-note.sh` needs `--help` retrofit too (the earlier "every script should have help" request was scoped to the shared reviewer scripts and `build-gate.sh`, but the principle is universal).
