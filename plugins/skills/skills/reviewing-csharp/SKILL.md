---
name: reviewing-csharp
description: Use when reviewing local C# diffs before commit. Produces structured findings classified as important, nit, or pre-existing, written as one file per finding under .findings/.
---

# Reviewing C#

Pre-commit review of C# diffs against the writing-csharp rubric, producing severity-classified findings under `.findings/`. The reviewer judges; the human decides.

## Philosophy

The rubric is the writing-csharp Philosophy. Reviewing-csharp judges; writing-csharp prescribes. The two skills co-evolve.

### Severity calibration (Fagan)

The vocabulary — important, nit, pre-existing — encodes the action the author should take, not how bad the code is. Naming the action keeps attention on what changes shipability. The definitions live in Guidance.

### Findings are observations, not commands

The reviewer reports; the author decides. A finding states what the code does and why a principle is violated; it does not demand the fix.

### The diff is the scope

Review the lines that changed and the context required to understand them. Pre-existing defects adjacent to the diff are surfaced as `pre-existing` findings, not chased upstream.

### Findings discover principles

A finding without a matching writing-csharp principle is a candidate for promotion — either the canonical principle exists under different wording, or the writing skill should grow.

### Mechanical before judgment

Mechanical checks (build, lint, analyzers, ArchUnitNET, EditorConfig) run via the build gate. Assume they are green; the reviewer focuses on what they can't capture — contextual judgment, principle interpretation, design intent. When a violation could plausibly be encoded mechanically, surface it as a candidate for the build gate — write a note, file a finding, or raise it in conversation. The steward decides whether to add the mechanical check.

## Guidance

Concrete patterns for producing findings and running the workflow.

### The workflow

1. `build-gate.sh` runs first. Address every error and warning it surfaces — these are mechanical defects the reviewer should never write findings about. A red build means the diff is not ready for review.
2. `changes.sh` produces the canonical diff plus the changed-file list. Read the diff and the surrounding context of each changed file before composing findings.
3. For each changed line, evaluate against writing-csharp principles for what mechanical checks cannot see. When a principle is violated, compose a finding.
4. `report-finding.sh --type code` writes the finding to `.findings/<slug>.md`. The slug comes from the title; the script validates the type and severity enums and refuses to overwrite without `--force`. C# findings always tag `--type code`.
5. `list-findings.sh` enumerates the current findings by reading each file's head. Scan it before composing a new finding — match on title and summary, since the slug catches reworded duplicates. `query.sh --type code` is the tool for predicate-driven scans (filter by severity, principle, location, etc.) when the finding set has grown.
6. `summarize.sh` collapses the directory to counts plus verdict. Run it when the review pass is complete.

### Severity calibration

- important — correctness defect, security defect, or principle violation with real cost (mutable domain state, throws in domain logic, infrastructure leaking into the model). The diff does not ship without resolution.
- nit — style miss, idiom miss, or judgment call without behavioral consequence (explicit type where `var` works, missing `internal sealed`, naming nit). The author may fix or skip.
- pre-existing — defect on lines the diff did not touch, surfaced because the agent's eye fell on it while reviewing nearby code. Not blocking. Natural input to triage for tech-debt filing.

### The Principle field

- Prefer an existing writing-csharp principle heading verbatim. The match links the finding to the rubric and keeps the vocabulary stable.
- When no existing principle fits, use a free-form descriptor. `summarize.sh` flags the mismatch; these findings are candidates for promotion into writing-csharp.

### Location

- Single location is the default: `` `path/to/file.cs:42` ``. Repo-relative path, the most relevant line.
- Multiple locations for the same defect are comma-separated: `` `src/A.cs:10, src/B.cs:25` ``. Use only when the locations share the exact same defect; distinct defects get distinct findings even when they violate the same principle.

### Dedup before writing

- Same defect on a different line: update the existing finding's Location to a comma-separated list with `report-finding.sh --force`, rather than creating a second file.
- Same principle violation in a different shape: separate findings. The artifact is per-defect, not per-principle.

### Where mechanical can't reach

What writing-csharp's mechanical gates can't encode — the judgment-shaped parts of the review:

- **Context-dependent applicability**: primitive obsession is the principle, but whether a specific `string` should be a `FilePath` value type depends on whether the concept carries invariants. Mechanical rules can't tell which `string`s are domain concepts.
- **Domain vs infrastructure failure**: a method returning `T` that throws is correct in an adapter and wrong in domain logic. The reviewer reads the layer the code lives in.
- **Design coherence**: whether a new shape matches its peers — mutable where peers are immutable, throwing where peers return Results — is judgment about surrounding code, not a syntactic check.
- **Pattern divergence on first instances**: the first slice of any new pattern carries disproportionate weight. The reviewer asks whether the example being set is the example wanted.
- **Severity calibration**: every finding names the action the author should take. Rules don't know what is shipping-blocking vs. skippable for this diff.

