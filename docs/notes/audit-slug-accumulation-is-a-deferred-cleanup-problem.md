---
title: Audit slug accumulation is a deferred cleanup problem
summary: report-finding.sh auto-suffixes on slug collision (-2, -3, ...) so repeated audits leave duplicate-defect files; cleanup is manual.
tags: [todo, skills, scripts, audit-mode-followup]
created: 2026-05-25
aliases: []
---

## Observation

- Decision #7 from the audit-mode interview (2026-05-16): always-write semantics; `--force` removed; auto-suffix on slug collision.
- Each audit pass that re-finds a persistent defect produces a new file: `recipe-page-in-reference-section.md`, then `-2.md`, then `-3.md`, and so on.
- reviewing-wiki/SKILL.md Dedup section: "Manual cleanup (delete the older files) is the user's responsibility — the script does not auto-prune."
- No script currently helps with cleanup. `summarize.sh`, `query.sh`, and `list-findings.sh` do not surface slug clusters.

## Interpretation

- Accumulation is small at first (one defect found twice = one extra file). It grows linearly with audit cadence multiplied by persistent-defect count.
- Hypothesis: weekly audits on a stable wiki with 10 known nit findings produce 50+ files after a quarter. The directory becomes unscannable.
- "Manual" cleanup is the lightest possible story — the next layer is undesigned. Options when it bites: `query.sh --duplicates` mode that lists same-slug clusters; a triage workflow that moves dispositioned findings out of `.findings/`; or `clear-findings.sh` invoked before each audit.

## Next

- Wait for the first real audit to produce a `-N` suffix before designing the cleanup layer. Don't over-design before the problem is concrete.
- Lightest probable fix when it bites: `query.sh --duplicates` (group same-slug findings, show one block per cluster).
