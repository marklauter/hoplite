---
title: Proofreading takes an --action option
summary: proofreading always fixes what it finds; add --action:report so a caller can get findings without edits, defaulting to --action:fix.
tags: [todo, skills, proofreading, claude-code]
created: 2026-07-24
priority: low
effort: low
status: open
---

# Proofreading takes an --action option

`plugins/hoplite-skills/skills/proofreading/SKILL.md` always edits: the description says "fix what the sweep finds", and the closing line says "Fix what the sweep finds, then sweep the fix." Add an `--action` option taking `report` or `fix`, defaulting to `fix`.

## Why

A caller who wants to see the tells before anything changes has no way to ask for that today. A cold subagent sweeping someone else's draft would land its edits unreviewed. Keeping `fix` as the default leaves every existing caller unchanged, since the five authoring skills that call it pass no arguments.

## Shape of done

- The `Skill` tool passes `args` through as a string, so the skill body branches on it.
- `--action:fix` and the no-argument case sweep and fix, as now.
- `--action:report` sweeps and reports the tells with file and line, and edits nothing.
- `glossary`, `spec`, `decision`, `taking-notes`, and `journaling` keep their current `Proofread` sections and continue to get `fix`.
