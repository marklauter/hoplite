---
name: reviewing-csharp
description: Use when reviewing local C# diffs before commit. Produces structured findings classified as important, nit, or pre-existing, written as one file per finding under .findings/.
---

# Reviewing C#

Philosophy, guidance, and validation for reviewing C# diffs before commit.

## Philosophy

These principles draw on a few orienting threads. Fagan on formal inspection — defect detection is the work, and severity calibration is the discipline that keeps it useful. Pólya on observation before interpretation — state what the code does, then name the principle from which it departs. Norman on forcing functions — the finding template shapes the review so the principle reference rides with every finding.

The rubric is the writing-csharp Philosophy. Reviewing-csharp judges; writing-csharp prescribes. The two skills co-evolve.

### Severity calibration

The vocabulary — important, nit, pre-existing — encodes the action the author should take, not how bad the code is. Important means the diff does not commit without this changing. Nit means a fix is welcome but optional. Pre-existing means the defect is not from this diff. Naming the action keeps the human's attention budget on the changes that change shipability.

### Findings are observations, not commands

The reviewer reports; the human decides. A finding states what the code does and why a principle is violated; it does not demand the fix. Judgment lives at the human review of the artifact.

### The diff is the scope

Review the lines that changed and the context required to understand them. Pre-existing defects adjacent to the diff are surfaced as `pre-existing` findings, not chased upstream. Whole-codebase audit is a different activity with different output.

### Findings discover principles

A finding that cannot be tied to an existing writing-csharp principle is a candidate for promotion — either the canonical principle exists and the review surfaced new wording, or the writing skill should grow to cover the case. The human decides during triage. The review loop and the writing skill co-evolve.

## Guidance

Concrete patterns for producing findings and running the workflow.

### The workflow

1. `changes.sh` produces the canonical diff plus the changed-file list. Read the diff and the surrounding context of each changed file before composing findings.
2. For each changed line, evaluate against writing-csharp principles. When a principle is violated, compose a finding.
3. `report-finding.sh` writes the finding to `.findings/<slug>.md`. The slug comes from the title; the script enforces the severity enum and refuses to overwrite without `--force`.
4. `list-findings.sh` enumerates the current findings by reading each file's head. Scan it before composing a new finding — match on title and summary, since the slug catches reworded duplicates.
5. `summarize.sh` collapses the directory to counts plus verdict. Run it when the review pass is complete.

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

- `list-findings.sh` shows the current set. Scan it before composing a new finding.
- Same defect on a different line: update the existing finding's Location to a comma-separated list with `report-finding.sh --force`, rather than creating a second file.
- Same principle violation in a different shape: separate findings. The artifact is per-defect, not per-principle.

### Per-principle signals

Each subsection mirrors a writing-csharp Philosophy heading. The signals listed are what the agent looks for in changed lines; they are not exhaustive.

#### Make invalid states unrepresentable

- A public parameterless constructor on a domain type — smart constructor bypassed.
- A property with `set;` on a domain type — invariants can be mutated post-construction.
- A `Create` factory that returns `T` rather than `Result<T>` (or equivalent) — validation has no failure channel.
- Primitive obsession: `int`, `string`, `DateTime` used directly for concepts that carry invariants.

#### Immutable by default

- `set;` on a domain property.
- Public mutable fields on domain types.
- A `List<T>` or `Dictionary<,>` exposed where `IReadOnlyList<T>` or `IReadOnlyDictionary<,>` would fit.
- Assignment to instance state outside the constructor.

#### Pure functions over procedures

- A method in the domain layer that reaches for `DateTime.Now`, `Random`, `Console`, `File`, network, or the database.
- An `ILogger` argument threaded into core domain logic.
- A `void`-returning method outside constructors, registrations, and explicit side-effect boundaries.

#### Results, not exceptions

- A domain signature returning `T` whose body throws for a domain failure.
- `try`/`catch` inside domain code translating between exception types instead of returning a Result.
- An `ErrorOr` (or equivalent) return type whose error case is never pattern-matched at the call site.

#### Fail loud when prevention fails

- A `catch (Exception)` that swallows silently.
- A `catch` that logs and continues without rethrowing or converting.
- A constructor that accepts a null and stores it instead of guarding.

#### The domain doesn't know how it's stored

- `using Microsoft.EntityFrameworkCore;` (or `Dapper`, `Marten`, `Microsoft.Azure.Cosmos`) in a domain file.
- `[JsonPropertyName]`, `[DataContract]`, `[Column]`, `[Table]`, `[Key]` on a domain type.
- A `DbContext` or repository reference inside a domain method.

