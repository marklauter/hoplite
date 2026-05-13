# Finish writing tests for the remaining scripts

Tags: todo,tests
Eight more scripts need *_test.sh files after Phase 1 (taking-notes/query, 16 cases, green) proved the harness.

## Observation

- Single test file exists: `plugins/skills/skills/taking-notes/tests/query_test.sh` — 16 cases, all green.
- Harness lives at `plugins/skills/tests/run-tests.sh`. Convention: file names end in `_test.sh`; each test is a function named `test_<something>`; tests run in subshells with cwd at a fresh tmpdir and `$PLUGIN_ROOT` exported.
- Untested scripts by location:
  - `plugins/skills/skills/taking-notes/scripts/`: `take-note.sh`, `list-notes.sh`
  - `plugins/skills/skills/journaling/scripts/`: `journal-entry.sh`, `list-journal.sh`, `query.sh`
  - `plugins/skills/scripts/`: `report-finding.sh`, `list-findings.sh`, `query.sh`, `summarize.sh`
  - `plugins/skills/skills/managing-github-issues/scripts/`: 10 scripts, all wrapping `gh`
  - `plugins/skills/skills/writing-csharp/scripts/`: `build-gate.sh`
  - `plugins/skills/scripts/`: `changes.sh`

## Interpretation

- **Easy batch (next session)**: the 9 local-file scripts under notes/journal and the shared reviewer set. Deterministic with fixture directories; mirror the shape of `query_test.sh`. ~2-3 hours.
- **Harder, defer**: the 10 `managing-github-issues` scripts need `gh` mocked via PATH stub. Doable but more scaffolding per test.
- **Defer, needs git fixture**: `changes.sh` needs a git-initialized temp dir as fixture and produces output that varies with git state.
- **Probably skip at this layer**: `writing-csharp/scripts/build-gate.sh` orchestrates `dotnet format`/`build`/`test` against a real .NET project. Integration-style; unit-testing the orchestration doesn't catch much.

## Next

- Phase 2: write the 9 easy local-file tests in one batch — `take-note_test.sh`, `list-notes_test.sh`, `journal-entry_test.sh`, `list-journal_test.sh`, `journaling/query_test.sh`, `report-finding_test.sh`, `list-findings_test.sh`, `findings-query_test.sh`, `summarize_test.sh`.
- Phase 3: design a `gh` mock pattern (PATH stub or sourced helper) and write tests for the 10 managing-github-issues scripts.
- Phase 4: git-fixture pattern for `changes.sh`.
- Skip `build-gate.sh` for now; revisit if it grows non-trivial logic that isn't `dotnet` orchestration.
