---
name: triaging-findings
description: Use after a review pass to decide the disposition of each .findings/<slug>.md — fix in the diff, file as a tracker issue, drop, or defer. Walks the queue in severity order via the scan scripts that act as a runtime index over the directory.
---

# Triaging findings

The `.findings/` directory is the queue. The head fields in each `.findings/<slug>.md` are name-indexed, and the scan scripts (`list-findings.sh`, `query.sh`, `summarize.sh`) read them and emit the head as the working surface — a runtime index that never drifts because it regenerates on every call. Triage walks the index in severity order, surfaces each finding to the steward, and applies the chosen disposition: Fix, File, Drop, or Defer.

## Philosophy

These principles describe how triage operates. They apply on every triage pass without exception.

### The agent surfaces, the steward decides

The agent walks the queue and presents each finding; the steward decides the disposition. Mutation scripts run once per approved entry, so the confirmation pause sits between findings. The agent never decides Drop or File on its own.

### Disposition is exhaustive

Every finding leaves triage with one of four dispositions: Fix, File, Drop, Defer. Nothing lingers undecided. Chronic Defer is a smell — a queue that grows is a queue that rots.

### Triage operates on findings as artifacts

The reviewer's Observation, Principle, and Location are the contract. Triage decides disposition, not whether the finding is real. When triage disagrees with the principle, the right move is Drop with a rationale, not editing the finding's body.

### The scan scripts are the index

The head-field shape exists so the readers can index it. Triage queries the readers; it does not enumerate `.findings/` files directly or re-implement what the readers already do. The index regenerates on every call, so it cannot drift from the directory it describes. ([[runtime-index-pattern]].)

### Dedup against the tracker before filing

File is a new-issue intent. Run `managing-github-issues/query.sh` against the finding's title and key terms first — a prior issue carries the history of why the problem persisted, and that history is more valuable than a new entry. ([[managing-github-issues]] Philosophy: Search before file.)

## Guidance

Concrete patterns for the scan-prioritize-feed loop and the disposition scripts.

### Scan

The scan scripts (`list-findings.sh`, `query.sh`, `summarize.sh`) ship under `${CLAUDE_PLUGIN_ROOT}/scripts/` — one level above the per-skill `scripts/` directory — because they are shared with the reviewer skills. The triage-owned mutations (`drop.sh`, `file.sh`) live under this skill's own `scripts/` directory.

`summarize.sh` first — counts per severity per type, so the agent knows the queue shape before walking it. `query.sh` then slices by predicate: `--severity important`, `--severity nit`, `--severity pre-existing`. The readers emit the head fields (title, severity, type, lens, location, principle, summary, slug); the file body is opened only when the head fields aren't enough to propose a disposition.

`--severity` and `--xseverity` are mutually exclusive in intent — pick `--severity LEVEL` to walk one bucket or `--xseverity LEVEL` to exclude one bucket. `--severity important --xseverity pre-existing` is a no-op redundancy.

### Prioritize

Severity is the spine. Walk in this order:

- `query.sh --severity important` — actionable now, blocks shipping.
- `query.sh --severity nit` — actionable, author's choice.
- `query.sh --severity pre-existing` — usually batch-deferred or batch-filed as follow-up; the agent proposes the bulk action and the steward confirms.

Within a severity, the readers' default order (alphabetical by slug) is fine. If a project needs a different priority signal, encode it in another head field rather than asking triage to sort in the agent's head.

### Feed

For each finding in the priority walk, the agent presents the head fields the readers emitted and proposes a disposition with a one-sentence rationale. The steward approves, redirects, or asks to see the body. On approval, the agent runs the mutation script and moves to the next finding.

### Disposition vocabulary

- **Fix** — author addresses the finding in the current diff; the agent or author runs `drop.sh` after the fix lands. Default for `important` findings.
- **File** — hand off to the tracker. The agent composes an issue body that conforms to the chosen template, then pipes it to `file.sh`, which forwards to `managing-github-issues/create.sh` and deletes the finding on success.
- **Drop** — false positive, register mismatch, or won't-fix. `drop.sh` deletes the finding; the rationale lives in the conversation, not in a side log.
- **Defer** — leave the finding in `.findings/` for the next pass.

### Severity recalibration

When the steward downgrades or upgrades a finding's severity, edit the `Severity:` head field in the finding file directly. `report-finding.sh` always writes — it auto-suffixes on slug collision (`<slug>-2.md`, `-3.md`, ...) — so it cannot rewrite an existing finding. In-place edits are the only way to update a finding after it's been written. The next scan picks up the new severity.

### Duplicates from audit re-runs

`report-finding.sh`'s auto-suffix behavior means the same defect can appear multiple times in `.findings/` when a reviewer re-runs an audit pass — `<slug>.md` and `<slug>-2.md` for the same observation. The duplicates show up in the priority walk; Drop is the natural disposition for the redundant ones (the steward picks the one to keep, drops the rest).

### Promotion candidates

`summarize.sh` flags findings citing non-canonical principles — those whose `Principle:` doesn't match a heading from the matching writing-X skill. The steward decides whether to promote the principle into the writing-X rubric. Promotion is orthogonal to disposition.

## Validation

Findings carry the triage outcome — `drop.sh` deletes, `file.sh` deletes after a successful `create.sh`. A non-empty `.findings/` directory after a triage pass means Defer entries the steward chose to keep.

### The script set

Triage uses scripts from two locations. Portable bash 3.2+; runs on Linux, macOS, and Windows (Git Bash, WSL).

Mutations — `${CLAUDE_PLUGIN_ROOT}/skills/triaging-findings/scripts/`:

- `drop.sh <slug>` — deletes `.findings/<slug>.md`. Silent on success; the conversation is the audit trail.
- `file.sh <slug> <template-name>` — reads the issue body from stdin, extracts the H1 title from `.findings/<slug>.md`, invokes `managing-github-issues/create.sh`, and deletes the finding when `create.sh` exits zero. The `LABELS` env var passes through.

Scan readers — `${CLAUDE_PLUGIN_ROOT}/scripts/` (shared with the reviewer skills):

- `list-findings.sh`, `query.sh`, `summarize.sh` — emit head-field views over `.findings/`.

Triage adds the two mutations above and reuses the readers; severity recalibration and other head-field updates are direct file edits, since `report-finding.sh` cannot rewrite an existing finding.

### Output discipline

- `drop.sh`: success is silent — the file is gone. Failure prints the error and exits non-zero.
- `file.sh`: success prints the created issue's URL. Failure prints the underlying error and exits with that command's code; the finding is preserved on failure so the steward can retry.

### Gate policies

- A finding selected for File must have a body composed against a real template — `file.sh` does not transform the body. The agent owns the reshape; `create.sh` rejects malformed templates.
- Tracker dedup runs before File. `managing-github-issues/query.sh` is the gate; a match means comment-on-existing, not file-new.
- The reviewer's contract is settled. Triage edits only the `Severity` head field, and does so in-place on the finding file — `report-finding.sh` always writes a new file (auto-suffixing on slug collision), so it cannot serve as a severity-rewrite tool.