## Validation

Findings are the artifact of the review pass. Each finding is one file under `.findings/`.

### The finding artifact

Findings live as one file per finding under `.findings/` at the repo root. The directory survives the session and is the durable record of the review.

File shape:

```markdown
# <one-line title — the H1>

Severity: <important | nit | pre-existing>
Type: code
Location: `path/to/file.cs:42`
Principle: <writing-csharp principle name>
<one-line summary>

## Observation
<observable facts about the code>

## Why it matters
<which principle, concrete cost>

## Suggested fix
<concrete code or prose>
```

The H1 is line 1. Head fields (`Severity:`, `Type:`, `Location:`, `Principle:`) are read by name, not by line offset. The summary is the line immediately after `Principle:`. The body sections follow.

C# findings always carry `Type: code`, distinguishing them from documentation findings in the same `.findings/` directory.

The filename is the slug of the title: lowercase, non-alphanumeric replaced with dashes, leading and trailing dashes trimmed, capped at 80 characters.

### The script set

Five scripts ship under `${CLAUDE_PLUGIN_ROOT}/scripts/`, shared with reviewing-documentation. Portable bash 3.2+; runs on Linux, macOS, and Windows (Git Bash, WSL).

- `changes.sh [<ref> | <ref1> <ref2>]` — produces the diff for the review. No args shows uncommitted changes against `HEAD` and the untracked-file list. One ref shows the diff against that ref. Two refs show the three-dot diff (PR-style: what is on `ref2` since it diverged from `ref1`).
- `report-finding.sh [--force] --type <code|documentation> [--lens <name>] <title> <severity> <location> <principle> <summary>` — body piped on stdin. For C# findings, pass `--type code`; `--lens` is forbidden. Slugifies the title for the filename, validates the type, severity, and lens enums, refuses to overwrite without `--force`, writes `.findings/<slug>.md`.
- `list-findings.sh` — reads the head fields of each `.findings/*.md` and emits one entry per finding: title, severity, type, lens (when present), location, principle, summary, slug filename. Use to dedup before composing a new finding.
- `query.sh [--title PAT] [--severity LEVEL] [--xseverity LEVEL] [--type KIND] [--xtype KIND] [--lens NAME] [--xlens NAME] [--location PAT] [--principle PAT] [--summary PAT]` — multi-predicate scan. Each flag is optional; flags AND together. Severity, type, and lens match exactly against their enums; the `--x*` flags exclude matches on the same enums; title, location, principle, and summary match substring case-insensitive. Output mirrors `list-findings.sh`. Filter by `--type code` when scanning C# findings in a mixed `.findings/` directory; legacy findings without a `Type:` field are treated as code. Use `--xseverity pre-existing` to focus on actionable findings on the current diff.
- `summarize.sh` — counts findings by severity per type, prints a verdict, and flags any finding whose `Principle:` value is not a canonical heading from the matching writing skill (`writing-csharp` for `Type: code`, `writing-documentation` for `Type: documentation`); the mismatch is signal for the writing skill, not a defect. When `CLAUDE_PLUGIN_ROOT` is unset or the writing-X skill file is unreadable, the canonical-principle check for that type is skipped and a warning prints to stderr.

### Output discipline

- Findings persist until the author deletes them; cleanup is manual.
- Filing is handled by `managing-github-issues` after author triage. The finding shape and the triage-proposal shape in that skill are deliberately compatible.
- `changes.sh`: success prints the three sections (files, diff, untracked when applicable). Failure prints git's error and exits with git's code.
- `report-finding.sh`: success is silent — the file is the artifact. Failure prints the validation error and exits non-zero.
- `list-findings.sh`: success prints the formatted finding list, or `no findings` when `.findings/` is empty or missing.
- `query.sh`: success prints the formatted matches in the same block format as `list-findings.sh`, or `no matches` when nothing satisfies the predicates. Exit code is 0 in both cases.
- `summarize.sh`: success prints the counts line, the verdict line, and the non-canonical-principle line when any apply. Stderr carries a warning when the rubric file is unreadable.

### Gate policies

When a finding is malformed, the rule is: fix the finding.

- A finding without a `Principle:` line is a defect. Every finding traces to a principle, canonical or free-form.
- A C# finding without `Type: code` is a defect. The shared infrastructure relies on the type tag to distinguish C# findings from documentation findings.
- An `important` finding without a `## Suggested fix` is a defect. The author needs the path forward.
- A `pre-existing` finding for a line the diff modified is a defect. The scope is mis-classified — the line did change, so the finding is `important` or `nit`.
- A finding citing a non-canonical principle is a candidate for promotion into writing-csharp. `summarize.sh` surfaces it; the author decides during triage.
