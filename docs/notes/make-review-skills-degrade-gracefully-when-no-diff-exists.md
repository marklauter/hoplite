---
title: Make review skills degrade gracefully when no diff exists
summary: Closed 2026-05-16. Reviewer scripts now support explicit-scope audit modes; the three reviewer SKILL.md files declare per-skill defaults.
tags: [note, closed, skills, reviewing]
created: 2026-05-25
aliases: []
---

## Resolution

`changes.sh` now supports three modes:

- Diff mode (no args, or `<ref>`, or `<ref1> <ref2>`) — unchanged behavior for the pre-commit gate.
- `--all [<dir>]` — filesystem walk of the directory (default `.`), respects `.gitignore`, skips hidden and symlinked entries. No git repo required.
- `--paths <p>...` — explicit files and directories; directories expand recursively. No git repo required.

When invoked with no args against a clean tree or outside a git repo, `changes.sh` emits a structured hint and exits non-zero. The calling skill picks a default from there:

- `reviewing-wiki` defaults to `changes.sh --all .` — audit is the routine mode for wikis.
- `reviewing-prose` and `reviewing-csharp` surface the hint to the user and wait — diff is the routine mode; audit is opt-in.

Severity vocabulary: `pre-existing` collapses in audit mode (no diff to be "outside of"). Audit findings are `important` or `nit` only. The gate-policies sections of all three reviewer skills flag a `pre-existing` produced in audit mode as malformed.

`summarize.sh`'s verdict is mode-agnostic: `review passes` / `review passes; nits optional` / `review blocked on important findings`, with `; pre-existing triage pending` appended when applicable.

`report-finding.sh` auto-suffixes on slug collision (`-2`, `-3`, ...) so audit reruns accumulate findings rather than silently dropping them. `--force` is gone.

## Path resolution under audit for sibling-cloned wikis

The standard wiki layout is sibling clones: source at `D:\{project}\{project}\` and wiki at `D:\{project}\{project}.wiki\`. When `changes.sh --all .` runs with CWD in the wiki clone, source paths for the Accuracy lens resolve to `../{project}/` (strip `.wiki` from CWD's name, look in the sibling). No config file required; the convention is the resolver. When the wiki lives inside the source repo (a `docs/` subdirectory or self-hosted markdown), source paths resolve normally within the same repo.

## Where the design lives

- `plugins/armory/scripts/changes.sh`
- `plugins/armory/scripts/report-finding.sh`
- `plugins/armory/scripts/summarize.sh`
- `plugins/armory/skills/reviewing-wiki/SKILL.md`
- `plugins/armory/skills/reviewing-prose/SKILL.md`
- `plugins/armory/skills/reviewing-csharp/SKILL.md`
