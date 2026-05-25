[![claude code](https://img.shields.io/badge/Claude%20Code-plugin-d97757?logo=anthropic)](https://docs.claude.com/en/docs/claude-code/plugins)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![MSL Armory](https://raw.githubusercontent.com/marklauter/claude/main/images/msl.armory.small.png "MSL Armory")

# claude plugin

*Another weapon from the MSL Armory*

A single git repo to maintain Claude Code skills, replacing copies spread across many project repos.

## Install locally

From inside Claude Code, with `<repo>` as the absolute path to your clone (the directory holding `.claude-plugin/marketplace.json`):

```text
/plugin marketplace add <repo>
/plugin install armory@msl.armory
```

After editing a skill, run `/reload-plugins` to apply.

## Structure

```text
.claude-plugin/marketplace.json           # marketplace manifest
plugins/armory/                          # the "armory" plugin
  .claude-plugin/plugin.json
  mcp/                                    # Hoplite MCP server (knowledge graph)
  hooks/                                  # SessionStart bootstrap + PostToolUse validator
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

## Adding a skill

1. Create `plugins/armory/skills/<skill-name>/SKILL.md`.
2. If the skill ships executable behavior, add `scripts/` and `tests/` subdirectories. Tests follow the `*_test.sh` convention documented at the top of `plugins/armory/tests/run-tests.sh`.
3. `/reload-plugins` in Claude Code to test.
4. Commit and push.

## Skills and shared tooling

Writers — produce durable artifacts:

- `writing-csharp` — C# and .NET; type-driven design, immutability, Result-based error handling.
- `writing-prose` — foundation for skills that produce prose artifacts; the editorial spine other writer skills compose with.
- `writing-wiki` — pages in a software-project wiki; loads alongside `writing-prose`.
- `taking-notes` — atomic wiki pages under `docs/notes/`, each representing the current state of an idea.
- `journaling` — dated, append-only entries under `docs/journal/`.

Reviewers — surface findings under `.findings/`:

- `reviewing-csharp`, `reviewing-prose`, `reviewing-wiki` — pre-commit review of local diffs.
- `triaging-findings` — walks `.findings/` in severity order; the steward decides each disposition.

GitHub:

- `managing-github-issues` — list, search, dedupe, file, triage, comment.

Shared scripts at `plugins/armory/scripts/` — the writer and readers over `.findings/`:

- `report-finding.sh` — writes a `.findings/<slug>.md` with the canonical head-field shape.
- `list-findings.sh`, `query.sh`, `summarize.sh` — read the head fields; reviewer skills and `triaging-findings` invoke these instead of enumerating the directory.
- `_lib.sh` — sourced helpers for head-field parsing and repo-anchored `.findings/` resolution.

Bash test runner at `plugins/armory/tests/run-tests.sh`:

- Discovers `*_test.sh` files anywhere under the plugin and runs each `test_*` function in a fresh tmpdir under `set -e`.
- Ships an assertion library (`assert_equal`, `assert_contains`, `assert_match`, `assert_exit_code`, `assert_file_exists`, ...) documented inline at the top of the file.

## Publishing to GitHub

Push this repo to GitHub, then update the marketplace source in consumers:

```text
/plugin marketplace remove msl.armory
/plugin marketplace add <github-user>/<repo-name>
```

No restructuring needed.
