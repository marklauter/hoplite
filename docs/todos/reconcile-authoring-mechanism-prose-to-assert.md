---
title: Reconcile authoring-mechanism prose to assert
summary: "The spec prose still names `declare` and `describe` as the two authoring mechanisms, but both have collapsed into `assert` (the single authoring act). Update `hoplite-authoring.md` and the README map line that still split them."
tags: [note, todo, hoplite]
created: 2026-06-20
status: evolving
---

# Reconcile authoring-mechanism prose to assert

The glossary collapsed the authoring acts: `author`, `declare`, and `describe` all retired into `assert` ("To advance a claim"), now locked at `docs/glossary:assert`. The engine side is `infer` ("To derive a feature"), contrasted with `assert`. So there is one authoring act, not the old `declare` (relationships) / `describe` (annotations) pair.

The spec prose hasn't caught up. Sites still encoding the dead two-mechanism split:

- `docs/specs/hoplite-authoring.md` — the title and H1 read "Authoring — declare relationships, describe documents"; the body reads "two mechanisms: declare and describe" and has the `## Declare and describe — applying explicit structure` section. Rewrite it around the single `assert` act (a stub, so cheap).
- `docs/specs/README.md` line 47 — "the write-side mutation surface for asserting features (declare relationships, describe documents)". Drop the parenthetical split.

Both are `stub`/`wip`, so this trails the glossary lock rather than blocking it.
