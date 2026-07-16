---
title: Python toolchain and the writing-python skill
summary: After spec wraps in the morning, the afternoon stands up the Python side — writing-python skill, writing-code component, ruff + pyright gate, src/tests layout for the MCP package. Tooling discipline locks in before any real code lands.
tags: [journal, mcp, python, tooling, milestone]
created: 2026-05-24
---

# Python toolchain and the writing-python skill

After spec wraps in the morning, the afternoon stands up the Python side — `writing-python` skill, `writing-code` component, ruff + pyright gate, src/tests layout for the MCP package. Tooling discipline locks in before any real code lands.

## Intent

The data-model and the SQLite-hybrid storage decision settled overnight. Implementation needs to land next, and Python is the chosen language ([[docs/decisions/prototype-the-plugin-mcp-server-in-python.md]] settled this). Before writing actual hoplite logic, the toolchain needs to be in place — linter, type-checker, layout, skill body teaching how to author Python here.

Doing the toolchain first is deliberate. The bash plugin established that fail-fast posture matters; the Python side should ship with the same discipline from line one.

## What landed (chronological)

- 2026-05-24 16:38 — Hoplite spec sweep: init tool, day-one MinHash, CWD-as-corpus, /hoplite skill. Final pre-implementation spec pass — confirms what the first code session will build against. The init tool gets a slot; MinHash lands as day-one (not deferred); the working-directory becomes the corpus root by convention.
- 2026-05-24 16:40 — Add `writing-python` skill and `writing-code` component; restructure mcp python to src/tests layout. The src-layout pattern over flat-package; tests as a sibling tree to src; standard pyproject.toml shape.
- 2026-05-24 17:01 — Add label expression parser; configure ruff + pyright gate. First real Python lands at the same time as the linter and type-checker that gate it. Configuration in pyproject.toml; pyright in strict mode; ruff rule set picked to include the kinds of things bash discipline was already enforcing (no unused, no implicit-any-style sloppiness, no string-formatting fragility).

## What the skill teaches

`writing-python` declares its rhetorical context against `writing-prose` (foundation) and injects the `writing-code` component for the cross-language coding principles. The Python-specific overrides:

- src/tests layout. `pyproject.toml` at repo root; package source under `src/<package>`; tests in a sibling `tests/` tree.
- Type-checker is strict. Pyright in strict mode; no `Any` without justification; no implicit return types on public functions.
- Linter is opinionated. Ruff rule set covering style, imports, comprehensions, and Python-specific footguns.
- Tests use pytest. Test discovery follows the standard naming (`test_*.py`).
- No `from __future__ import annotations` blanket — opt in per module if a circular type reference demands it. (This decision evolved over the following week.)

## Decisions captured

- Toolchain before code. The lint/type-check gate has to be running before the first line of business logic, so every commit ships clean. Retrofitting lint discipline onto an existing codebase is a much bigger move than starting with it.
- Pyright over mypy. Faster, friendlier diagnostics, better support for the kind of dataclass-heavy code Hoplite would be. The cost is one more tool in the chain; the benefit is staying out of mypy's slow paths.
- Ruff over flake8/black/isort. One binary covers what used to take three; configuration in one file; the speed lets a pre-commit hook run without complaint.
- `writing-python` is a downstream of `writing-prose`. Same foundation/downstream pattern as the existing prose skills. The python-specific section overrides Genre (code), Tone (declarative), Audience (engineer + LLM consumer of generated code).
- `writing-code` as a component shared with future language skills. The skill is Python; the component covers what would generalize to writing-csharp or writing-go later.

## What this set up

The next several hours produce the first real hoplite modules — label-expression parser, candidate-filter, MinHash, IDs, wikilinks — all built against this toolchain from line one. Every commit in that run goes through ruff + pyright clean. See `[[journal/2026-05-24-1918-first-hoplite-modules]]`.

## Next

Label-expression parser, candidate-filter wrapper, MCP stub surface, MinHash, IDs module, wikilinks module — the building blocks land in sequence over the rest of the day. See `[[journal/2026-05-24-1918-first-hoplite-modules]]`.
