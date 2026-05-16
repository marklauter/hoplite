# msl.armory — a collection of skills

A single git repo to centrally maintain Claude Code skills, replacing copies spread across many project repos.

## Structure (subject to drift)

```
.claude-plugin/marketplace.json           # marketplace manifest
plugins/skills/                           # the "skills" plugin
  .claude-plugin/plugin.json
  scripts/                                # shared reviewer scripts
  tests/                                  # bash test runner + tests for shared scripts
  skills/<skill-name>/
    SKILL.md                              # the skill body
    scripts/                              # optional, skill-owned
    tests/                                # optional, skill-owned
docs/
  notes/                                  # taking-notes output
  journal/                                # journaling output
```

## Install locally

From any directory inside Claude Code, with `<repo>` set to the absolute path of your clone of this repo (the directory containing `.claude-plugin/marketplace.json`):

```
/plugin marketplace add <repo>
/plugin install skills@msl.armory
```

After editing a skill, run `/reload-plugins` to apply.

## Skill template

Every skill is a single `SKILL.md` that looks roughly like this:

```markdown
---
name: <skill-name>
description: When this skill should activate. Be specific about trigger phrases and topics.
---

# <Skill Title>

Brief prose describing what this skill covers.

## Philosophy

The principles behind the domain. Why this works the way it does.

## Guidance

Concrete patterns, idioms, and rules. The dense reference material.

## Validation

How to verify the work meets the philosophy and guidance.
```

- Skill name: gerund form per Anthropic best practices (`writing-X`, `reviewing-X`, `triaging-X`).
- Description: the trigger. Claude reads this to decide whether to load the skill — invest in it.
- Body: the domain knowledge that gets injected when the skill activates.

Individual skills drift from this template as their domain demands; the canonical reference is `plugins/skills/skills/writing-csharp/SKILL.md`.

## Adding a skill

1. Create `plugins/skills/skills/<skill-name>/SKILL.md` following the template above.
2. If the skill ships executable behavior, add `scripts/` and `tests/` subdirectories. Tests follow the `*_test.sh` convention documented at the top of `plugins/skills/tests/run-tests.sh`.
3. `/reload-plugins` in Claude Code to test.
4. Commit and push.

## Skills and shared tooling

Writers — produce durable artifacts:

- `writing-csharp` — C# and .NET; type-driven design, immutability, Result-based error handling.
- `writing-documentation` — durable markdown of every kind; the prose spine other writer skills compose with.
- `writing-wiki` — pages in a software-project wiki; loads alongside `writing-documentation`.
- `taking-notes` — atomic wiki pages under `docs/notes/`, each representing the current state of an idea.
- `journaling` — dated, append-only entries under `docs/journal/`.

Reviewers — surface findings under `.findings/`:

- `reviewing-csharp`, `reviewing-documentation`, `reviewing-wiki` — pre-commit review of local diffs.
- `triaging-findings` — walks `.findings/` in severity order; the steward decides each disposition.

GitHub:

- `managing-github-issues` — list, search, dedupe, file, triage, comment.

Shared scripts at `plugins/skills/scripts/` — the runtime index over `.findings/`:

- `report-finding.sh` — writes a `.findings/<slug>.md` with the canonical head-field shape.
- `list-findings.sh`, `query.sh`, `summarize.sh` — read the head fields; reviewer skills and `triaging-findings` invoke these instead of enumerating the directory.
- `_lib.sh` — sourced helpers for head-field parsing and repo-anchored `.findings/` resolution.

Bash test runner at `plugins/skills/tests/run-tests.sh`:

- Discovers `*_test.sh` files anywhere under the plugin and runs each `test_*` function in a fresh tmpdir under `set -e`.
- Ships an assertion library (`assert_equal`, `assert_contains`, `assert_match`, `assert_exit_code`, `assert_file_exists`, ...) documented inline at the top of the file.

## Publishing to GitHub later

Push this repo to GitHub, then update the marketplace source in consumers:

```
/plugin marketplace remove msl.armory
/plugin marketplace add <github-user>/<repo-name>
```

No restructuring needed.
