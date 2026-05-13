---
name: reviewing-documentation
description: Use when reviewing local markdown diffs before commit. Produces structured findings under .findings/ classified by severity (important / nit / pre-existing) and lens (Structure / Line / Copy / Accuracy / Coherence / References).
---

# Reviewing documentation

Pre-commit review of markdown diffs through six lenses — Structure, Line, Copy, Accuracy, Coherence, References — producing severity-classified findings under `.findings/` against the writing-documentation rubric.

## Philosophy

These principles draw on a few orienting threads. Fagan on formal inspection — defect detection is the work, and severity calibration is the discipline that keeps it useful. Pólya on observation before interpretation — name what the prose does, then name the principle from which it departs. Strunk and White on the asymmetric cost of wasted words.

The rubric is writing-documentation. Reviewing-documentation judges; writing-documentation prescribes. The two skills co-evolve. Every finding traces to a writing-documentation Philosophy anchor — the Philosophy section is the contract the reviewer enforces; the Guidance section applies it.

### Findings are observations, not commands

The reviewer reports; the author decides. A finding describes what the prose does and why a principle is violated; it does not demand the fix. The Suggested fix section offers a path, not an instruction.

The reviewer's authority comes from the rubric, not from preference. Every finding cites the contract.

### The diff is the scope

Review the lines that changed and the surrounding context required to understand them. Pre-existing defects on lines the diff did not touch are surfaced as `pre-existing` findings, not chased into adjacent work. A whole-corpus audit is a different activity with different output.

The Coherence and References lenses are exceptions in degree — they require reading sibling documents to detect drift and link integrity, but the findings still attach to lines in the diff.

### Evidence-based

Every finding quotes the prose and cites the principle. The form is: "this paragraph deviates from {principle} because {observation about the prose}." Specificity makes findings actionable. Vague findings ("this section feels weak") fail the test.

Quote enough to locate the issue and no more. A short quote plus a `path:line` is sufficient; a multi-paragraph quote is rarely needed.

### Severity encodes the action

The vocabulary — important, nit, pre-existing — names the action the author should take, not how bad the prose is. Important means the diff does not ship without resolution. Nit means a fix is welcome but optional. Pre-existing means the defect is not from this diff. Naming the action keeps the author's attention budget on the changes that change shipability.

### Findings discover principles

A finding that cites a non-canonical principle is a candidate for promotion into writing-documentation. The reviewer can free-form the `Principle:` field when no canonical anchor fits; `summarize.sh` surfaces these for the author to triage. The writing skill grows from review pressure rather than from speculative additions.

## Guidance

Concrete patterns for producing findings and running the workflow.

### The workflow

1. `changes.sh` produces the canonical diff plus the changed-file list. Read the diff and enough surrounding context of each changed page to detect the operating register.
2. Detect the register from sibling documents before judging. A tutorial-friendly opening is not a defect in a tutorial folder.
3. For each changed line, evaluate against writing-documentation principles through each of the six lenses. When a principle is violated, compose a finding.
4. `report-finding.sh --type documentation --lens <name>` writes the finding to `.findings/<slug>.md`. The slug comes from the title; the script enforces the type, severity, and lens enums and refuses to overwrite without `--force`.
5. `list-findings.sh` enumerates the current findings by reading each file's head. Scan it before composing a new finding — match on title, principle, and lens, since the slug catches reworded duplicates. `query.sh --type documentation --lens <name>` is the tool for predicate-driven scans (filter by lens, severity, principle, etc.) when the finding set has grown.
6. `summarize.sh` collapses the directory to counts plus verdict. Run it when the review pass is complete.

### Severity calibration

- important — the prose contradicts source code (Accuracy), breaks a hard editorial rule that changes how the reader understands the page (factual claim, broken cross-reference, or malformed page structure that prevents the page from doing its job), or violates a writing-documentation Philosophy anchor with real cost. The diff does not ship without resolution.
- nit — style miss, idiom miss, or judgment call without behavioral consequence (a sentence that could be tighter, a heading that could be sharper, a missing Oxford comma). The author may fix or skip.
- pre-existing — defect on prose the diff did not touch, surfaced because the reviewer's eye fell on it while reviewing nearby changes. Not blocking. Natural input to triage for follow-up work.

Calibration check — would a skilled technical editor flag this? If "probably not," skip it.

### Detect the register before judging

The reviewer's first move is to read the sibling documents and the parent directory's prose to detect the operating register. A finding that says "too informal" is meaningless without knowing the register the document operates in.

- Tutorial-register documents are allowed to walk the reader through, address them as "you," use imperative steps, and provide more context than reference would.
- Reference-register documents are allowed to be terse, declarative, and organized for lookup.
- Vision-register documents are allowed to take positions and assert opinions.

A register mismatch is itself a finding — when the document's register does not match its directory, flag it under the Structure lens for page-wide mismatch or the Line lens for sentence-level drift.

### The Principle and Lens fields

