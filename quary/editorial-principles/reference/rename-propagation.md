# Rename propagation

On renames and refactors, grep the project for the old name or path before declaring done; update every reference in the same change set.

## How to apply

- Identify the rename: old name or path → new name or path.
- Grep the entire project for the old name (filenames, identifiers, paths, documentation references, link targets).
- For each hit, update to the new name in the same change set.
- Run any tests or builds that exercise the renamed surface to catch missed references.

## Why this matters

A partial rename leaves the project in a broken state: documents reference identifiers that no longer exist, scripts reference paths that have moved. Renames are loud events; the rename must propagate atomically. Pair with **Cross-document cohesion read** in Validation.
