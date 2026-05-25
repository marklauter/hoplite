---
title: Skill-picks-the-default is a prose contract, not enforced
summary: SKILL.md text declares each reviewer's default invocation (audit for wiki, diff for csharp/documentation), but nothing in the scripts ensures Claude follows it.
tags: [note, todo, skills, scripts, audit-mode-followup]
created: 2026-05-25
aliases: []
---

## Observation

- Decision #2 from the audit-mode interview (2026-05-16): each skill picks its default. reviewing-wiki defaults to `changes.sh --all .`; reviewing-csharp and reviewing-prose print the hint and stop.
- `changes.sh` emits the structured hint on the clean-tree no-args path, but the hint is identical regardless of caller — the script does not know which skill invoked it.
- The "skill picks the default" lives entirely in SKILL.md prose. A future Claude session that runs `changes.sh` by reflex (because that is the muscle memory from reviewing-csharp) gets the hint and then has to remember to run `changes.sh --all .` instead.

## Interpretation

- Runtime contract enforced only by the reviewer agent's reading discipline. No mechanical safety net.
- Hypothesis: Claude will get this right most of the time because reviewing-wiki workflow step 2 explicitly names the default invocation. "Most of the time" is not "always."
- Hardening options when needed: (a) per-skill wrapper script (`audit-wiki.sh` that just calls `changes.sh --all .`); (b) environment variable read by changes.sh to switch defaults; (c) the skill's slash-command implementation explicitly invokes the right mode; (d) leave it as a prose contract and trust the reviewer.
- Option (d) shipped. Lowest-machinery option; highest "Claude forgot" failure mode.

## Next

- Observe whether the prose contract holds across sessions in practice.
- If reviewing-wiki sessions repeatedly default to diff mode by reflex, harden via option (a) — a wrapper script — which is the least intrusive of the mechanical options.
