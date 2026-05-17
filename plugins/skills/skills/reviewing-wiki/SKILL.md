---
name: reviewing-wiki
description: Use when reviewing local markdown diffs in a software-project wiki before commit — GitHub wiki, docs site, or any partitioned set of pages organized by a sidebar. Produces structured findings under .findings/ classified by severity (important / nit / pre-existing) and lens (Structure / Line / Copy / Accuracy / Coherence / References). Self-contained rubric — does not load reviewing-documentation.
---

# Reviewing wiki

Pre-commit review of wiki diffs through six lenses — Structure, Line, Copy, Accuracy, Coherence, References — producing severity-classified findings under `.findings/` against the writing-wiki and writing-prose rubrics. Self-contained: the per-lens signals below cover both wiki-shaped concerns and general prose concerns, so the reviewer applies one rubric in one pass.

## Philosophy

The rubric is writing-wiki layered on writing-prose. Reviewing-wiki judges; the writing skills prescribe. Every finding traces to a Philosophy anchor — `writing-wiki` for wiki-shaped violations (section assignment, sidebar partition, register bleed, source-grounded claims) and `writing-prose` for general prose violations (voice, density, sentence-case, define-by-presence). The skill copies and refines the reviewing-documentation rubric rather than composing with it at runtime; runtime composition of signal sets across two reviewer skills is unreliable.

### Findings are observations, not commands

The reviewer reports; the author decides. A finding describes what the prose does and why a principle is violated; it does not demand the fix. The Suggested fix section offers a path, not an instruction.

### The scope must be explicit

Every review pass declares its scope. Two modes:

- **Diff mode** — the pre-commit gate. `changes.sh` (no args) produces the canonical diff against `HEAD`. Findings attach to lines in the diff. Pre-existing defects on lines the diff did not touch are surfaced as `pre-existing` findings, not chased into adjacent work.
- **Audit mode** — the routine whole-wiki pass. `changes.sh --all` (or `--paths <p>...`) enumerates the files in scope. For wiki review, audit is the default — wikis are commonly reviewed in batches before publishing, independent of any in-progress edit. In audit mode `pre-existing` does not apply (no diff to be "outside of"); findings are `important` or `nit` only.

The Coherence and References lenses always require reading the whole wiki — sidebar, Home, sibling pages — to detect drift, terminology conflicts, and link integrity. In diff mode the findings still attach to lines in the diff; in audit mode they attach to whatever pages or structural files the defect lives in.

### Sections own the triple

Before judging a page, locate it in `_Sidebar.md` and read the other pages in its section. The section declares the audience, tone, and register the page must honor — a tutorial-friendly opening is not a defect in the Getting Started section but is a defect in a Reference section. A register mismatch between the page and its section is a Structure-lens finding.

### Source code is the accuracy authority

Every factual claim in a wiki page is verifiable against source code or an external specification the page cites. The Accuracy lens checks the claim against source — not against training data, not against inference. A claim that cannot be verified is flagged for resolution, not assumed correct.

### Evidence-based

Every finding quotes the prose and cites the principle. The form is: "this paragraph deviates from {principle} because {observation about the prose}." Specificity makes findings actionable. Vague findings ("this section feels weak") fail the test.

Quote enough to locate the issue and no more. A short quote plus a `path:line` is sufficient; a multi-paragraph quote is rarely needed.

### Severity encodes the action

The vocabulary — important, nit, pre-existing — names the action the author should take, not how bad the prose is. Naming the action keeps attention on what changes shipability. The definitions live in Guidance.

### Findings discover principles

A finding that cites a non-canonical principle is a candidate for promotion into writing-wiki or writing-prose. The reviewer can free-form the `Principle:` field when no canonical anchor fits; `summarize.sh` surfaces these for the author to triage. The writing skills grow from review pressure rather than from speculative additions.

## Guidance

Concrete patterns for producing findings and running the workflow.

### The workflow

