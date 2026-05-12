---
name: managing-github-issues
description: Use when listing, searching, deduplicating, or filing GitHub issues. Covers gh CLI workflows, issue templates, label vocabulary, and the search-before-file discipline.
---

# Managing GitHub Issues

Philosophy, guidance, and validation for working with GitHub issues via the `gh` CLI.

## Philosophy

These principles draw on a few orienting threads. Evans on ubiquitous language — labels and titles are the shared vocabulary between code, agents, and humans. Norman on affordances and forcing functions — templates make the right shape the easy shape. Hickey on values and one source of truth — the issue tracker is the canonical backlog, and every fact lives in exactly one issue.

They describe what good issue hygiene looks like. They apply on every interaction with the tracker without exception.

### Search before file

Every problem lives in exactly one issue. Before any create operation, the agent searches open and closed issues for the same problem. The search is non-negotiable — finding a prior occurrence is more valuable than filing a new entry, because it carries the history of why the problem persisted.

### The template is the schema

Issue templates encode the project's intent — required fields, allowed values, the questions every report must answer. A filed issue conforms to its template: every required field present, every dropdown value drawn from the template's `options` array. Read the template before composing the body.

### One issue, one problem

Each issue describes a single defect, a single piece of debt, or a single behavioral mismatch. A report that bundles three concerns is three issues. Atomic issues are searchable, prioritizable, and closable. Each split entry moves independently through triage and closure.

### Concrete references over prose

Code references point at file and line. Repros are minimal and self-contained. Expected and actual state observable behavior — the symbol, the value, the call. The agent describes what the code does.

### Labels carry meaning

The label vocabulary is the domain language of the tracker. New labels are introduced deliberately, keeping the namespace coherent. Every filing carries at least one label — that is how future searches find it.

### The tracker is the source of truth

The issue tracker holds the canonical state of every known problem. Status (open/closed), assignment, and resolution live in GitHub, not in commit messages, chat threads, or documents. Code changes that resolve an issue close it; the tracker reflects state without lag.

### Confirm before mutating

Listing and searching are read-only and run freely. Creating, closing, commenting, and editing are mutations and pause for explicit confirmation. Mutations are reversible only by additional mutations.

### Triage is decision, not data entry

Triage is the act of deciding what an issue is, where it belongs, and whether it should remain open. The agent surfaces candidates and proposes actions in a structured document; the human approves or redirects entry by entry; a script applies the approved mutations one at a time. Every triage decision is a judgment about the project's backlog, and judgment is what the human keeps. The document is the audit trail — the agent's reasoning is reviewable before any state changes.

## Guidance

Concrete patterns for the `gh` CLI and the consolidated scripts. Each subsection mirrors a philosophy heading.

### Search before file

- Run `find.sh` before any file operation. The script searches both open and closed issues and prints any hits with state markers.
- Match on the underlying concept. A bug about "key serialization fails on nested maps" matches a prior issue titled "nested map keys produce malformed binary" — same concept, different wording.
- When a match exists, show it to the user with the URL and state. Ask whether to comment on the existing issue, reopen if closed, or proceed with a new filing because the prior issue is genuinely distinct.
- When no match exists, state that explicitly before composing the new issue. "No open or closed issues matched `<keywords>`." Announcing the gate result on every filing keeps the dedup discipline visible.

### The template is the schema

- Discover templates first. `ls .github/ISSUE_TEMPLATE/` lists available templates; common filenames are `bug-report.yml`, `tech-debt.yml`, `feature-request.yml`. Repos with nested project roots may have templates at `<project>/.github/ISSUE_TEMPLATE/`.
- Read the template YAML before composing. Extract field `id` values, `label` text, `required` flags, and `options` arrays for dropdowns. The body must include every required field.
- Build the body as `### Field Label` headings matching the template's `label` values, with the user-provided or inferred content beneath each heading. Optional fields with no content use `_No response_` — the gh tracker renders this consistently with the web form.
- Dropdown values match the template's `options` exactly — gh validates against the array, so the body uses the literal text. When inferring a dropdown value, list the allowed options first to make the constraint visible.
- Template-declared `labels:` apply on every issue created through `create.sh`. The script reads the YAML, merges with the `LABELS` env var, and passes the combined set to `gh`.