- `Principle:` prefers a writing-documentation Philosophy anchor verbatim. The match links the finding to the rubric and keeps the vocabulary stable.
- When no existing anchor fits, use a free-form descriptor. `summarize.sh` flags the mismatch; these findings are candidates for promotion into writing-documentation.
- `Lens:` is required and is one of the six. The lens names the kind of defect; the principle names the rule violated. A single defect maps to one lens — when it could map to two, choose the lens whose signals (listed in Per-lens signals below) catch it most directly.

### Location

- Single location is the default: `` `path/to/page.md:42` ``. Repo-relative path, the most relevant line.
- Multiple locations for the same defect are comma-separated: `` `docs/A.md:10, docs/B.md:25` ``. Use only when the locations share the exact same defect; distinct defects get distinct findings even when they violate the same principle in the same lens.
- Accuracy findings cite both the doc line and the source `path:line` that the doc contradicts: `` `docs/api.md:14 (source: src/Api.cs:88)` ``.

### Dedup before writing

- Same defect on a different line: update the existing finding's Location to a comma-separated list with `report-finding.sh --force`, rather than creating a second file.
- Same principle violation in a different shape: separate findings. The artifact is per-defect, not per-principle.
- Same defect in two different lenses: this is rare and usually means the lens choice was wrong. Pick the more specific lens and merge.

### Per-lens signals

Each subsection names the kinds of defects the lens catches. The signals are not exhaustive — they are the patterns the reviewer's eye looks for first. Evaluate every signal against the operating register: a reference document is allowed third person and dry density; a tutorial is allowed walks-the-reader-through pacing. The register sets the floor for what counts as a violation.

#### Structure

Page-level organization, ordering, gaps, and redundancy.

- The page lacks a lede — the first sentence does not name what the page is for.
- Sections appear in an order that breaks the reader's path (architecture before usage, conclusions buried after long justifications).
- A required section for the artifact type is missing (an ADR without a Decision section, a skill without Validation).
- A section is present that the artifact's shape does not call for.
- Two sections cover the same ground.
- A heading uses Title Case where the rest of the page uses sentence case.
- A page that should stand alone requires the reader to follow links before the first sentence makes sense.
- The page's register does not match the directory's register (formal in a folder of tutorials, friendly in a folder of references).

#### Line

Sentence-level clarity, voice, tense, density.

- Voice violations: third person ("the user should", "one might"), passive voice where active works ("the engine is called by..."), first person plural ("we recommend") in non-narrative contexts.
- Tense drift: future ("will return") or past ("returned") where present applies. Most documentation describes behavior in the present.
- Hedges in declarative prose: *might*, *perhaps*, *could be*, *it's worth noting*, *might want to*.
- Filler: *basically*, *simply*, *just*, *actually*, *really*, *quite*, *very*, *in order to*.
- Wordy stock phrases that have short forms: *at this point in time* → *now*, *due to the fact that* → *because*, *in the event that* → *if*.
- Transitions that announce instead of saying. "In this section we will discuss X" — say X.
- A sentence that restates the previous sentence in different words.
- A paragraph that restates an adjacent paragraph at a different length.
- Dense paragraphs of four or more sentences carrying multiple ideas that should split.

#### Copy

Grammar, formatting, mechanical consistency.

- Sentence-case headings broken (a Title-Case heading in a sentence-case page).
- Em dash typed as double hyphens (`--`) instead of the character (`—`).
- Oxford comma missing in a list of three or more.
- Bold (`**...**`) in the prose. Headings, lists, and prose carry structure on their own.
- Tables (`|---|`) where headings and bullets would serve.
- Code, paths, identifiers, or CLI commands not in backticks.
- Link text that is "click here" or "this page" instead of describing the target.
- A code fence missing its language tag.
- Inconsistent capitalization of defined role names (User in one paragraph, user in the next, when the term refers to the same actor).

#### Accuracy

Claims that contradict the source code or the authoritative artifact.

- A function signature, parameter list, or return type that does not match the source.
- A configuration key, default value, or environment variable that does not match what the code reads.
- A command-line flag, argument order, or required flag that the implementation does not support.
- A version number, dependency, or feature claim that does not match the actual state of the system.
- A path, file name, or URL that does not exist.
- A behavior description that contradicts what the code does.
- Findings in this lens require the source citation in the Location field: `` `docs/api.md:14 (source: src/Api.cs:88)` ``.

#### Coherence

Cross-page semantic drift and contradiction.

- Two pages describe the same concept with conflicting definitions or scope.
- A term defined in the glossary is used in a page with a meaning that differs from the glossary definition.
- A role described in one page is described differently in another (different responsibilities, different scope).
- Two pages name the same event, command, or artifact with different shapes.
- A page claims another page covers something that the other page does not actually cover.
- Two pages each claim ownership of the same concept without naming the partition.

Coherence findings always quote both pages and name the conflict explicitly. The author decides which page is canonical.

#### References

Link integrity and cross-reference correctness.