#### Inference, not annotation

- Explicit type annotations where `var` works (`string x = ...`, `List<Foo> z = new List<Foo>()`).
- IDE0007-shaped patterns the analyzer would flag in writing.

#### Modern idioms

- `new List<T>()` instead of `[]` or `new()`.
- `string.Format` or `+` concatenation instead of interpolated strings.
- Block-scoped namespaces instead of file-scoped.
- `if (x == null)` instead of `if (x is null)` or pattern matching.

#### Performance where it matters

- `.Count() > 0` instead of `.Any()`.
- `.ToList()` or `.ToArray()` inside a hot loop.
- A LINQ chain where a `Span<T>` or `for` would avoid allocations on a measured hot path.

#### Build gates are signal

- `#pragma warning disable` without a paired `restore` and a comment.
- `[SuppressMessage]` without a `Justification` string.
- `<NoWarn>1234</NoWarn>` in a `.csproj` or `Directory.Build.props` without the preceding comment block.
- `[ExcludeFromCodeCoverage]` on hand-written logic.

#### The first slice sets the pattern

- A new aggregate that diverges from the existing pattern in the same layer — mutable state where peers are immutable, exception throwing where peers return Results.

#### One source of truth

- The same magic number, error message, or path literal appearing in more than one file.
- Two type definitions for the same concept.
- A configuration value restated in both code and config.

#### The easy path is the correct path

- A service registered manually instead of via the canonical factory.
- Configuration that bypasses the fluent builder.

## Validation

"Beware of bugs in the above code; I have only proved it correct, not tried it" (Knuth). Validation for review is Boyd's OODA applied to a diff: observe the changes, orient against the writing-csharp rubric, decide severity, act by writing the finding. The finding artifact is the loop's output.

### The finding artifact

Findings live as one file per finding under `.findings/` at the repo root. The directory survives the session and is the durable record of the review.

File shape:

```
# <one-line title — the H1>

Severity: <important | nit | pre-existing>
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

Line 1 is the H1. Line 2 is blank. Lines 3-6 are the scannable head — severity, location, principle, summary. Line 7 is blank, then the `## Observation` body and its siblings.

The filename is the slug of the title: lowercase, non-alphanumeric replaced with dashes, leading and trailing dashes trimmed, capped at 80 characters.

### The script set

Four scripts ship under `${CLAUDE_PLUGIN_ROOT}/skills/reviewing-csharp/scripts/`. Portable POSIX bash; runs on Linux, macOS, and Windows (Git Bash, WSL).

- `changes.sh [<ref> | <ref1> <ref2>]` — produces the diff for the review. No args shows uncommitted changes against `HEAD` and the untracked-file list. One ref shows the diff against that ref. Two refs show the three-dot diff (PR-style: what is on `ref2` since it diverged from `ref1`).
- `report-finding.sh [--force] <title> <severity> <location> <principle> <summary>` — body piped on stdin. Slugifies the title for the filename, validates severity, refuses to overwrite without `--force`, writes `.findings/<slug>.md`.
- `list-findings.sh` — reads the first six lines of each `.findings/*.md` and emits one entry per finding: title, severity, location, principle, summary, slug filename. Use to dedup before composing a new finding.
- `summarize.sh` — counts findings by severity, prints the counts line and a verdict. Reads writing-csharp's Philosophy headings and flags any finding whose `Principle:` value is not a canonical heading; the mismatch is signal for the writing skill, not a defect.

### Output discipline

- Findings persist until the human deletes them; cleanup is manual.
- Filing is handled by `managing-github-issues` after human triage. The finding shape and the triage-proposal shape in that skill are deliberately compatible.
- `changes.sh`: success prints the three sections (files, diff, untracked when applicable). Failure prints git's error and exits with git's code.
- `report-finding.sh`: success is silent — the file is the artifact. Failure prints the validation error and exits non-zero.
- `list-findings.sh`: success prints the formatted finding list, or `no findings` when `.findings/` is empty or missing.
- `summarize.sh`: success prints the counts line, the verdict line, and the non-canonical-principle line when any apply.

### Gate policies

When a finding is malformed, the rule is: fix the finding.

- A finding without a `Principle:` line is a defect. Every finding traces to a principle, canonical or free-form.
- An `important` finding without a `## Suggested fix` is a defect. The author needs the path forward.
- A `pre-existing` finding for a line inside the diff is a defect. The scope is mis-classified — the line did change, so the finding is `important` or `nit`.
- A finding citing a non-canonical principle is a candidate for promotion into writing-csharp. `summarize.sh` surfaces it; the human decides during triage.