### One issue, one problem

- Before composing, restate the problem as a single sentence. If the sentence needs "and" between two concerns, file two issues.
- Issues cross-reference each other with "see also" notes; each body still describes one concern.
- Bundled refactors split by area. "Refactor serialization layer" becomes one issue per file or per concern, with a parent tracking issue if coordination is needed.

### Concrete references over prose

- Code references use the form `` `path/to/file.cs:42` — brief description ``. The path is repo-relative; the line is the most relevant line, not a range. Multiple references list one per line.
- Repros are minimal. A C# repro is a single test method or program that triggers the defect; the body uses `render: csharp` if the template specifies it.
- Expected versus actual states observable behavior. "Returns `Result.NotFound`" — the exact symbol, the exact value. The reader reproduces the issue from the body alone.
- Stack traces and error output go in fenced code blocks. Truncate to the relevant frames; the full trace is rarely the signal.

### Labels carry meaning

- Use the project's existing label vocabulary. `labels.sh` enumerates known labels; the agent picks from that set unless the user introduces a new one.
- Type labels (`bug`, `tech-debt`, `enhancement`) classify the issue. Area labels (`serialization`, `transactions`, `core`) locate it. Priority labels (`priority:high`, `priority:medium`, `priority:low`) rank it. The three axes compose.

### The tracker is the source of truth

- Closing is a mutation; `close.sh <number>` reads the comment from stdin so the reason rides with the closure — fixed in commit X, superseded by issue Y, won't-fix because Z.
- Linking commits to issues uses GitHub's keyword syntax in the commit message (`Fixes #123`, `Closes #45`). The keyword closes the issue automatically on merge to the default branch.
- When the same problem resurfaces, reopen the prior issue — the history of why it was closed carries forward as context for the new occurrence.

### Confirm before mutating

- List, search, and label-vocabulary operations run without prompting. `list.sh`, `find.sh`, `labels.sh`, and `triage-list.sh` are read-only.
- Create, close, reopen, and comment operations show the full proposed payload before invoking the script. For creation: the rendered body, title, labels, and template name.
- Edits go through `edit.sh`, which prints the resolved invocation before applying the change.

### Triage is decision, not data entry

Triage decides six things for each candidate:

- Whether the issue describes a real, actionable problem. A report carrying enough signal to act on names what happened, where, and how to observe it; reports that fall short of that bar close with the comment `invalid: insufficient detail`. The `noise-candidates` filter surfaces filed-and-forgotten one-liners so the agent reads them first.
- Whether the issue is a duplicate. `find.sh` runs against the candidate's title and key terms; a match closes the candidate with `duplicate of #N`, or reopens the prior issue when it had been closed prematurely.
- The type. `bug`, `tech-debt`, `enhancement`, `feature-gap`, `documentation`, or whatever the project's type vocabulary is. Triage picks exactly one.
- The area. The project's area vocabulary applies; triage assigns one. When the issue's location falls outside it, the agent surfaces the gap so the human can decide whether to introduce a new label.
- The priority. `priority: high` / `priority: medium` / `priority: low`, or the project's spelling. Triage assigns one — the agent picks the best fit from the body and resolves ambiguity by asking the human.
- The state. Remain open, close, or reopen. The agent proposes close-as-resolved (with a commit reference), close-as-invalid (noise), and close-as-duplicate. Close-as-won't-fix is a human-only decision; the agent proposes it only when the user has named the rationale.

A fully triaged issue carries a label on each axis — type, priority, area — and shows recent activity. The validation filters surface candidates that fall short on at least one axis:

- `unlabeled` — no labels at all.
- `no-priority` — no label whose name begins with `priority`. Handles both `priority:high` and `priority: high`.
- `no-area` — no label whose name begins with `area`, or no label in the project's area vocabulary when that vocabulary uses bare names (configured via `AREA_LABELS`).
- `stale` — no activity in N days (default 90). Activity is `updatedAt`, which includes comments and label changes, not just the original filing date.
- `noise-candidates` — no labels, zero comments, and body shorter than `NOISE_BODY_CHARS` (default 200) or empty. Catches filed-and-forgotten one-liners.

The triage workflow runs in three steps. First, the agent enumerates candidates with `triage-list.sh <filter>` and runs `find.sh` against each candidate's title and key terms to surface duplicates. Second, the agent composes a triage proposal document — one entry per candidate, in heading order matching the list output. Third, the human reviews the document and approves entries individually or as a set; the agent then runs `edit.sh`, `close.sh`, or `reopen.sh` once per approved entry.

The triage proposal document uses one heading per candidate, in this exact shape:

```
### Triage NNN — #<issue-number> <issue-title>

Action: <Label | Close | Reopen | Comment | NoChange>
Add labels: <list or none>
Remove labels: <list or none>
Close reason: <fixed in commit X | duplicate of #N | won't-fix because Y>
Rationale: <one or two sentences>
```

`Action` is the verb the agent will execute when the human approves. `Add labels` and `Remove labels` list label names exactly as they appear in `labels.sh`. `Close reason` is required when `Action` is `Close` and omitted otherwise. `Rationale` is the one-or-two-sentence justification — what made the agent choose this action, citing the issue body, prior comments, or related issues by number.

Canonical mutation calls during triage:

- Labels, title, assignee, milestone: `edit.sh <number> --add-label "..." --remove-label "..." --title "..." --add-assignee "@me" --milestone "v1.2"`. Prints the diff being applied and exits on the first failure.
- Close with comment: `close.sh <number>` with the reason piped on stdin — fixed in commit X, duplicate of #N, won't-fix because Y.
- Reopen with comment: `reopen.sh <number>` with the reason piped on stdin — the problem resurfaced, the prior decision was revisited, a related fix regressed.
- Free-form comment: `comment.sh <number>` with the body piped on stdin.

### gh CLI canonical invocations

The scripts wrap these `gh` calls — reference for reading script output and extending the set.

- List by state: `gh issue list --state open|closed|all`. Default is open.
- Filter by label: `--label "tech-debt"`. Multiple `--label` flags AND together.
- Search keywords: `--search "keyword"`. The search runs against title and body.
- JSON output: `--json number,title,state,labels,url --limit 100`. The scripts format this into one line per issue.
- Create non-interactively: `gh issue create --title "..." --body-file - --label "..."`. The `--body` or `--body-file` flag is required without a TTY; `gh` rejects `--template` together with either, so `create.sh` reads the template YAML directly for label extraction.

## Validation

"Make the right way the easy way" (Norman). When a script exists for an operation, the agent runs the script. The scripts collapse multi-step workflows into single invocations, enforce output discipline, and live in the plugin install location so the canonical invocations stay stable across consuming repos.

### The script set

Nine scripts cover the workflow. All ship under `${CLAUDE_PLUGIN_ROOT}/skills/managing-github-issues/scripts/`. Portable POSIX bash; runs on Linux, macOS, and Windows (Git Bash, WSL).

Every script that takes a body or comment reads it from stdin rather than as a CLI argument, so the agent composes content as a plain string in its tool call rather than escaping quotes, backticks, dollar signs, or newlines for the shell.