1. Locate the source clone and detect the host. The standard layout is sibling clones — when CWD is `{project}.wiki/`, the source clone is the sibling directory `{project}/` (strip the `.wiki` suffix from CWD's name), and the host is GitHub by convention (the `.wiki` repo is paired with the GitHub repo of the same name). The Accuracy lens cites source as `(source: ../{project}/path/to/file:line)`. The References lens applies GitHub wiki link rules — see the References signals below. When the wiki lives inside the source repo instead (a `docs/` subdirectory or a self-hosted wiki engine), source paths resolve normally within the repo and link rules follow whichever renderer the docs site uses.
2. Pick the scope. For wiki review, the default is audit mode: `changes.sh --all .` enumerates the wiki's files. When a fresh diff exists (uncommitted page edits), `changes.sh` with no args produces the diff view instead. Diff mode is the pre-commit gate; audit mode is the routine whole-wiki pass before publishing.
3. Read enough surrounding context of each in-scope page to detect the operating triple (audience, tone, register).
4. For each in-scope page, open `_Sidebar.md` to confirm which section it belongs to. Read at least two sibling pages in the same section to detect the section's triple. A page whose register does not match its section's is itself a finding.
5. Evaluate each in-scope page against the writing-wiki and writing-prose principles through each of the six lenses. When a principle is violated, compose a finding.
6. `report-finding.sh --type wiki --lens <name>` writes the finding to `.findings/<slug>.md`. The slug comes from the title; the script enforces the type, severity, and lens enums. Slug collisions auto-suffix (`-2`, `-3`, ...) — writes always succeed, so repeated audit passes accumulate findings rather than silently dropping them.
7. `list-findings.sh` enumerates the current findings by reading each file's head. Scan it before composing a new finding — match on title, principle, and lens, since the slug catches reworded duplicates. `query.sh --type wiki --lens <name>` is the tool for predicate-driven scans (filter by lens, severity, principle, etc.) when the finding set has grown.
8. `summarize.sh` collapses the directory to counts plus verdict. Run it when the review pass is complete. The verdict reads `review passes`, `review passes; nits optional`, or `review blocked on important findings` — same vocabulary in diff and audit modes.

### Severity calibration

- important — the prose contradicts source code (Accuracy), breaks a hard editorial rule that changes how the reader understands the page (factual claim, broken cross-reference, malformed page structure, register mismatch with the section, orphaned page, broken sidebar link), or violates a writing-wiki or writing-prose Philosophy anchor with real cost. Blocks the review.
- nit — style miss, idiom miss, or judgment call without behavioral consequence (a sentence that could be tighter, a heading that could be sharper, a missing Oxford comma). The author may fix or skip.
- pre-existing — diff-mode only. Defect on prose the diff did not touch, surfaced because the reviewer's eye fell on it while reviewing nearby changes. Not blocking. Natural input to triage for follow-up work. In audit mode `pre-existing` does not apply — there is no diff to be "outside of"; every defect is `important` or `nit`.

Calibration check — would a skilled technical editor flag this on a software-project wiki? If "probably not," skip it.

### Detect the section triple before judging

The reviewer's first move is to read the sibling pages in the same sidebar section to detect the section's triple — audience, tone, register. A finding that says "too informal" is meaningless without knowing the register the section operates in.

- Tutorial-register sections (Getting Started, Quickstart) are allowed to walk the reader through, address them as "you," use imperative steps, and provide more context than reference would.
- Reference-register sections (API, Configuration) are allowed to be terse, declarative, and organized for lookup.
- Recipe-register sections (Recipes, Cookbook) are allowed to be hybrid — task framing on top of reference-density meat. They name the scenario, then show the construction.
- Concepts-register sections (Architecture, Design) are allowed to take positions and assert opinions.

A register mismatch is itself a finding — when the page's register does not match its sidebar section, flag it under the Structure lens for page-wide mismatch or the Line lens for sentence-level drift.

### The Principle and Lens fields

- `Principle:` prefers a writing-wiki or writing-prose Philosophy anchor verbatim. The match links the finding to the rubric and keeps the vocabulary stable.
- When no existing anchor fits, use a free-form descriptor. `summarize.sh` flags the mismatch; these findings are candidates for promotion into writing-wiki or writing-prose.
- `Lens:` is required and is one of the six. The lens names the kind of defect; the principle names the rule violated. A single defect maps to one lens — when it could map to two, choose the lens whose signals (listed in Per-lens signals below) catch it most directly.

### Location

- Single location is the default: `` `path/to/Page-Name.md:42` ``. Repo-relative path, the most relevant line.
- Multiple locations for the same defect are comma-separated: `` `docs/A.md:10, docs/B.md:25` ``. Use only when the locations share the exact same defect; distinct defects get distinct findings even when they violate the same principle in the same lens.
- Accuracy findings cite both the doc line and the source `path:line` that the doc contradicts: `` `Building-A-Pipeline.md:14 (source: src/Pipeline/Builder.cs:88)` ``.
- Sidebar and Home findings cite the structural file plus the affected entry: `` `_Sidebar.md:18 (page: Recipe-Webhook-Receiver.md)` ``.

### Dedup before writing

- Same defect on a different line: update the existing finding's Location to a comma-separated list by editing the file directly, rather than creating a second file. (`report-finding.sh` auto-suffixes on slug collision, so a re-file would create `<slug>-2.md` rather than overwrite. Edit the original.)
- Same principle violation in a different shape: separate findings. The artifact is per-defect, not per-principle.
- Same defect in two different lenses: this is rare and usually means the lens choice was wrong. Pick the more specific lens and merge.
- In audit mode, the same defect found across successive runs accumulates as `<slug>.md`, `<slug>-2.md`, `<slug>-3.md`. Manual cleanup (delete the older files) is the user's responsibility — the script does not auto-prune.

### Per-lens signals

Each subsection names the kinds of defects the lens catches on a wiki page. The signals are not exhaustive — they are the patterns the reviewer's eye looks for first. Evaluate every signal against the section triple detected earlier.

#### Structure

Page-level organization, ordering, section assignment, sidebar partition, Home shape.

- The page lacks a lede — the first sentence does not name what the page is for and what the reader of this section gets from it.
- The page's register does not match its sidebar section's register (a Reference-register page in the Getting Started section, a Tutorial-register page in the Reference section).
- The page is in the wrong section for its audience (a contributor-facing architecture page filed under Getting Started, a user-facing tutorial filed under Architecture).
- Architecture or internals are presented before usage on a user-facing page. Usage and behavior come before how it works.
- Sections appear in an order that breaks the reader's path (advanced concepts before basics on a tutorial page, edge cases before the happy path on a reference page).
- A required section for the page type is missing (a Recipe page without a "When this recipe applies" or equivalent scope statement, a Reference page without the API surface it claims to cover).
- Two sections on the page cover the same ground.
- A heading uses Title Case where the rest of the page uses sentence case.
- The page is missing from `_Sidebar.md` (orphaned page) or `_Sidebar.md` points at a page that does not exist on disk (dangling sidebar entry).
- `_Sidebar.md` has grown a section past roughly seven pages without splitting — the partition is no longer a cognitive map.
- `Home.md` enumerates every page in the wiki instead of directing the reader to sections.
- `Home.md` points at a section that no longer exists, or fails to mention a section that does.
- The page documents a capability that does not exist in the source. "Document only what exists" is a Structure-lens defect — the page should not be in the wiki.

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
- Register drift within a page — a tutorial page whose middle sections lapse into reference voice, a reference page whose introduction lapses into tutorial voice.
- Negative framing where positive framing carries the same meaning ("not invalid" → "valid"; "don't forget to call X" → "call X").

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
- File-naming inconsistency in the wiki (`Recipe-Webhook-Receiver.md` next to `webhook_receiver.md`).

#### Accuracy

Claims that contradict the source code or the authoritative artifact.

- A function signature, parameter list, or return type that does not match the source.
- A configuration key, default value, or environment variable that does not match what the code reads.
- A command-line flag, argument order, or required flag that the implementation does not support.
- A version number, dependency, or feature claim that does not match the actual state of the system.
- A path, file name, or URL that does not exist.
- A behavior description that contradicts what the code does.
- A code sample that does not compile against the current source.
- An external reference (RFC, vendor doc, spec URL) the page depends on that has changed or is unreachable.
- A claim about behavior, signature, or default that lacks a source citation — accuracy is verifiable only when the citation is present.
- Findings in this lens require the source citation in the Location field: `` `Building-A-Pipeline.md:14 (source: src/Pipeline/Builder.cs:88)` ``.

#### Coherence

Cross-page semantic drift, contradiction, and section partition violations.

- Two pages describe the same concept with conflicting definitions or scope.
- A term defined in the Concepts page (or its section equivalent) is used elsewhere with a meaning that differs from the canonical definition.
- A role or actor described on one page is described differently on another (different responsibilities, different scope).
- Two pages name the same event, command, or artifact with different shapes.
- A page claims another page covers something that the other page does not actually cover.
- Two pages within the same section cover the same ground without naming the partition — they teach the reader twice and confuse them once.
- A page borrows the voice of a different section it links to (a recipe page that adopts reference voice when summarizing the concept it depends on; a tutorial that pastes in a reference table instead of linking).
- A page documents a capability that another page in the wiki claims has been removed or replaced.

Coherence findings always quote both pages and name the conflict explicitly. The author decides which page is canonical.

#### References

Link integrity, sidebar partition integrity, and cross-reference correctness.

- A link target page does not exist on disk.
- A link target page exists but does not contain the content the link text implies (a link labeled "Middleware" pointing to a page about request lifecycle).
- A glossary or Concepts term used meaningfully across multiple pages is absent from the canonical definition page.
- A defined role, concept, or artifact is referenced in prose but has no canonical page defining it.
- `_Sidebar.md` omits a page that exists on disk (orphaned page).
- `_Sidebar.md` lists a page that does not exist on disk (dangling entry).
- `_Sidebar.md` link text misrepresents the target (a sidebar entry labeled "Quickstart" pointing at a 400-line reference page).
- `Home.md` points at a section heading that does not exist in `_Sidebar.md`.
- Anchor links to headings within a page do not resolve to actual headings.
- An external link (vendor doc, RFC, repo, package registry) returns 404 or has been redirected to unrelated content.
- On a GitHub-hosted wiki (CWD ending in `.wiki`), a wiki-to-wiki link includes the `.md` extension — `[text](Page-Name.md)` renders broken; the form GitHub resolves is `[text](Page-Name)`.
- On a GitHub-hosted wiki, a cross-page or in-page anchor uses a fragment that does not match GitHub's heading-slug transform (lowercase, spaces and punctuation to hyphens). `#Picking-A-Strategy` does not resolve; `#picking-a-strategy` does.
- On a GitHub-hosted wiki, a link into the companion source repo uses a relative `../{project}/path` path that does not resolve at render time. The form that works in the browser is an absolute `https://github.com/<owner>/<repo>/blob/<ref>/<path>` URL, optionally with `#L42`.
- `_Sidebar.md` or `Home.md` entries on a GitHub-hosted wiki include `.md` in link targets, producing a broken sidebar.

## Validation

Findings are the artifact of the review pass. Each finding is one file under `.findings/`.

### The finding artifact

Findings live as one file per finding under `.findings/` at the repo root. The directory survives the session and is the durable record of the review.

File shape for wiki findings:

```markdown
# <one-line title — the H1>

Severity: <important | nit | pre-existing>
Type: wiki
Lens: <Structure | Line | Copy | Accuracy | Coherence | References>
Location: `path/to/Page-Name.md:42`
Principle: <writing-wiki or writing-prose Philosophy anchor>
<one-line summary>

## Observation
<observable facts about the prose, with a short quote>

## Why it matters
<which principle, concrete cost to the reader>

## Suggested fix
<corrected text for line/copy fixes, or prose describing the change>
```

The H1 is line 1. Head fields are read by name, not by line offset. The summary is the line immediately after `Principle:`. The body sections follow.

The filename is the slug of the title: lowercase, non-alphanumeric replaced with dashes, leading and trailing dashes trimmed, capped at 80 characters.

### The script set

The same scripts as reviewing-documentation and reviewing-csharp ship under `${CLAUDE_PLUGIN_ROOT}/scripts/`. Portable bash 3.2+; runs on Linux, macOS, and Windows (Git Bash, WSL).

- `changes.sh [<ref> | <ref1> <ref2> | --all [<dir>] | --paths <p>...]` — produces the canonical scope. No args shows uncommitted changes against `HEAD` and the untracked-file list (diff mode). One ref shows the diff against that ref; two refs show the three-dot diff (PR-style). `--all [<dir>]` walks the filesystem (default `.`), respects `.gitignore`, skips hidden and symlinked entries; output is the file list only. `--paths <p>...` enumerates the given files and directories (directories expand recursively under the same walker); errors on a missing path. When invoked with no args against a clean tree or outside a git repo, the script emits a structured hint and exits non-zero — the calling skill picks a default from there.
- `report-finding.sh --type wiki [--lens <name>] <title> <severity> <location> <principle> <summary>` — body piped on stdin. For wiki findings, `--type wiki` and `--lens <name>` are required. Slugifies the title for the filename, validates the type, severity, and lens enums, writes `.findings/<slug>.md`. On slug collision, auto-suffixes (`-2`, `-3`, ...) — every call succeeds.
- `list-findings.sh` — reads the head fields of each `.findings/*.md` and emits one entry per finding: title, severity, type, lens (when present), location, principle, summary, slug filename. Use to dedup before composing a new finding.
- `query.sh [--title PAT] [--severity LEVEL] [--xseverity LEVEL] [--type KIND] [--xtype KIND] [--lens NAME] [--xlens NAME] [--location PAT] [--principle PAT] [--summary PAT]` — filters findings by structured predicates. Multiple predicates AND together; no predicates matches every finding. The `--x*` flags exclude matches on the enum fields (severity, type, lens). Use `--type wiki` to scan only wiki findings; `--xlens References` to filter out reference-checking output; `--xseverity pre-existing` to focus on actionable findings.
- `summarize.sh` — counts findings by severity per type, prints a lens breakdown when wiki findings are present, prints the verdict line, and flags any finding whose `Principle:` value is not a canonical writing-wiki or writing-prose heading. When `CLAUDE_PLUGIN_ROOT` is unset or the writing skill files are unreadable, the canonical-principle check is skipped and a warning prints to stderr.

The `wiki` type is registered in `report-finding.sh`'s type enum. `summarize.sh` checks wiki findings' `Principle:` field against the union of `writing-wiki/SKILL.md` and `writing-prose/SKILL.md` Philosophy headings — a wiki finding may legitimately cite either rubric. `query.sh --type wiki` filters to wiki findings only.

### Output discipline

- Findings persist until the author deletes them; cleanup is manual.
- Filing is handled by `managing-github-issues` after author triage. The finding shape and the triage-proposal shape in that skill are compatible.
- `changes.sh`: success prints the three sections (files, diff, untracked when applicable). Failure prints git's error and exits with git's code.
- `report-finding.sh`: success is silent — the file is the artifact. Failure prints the validation error and exits non-zero.
- `list-findings.sh`: success prints the formatted finding list, or `no findings` when `.findings/` is empty or missing.
- `query.sh`: success prints matching findings in `list-findings.sh` format, or `no matches` when predicates exclude everything.
- `summarize.sh`: success prints the per-type counts, the lens breakdown when wiki findings exist, the verdict line, and any non-canonical-principle lines. Stderr carries a warning when the rubric files are unreadable.

### Gate policies

When a finding is malformed, the rule is: fix the finding.

- A finding without a `Principle:` line is a defect. Every finding traces to a principle, canonical or free-form.
- A wiki finding without a `Lens:` line is a defect. Every wiki finding belongs to one of the six lenses.
- An `important` finding without a `## Suggested fix` is a defect. The author needs the path forward.
- A `pre-existing` finding for a line the diff modified is a defect. The scope is mis-classified — the line did change, so the finding is `important` or `nit`.
- A `pre-existing` finding produced in audit mode is a defect. Audit mode has no diff; every defect is `important` or `nit`.
- A finding citing a non-canonical principle is a candidate for promotion into writing-wiki or writing-prose. `summarize.sh` surfaces it; the author decides during triage.
- An Accuracy finding without a source `path:line` in the Location field is malformed. The whole point of the Accuracy lens is the source citation.
- A Structure finding about section assignment, sidebar partition, or Home shape that does not name the affected structural file (`_Sidebar.md` or `Home.md`) in the Location field is malformed. The reviewer needs to know which structural file is broken.
