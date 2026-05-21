# Extract shared scan lib after third skill

tags: todo,refactor,scripts
Journaling and taking-notes scan scripts are ~80% duplicated; defer the shared lib until a third skill adopts the pattern so the abstraction fits three instances instead of two.

## Status

Todo, deferred. Waiting on a third skill to adopt the head + predicates scan pattern before extracting.

## Current instances

- `plugins/skills/skills/journaling/scripts/scan.sh`
- `plugins/skills/skills/taking-notes/scripts/scan.sh`

## Shared shape (~80%)

- Predicate-parsing loop with `--title`, `--tag`, `--xtag`, `--summary`
- `to_lower` helper for case-insensitive substring matching
- Comma-tag membership via `,${tags// /},` pattern
- `nullglob`-guarded file iteration over a fixed directory
- Predicate-echo on empty match: `no <items> matching <flags>`
- Block-per-match output: title, tags, summary, filename
- Exit 0 on clean empty result

## Real differences

- Journaling adds `--since YYYY-MM-DD` and `--until YYYY-MM-DD` filtering against the filename's date prefix; notes does not.
- Journaling head carries a `date:` field on line 3 (`tags:` on line 4, summary on line 5); notes head has no date (`tags:` on line 3, summary on line 4).
- Journaling output block includes a `date:` line; notes does not.
- Scanned directory: `docs/journal` vs `docs/notes`.

## Why deferred — rule of three

Two examples can mislead the abstraction; the shared shape between them may be coincidental. A lib drawn from two will fit a third badly. Wait for the third concrete instance before factoring.

## What to do when the third arrives

Likely shape: a sourced `plugins/skills/scripts/_scan_lib.sh` exporting the predicate-parsing loop, `to_lower`, the membership test, and the empty-match printer. Each skill keeps a thin `scan.sh` that defines its head schema (which lines hold which fields) and its output block format, then delegates the loop to the shared lib. Parallels how `plugins/skills/scripts/_lib.sh` factors `findings_dir` / `get_field` out of the findings query.
