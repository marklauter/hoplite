---
title: Migrate run-tests.sh to vendored crucible
summary: Swap our in-repo bash test runner for the sibling crucible.sh; two small migration items block the cut.
tags: [todo, crucible]
created: 2026-05-25
aliases: []
---

## Observation

`plugins/armory/tests/run-tests.sh` is our current bash test runner. The sibling project `D:\crucible\crucible` ships `crucible.sh` (version 0.1.0, no release tags yet) as a single-file, drop-in runner with the same conventions: `*_test.sh` files, `test_*` functions, optional `setup`/`teardown`, per-test subshell with cwd at a fresh tmpdir, `set -e` inside the test.

Crucible is a strict superset of our runner on assertions except `assert_exit_code`. It adds:

- `run <cmd>` capture helper populating `$status`/`$stdout`/`$stderr`/`$output`/`$lines`
- Stream assertions: `assert_status`, `assert_stdout_contains`, `assert_stderr_match`, etc.
- `--filter <regex>` to run a single test by name
- `--list` to enumerate without running
- `bash -n` syntax-check before sourcing (our runner silently produces "0 passed" on broken files)
- `skip [reason]`, `fail [msg]`, `--verbose`, `--ascii`

Two migration items:

1. **`$PLUGIN_ROOT` → `$PROJECT_ROOT`.** Our runner exports `$PLUGIN_ROOT` (= `plugins/armory`). Crucible exports `$PROJECT_ROOT` (= git toplevel). All 12 test files reference `$PLUGIN_ROOT`. Either mechanical sed (`$PLUGIN_ROOT` → `$PROJECT_ROOT/plugins/armory`) or one line in a shared helper: `export PLUGIN_ROOT="$PROJECT_ROOT/plugins/armory"`.
2. **`assert_exit_code` missing in crucible.** 48 call sites across 11 files. Cheapest: add a shim to a shared helper — `assert_exit_code() { assert_equal "$1" "$2" "${3:-}"; }`. Cleaner long-term: rewrite to `run cmd; assert_status N`.

## Interpretation

The shim path means zero edits to existing test files. Net wins (`--filter`, `--list`, syntax-check, `run` capture) outweigh the migration cost. No release tags on crucible yet means we vendor the file and track sibling HEAD manually until it cuts releases — acceptable for now.

## Next

- Vendor `crucible.sh` to `plugins/armory/tests/crucible.sh`.
- Add a shared helper (e.g. `plugins/armory/tests/_helpers.sh`) sourcing line: `export PLUGIN_ROOT="$PROJECT_ROOT/plugins/armory"` plus the `assert_exit_code` shim. Have each `*_test.sh` source it at the top — or have crucible do it via a `crucible.config.sh` pattern if that lands upstream.
- Delete `plugins/armory/tests/run-tests.sh`.
- Update any CI invocations and docs that reference `run-tests.sh` (Skill `Testing` page in the wiki, top-level README's "Bash test runner" section).
