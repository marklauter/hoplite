---
title: Audit-mode shipped before the existing tests ran
summary: Audit-mode for reviewer scripts landed after a focused smoke test, but six tests in report-finding_test.sh and summarize_test.sh failed against the new --force-removed and verdict-copy behavior; a second agent caught the miss. The writing-loop discipline gained an explicit "run the existing test suite" step.
tags: [journal, skills, testing, audit-mode, dead-end]
created: 2026-05-16
aliases: []
---

# Audit-mode shipped before the existing tests ran

Audit-mode for reviewer scripts landed after a focused smoke test, but six tests in `report-finding_test.sh` and `summarize_test.sh` failed against the new `--force`-removed and verdict-copy behavior; a second agent caught the miss. The writing-loop discipline gained an explicit "run the existing test suite" step.

## Intent

Add audit-mode to the reviewer scripts. The session also stood up `triaging-findings` and a wiki skill pair (`writing-wiki`, `reviewing-wiki`). The audit-mode change touched `report-finding.sh` and `summarize.sh` behavior — removed the `--force` flag and changed how verdicts copy through the pipeline.

The agent declared the work done after a smoke test of the new behavior. The smoke test exercised the audit-mode happy path. It did not run `tests/run-tests.sh`.

## What happened

A second agent ran the existing test suite and surfaced six failures. The tests in `report-finding_test.sh` and `summarize_test.sh` had been written against the old `--force` behavior and the old verdict-copy semantics. The audit-mode work changed both, but the agent didn't grep for `*test*.sh` in the affected scripts' directories, and didn't run the test suite, and didn't notice the tests existed.

The smoke-test-only validation looked complete from the writing agent's vantage. The reviewing agent only had to type `bash tests/run-tests.sh` to see the failure.

## What this changed

The writing-loop discipline as it stood did not require running an existing test suite against script changes. A change that broke six tests still got declared done. Two things came out of this:

- The immediate fix — update the failing tests to match the new behavior, or revert the breaking changes if the new behavior was wrong. (The new behavior was correct; the tests had to update.)
- The systemic fix — a follow-up note proposing two new skills, `writing-skills` and `writing-bash`, both required to include a Validation section that explicitly names running the existing test suite as part of the writing loop. Encoding the discipline into the skill so future sessions inherit it.

The follow-up note: see `[[write-writing-skills-and-writing-bash-skills-with-verification-sections]]`. That note traveled with the repo for a long time as a todo before the broader writing-prose refactor reabsorbed its requirements into the foundation skill's validation contract.

## Decisions captured

- Smoke tests are not enough when an existing test suite exists. The first thing to check after a script change is whether the script has tests. The second thing is to run them. The third thing is to update them only if the new behavior is intentional.
- Skill bodies encode the validation discipline. The miss happened because no skill said "run the test suite." A skill that says it is a defense against the next agent making the same call.
- Second agents are load-bearing. The writing agent missed something the reviewing agent caught in one command. Two-agent flow is part of how this repo stays honest.

## Next

`writing-skills` and `writing-bash` end up superseded by the broader writing-prose foundation refactor a few days later; the Validation-section requirement migrates into the foundation rather than staying split across two specialist skills.