- A link target file does not exist.
- A link target file exists but does not contain the content the link text implies (a link labeled "Authentication" pointing to a page about caching).
- A glossary term is used meaningfully across multiple pages but absent from the glossary.
- A defined role, concept, or artifact is referenced in prose but has no canonical page defining it.
- A catalog or index page omits an artifact that exists, or lists an artifact that does not exist.
- Anchor links to headings within a page do not resolve to actual headings.

## Validation

"Beware of bugs in the above code; I have only proved it correct, not tried it" (Knuth). Validation for review is the loop applied to prose: observe the diff, orient against the rubric, decide severity, act by writing the finding. The finding artifact is the loop's output.

### The finding artifact

Findings live as one file per finding under `.findings/` at the repo root. The directory survives the session and is the durable record of the review.

File shape for documentation findings:

```markdown
# <one-line title — the H1>

Severity: <important | nit | pre-existing>
Type: documentation
Lens: <Structure | Line | Copy | Accuracy | Coherence | References>
Location: `path/to/page.md:42`
Principle: <writing-documentation Philosophy anchor>
<one-line summary>

## Observation
<observable facts about the prose, with a short quote>

## Why it matters
<which principle, concrete cost to the reader>

## Suggested fix
<corrected text for line/copy fixes, or prose describing the change>
```

The H1 is line 1. The head fields are written by name, so the reader scripts find them by name rather than by line offset. The summary is the line immediately after `Principle:`. The body sections `## Observation`, `## Why it matters`, and `## Suggested fix` follow.

The filename is the slug of the title: lowercase, non-alphanumeric replaced with dashes, leading and trailing dashes trimmed, capped at 80 characters.

### The script set

Five scripts ship under `${CLAUDE_PLUGIN_ROOT}/scripts/`, shared with reviewing-csharp. Portable bash 3.2+; runs on Linux, macOS, and Windows (Git Bash, WSL).

- `changes.sh [<ref> | <ref1> <ref2>]` — produces the diff for the review. No args shows uncommitted changes against `HEAD` and the untracked-file list. One ref shows the diff against that ref. Two refs show the three-dot diff (PR-style: what is on `ref2` since it diverged from `ref1`).
- `report-finding.sh [--force] --type <code|documentation> [--lens <name>] <title> <severity> <location> <principle> <summary>` — body piped on stdin. For documentation findings, `--type documentation` and `--lens <name>` are required. Slugifies the title for the filename, validates the type, severity, and lens enums, refuses to overwrite without `--force`, writes `.findings/<slug>.md`.
- `list-findings.sh` — reads the head fields of each `.findings/*.md` and emits one entry per finding: title, severity, type, lens (when present), location, principle, summary, slug filename. Use to dedup before composing a new finding.
- `query.sh [--title PAT] [--severity LEVEL] [--xseverity LEVEL] [--type KIND] [--xtype KIND] [--lens NAME] [--xlens NAME] [--location PAT] [--principle PAT] [--summary PAT]` — filters findings by structured predicates. Multiple predicates AND together; no predicates matches every finding. The `--x*` flags exclude matches on the enum fields (severity, type, lens). Use `--type documentation` to scan only doc findings; `--xlens References` to filter out reference-checking output; `--xseverity pre-existing` to focus on actionable findings.
- `summarize.sh` — counts findings by severity per type, prints a lens breakdown when documentation findings are present, prints the verdict line, and flags any finding whose `Principle:` value is not a canonical writing-documentation heading. When `CLAUDE_PLUGIN_ROOT` is unset or the writing-documentation skill file is unreadable, the canonical-principle check is skipped and a warning prints to stderr.

### Output discipline

- Findings persist until the author deletes them; cleanup is manual.
- Filing is handled by `managing-github-issues` after author triage. The finding shape and the triage-proposal shape in that skill are compatible.
- `changes.sh`: success prints the three sections (files, diff, untracked when applicable). Failure prints git's error and exits with git's code.
- `report-finding.sh`: success is silent — the file is the artifact. Failure prints the validation error and exits non-zero.
- `list-findings.sh`: success prints the formatted finding list, or `no findings` when `.findings/` is empty or missing.
- `query.sh`: success prints matching findings in `list-findings.sh` format, or `no matches` when predicates exclude everything.
- `summarize.sh`: success prints the per-type counts, the lens breakdown when documentation findings exist, the verdict line, and any non-canonical-principle lines. Stderr carries a warning when the rubric file is unreadable.

### Gate policies

When a finding is malformed, the rule is: fix the finding.

- A finding without a `Principle:` line is a defect. Every finding traces to a principle, canonical or free-form.
- A documentation finding without a `Lens:` line is a defect. Every documentation finding belongs to one of the six lenses.
- An `important` finding without a `## Suggested fix` is a defect. The author needs the path forward.
- A `pre-existing` finding for a line the diff modified is a defect. The scope is mis-classified — the line did change, so the finding is `important` or `nit`.
- A finding citing a non-canonical principle is a candidate for promotion into writing-documentation. `summarize.sh` surfaces it; the author decides during triage.
- An Accuracy finding without a source `path:line` in the Location field is malformed. The whole point of the Accuracy lens is the source citation.