- `list.sh [state] [label] [search]` — lists issues with optional filters. State defaults to `open`; pass `closed` or `all` to widen. Output is one line per issue: `#<number> [<state>] [<labels>] <title>  <url>`.
- `find.sh <keywords...>` — the dedup gate, used before filing and during triage. Searches both open and closed issues and prints matches with state markers. Empty result prints `no matches`; exit code is `0` either way — a clean dedup result is success.
- `labels.sh` — lists the repository's labels, one per line as `<name>  <description>`. The agent runs this before composing a filing or a triage entry so label names match exactly.
- `create.sh <template-name> <title>` — reads the body from stdin. Locates the template under `.github/ISSUE_TEMPLATE/`, extracts its `labels:` declaration, merges with the `LABELS` env var, and passes the combined set to `gh`. (`gh` rejects `--template` with `--body-file`, hence reading labels from YAML.) The template name is required — it names the schema the body conforms to, and locating the YAML verifies the template exists. Example: `LABELS="priority:high,area:serialization" create.sh tech-debt.yml "title"`.
- `triage-list.sh [filter]` — enumerates triage candidates. Filter is one of `unlabeled`, `no-priority`, `no-area`, `stale`, `noise-candidates`; default is `unlabeled`. Output matches `list.sh`. Filter semantics and environment overrides (`AREA_LABELS`, `STALE_DAYS`, `NOISE_BODY_CHARS`) are in the Triage Guidance subsection.
- `edit.sh <number> [flags]` — wraps `gh issue edit` for a single issue. Flags pass through: `--add-label`, `--remove-label`, `--add-assignee`, `--remove-assignee`, `--title`, `--milestone`, `--body`, `--body-file`. Prints the resolved invocation before calling `gh` so the human sees the exact diff being applied. One issue per invocation — walking a triage document is the agent's job, not the script's, so the confirmation pause happens between entries.
- `close.sh <number>` — closes an issue with a mandatory comment read from stdin. Empty stdin is an error, so every closure carries a reason. Prints the resolved invocation, then gh's confirmation on success.
- `reopen.sh <number>` — reopens with a mandatory stdin comment naming what changed since closure. Same output discipline as `close.sh`.
- `comment.sh <number>` — adds a comment via `gh issue comment --body-file -` with the body on stdin. Same output discipline as `close.sh`.

### Output discipline

Each script captures stdout and stderr from its underlying `gh` call. On failure, the captured output prints in full and the script exits with the command's code. On success:

- `list.sh` prints the formatted issue list.
- `find.sh` prints matches or `no matches`.
- `labels.sh` prints the label list or `no labels`.
- `create.sh` prints the created issue's URL.
- `triage-list.sh` prints the candidate list or `no candidates`.
- `edit.sh` prints the resolved `gh issue edit` invocation, then the issue URL on success.
- `close.sh`, `reopen.sh`, `comment.sh` print the resolved invocation, then gh's confirmation line on success.

Each script has one underlying `gh` call, so the script name labels its output — no `==> step-name` prefix.

### Gate policies

When a gate fires, the rule is the same as in any other skill: fix the underlying cause.

- The tracker holds one canonical issue per problem. `find.sh` runs before every `create.sh` to keep that invariant.
- The body conforms to the template: every required field present, every dropdown value drawn from the template's `options` array. The agent reads the template YAML before composing.
- Template-declared labels apply automatically through `create.sh`; the `LABELS` env var carries any extras.
- Every closure and reopen carries a comment that names the reason — `close.sh` and `reopen.sh` enforce this by treating empty stdin as an error.
- Triage mutations pause for confirmation, one entry at a time. The agent presents the proposal in full; the human approves entries; the agent runs `edit.sh`, `close.sh`, or `reopen.sh` once per approved entry.

### Layered defense

GitHub's API rejects malformed payloads — the first gate. The template YAML defines required fields and allowed values — the second. Dedup-before-file catches duplicates the API cannot — the third. The scripts encode the canonical invocations so they stay stable across calls — the fourth. The triage proposal document is the fifth, interposing a human review between candidate enumeration and mutation so each label edit traces back to a reviewed entry. Each layer carries the load it can carry.
