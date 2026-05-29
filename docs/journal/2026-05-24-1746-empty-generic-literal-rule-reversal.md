---
title: Empty-generic-literal rule reversal
summary: A semgrep rule against `frozenset[str]()` and similar empty-generic-with-explicit-type-param literals added at 17:34 and reverted at 17:46. The rule was right about a real pattern; the cost of reading the rule's diagnostic was higher than the cost of letting the pattern exist.
document:
  tags: [journal, hoplite, python, tooling, dead-end]
  created: 2026-05-24
---

# Empty-generic-literal rule reversal

A semgrep rule against `frozenset[str]()` and similar empty-generic-with-explicit-type-param literals added at 17:34 and reverted at 17:46. The rule was right about a real pattern; the cost of reading the rule's diagnostic was higher than the cost of letting the pattern exist.

## What the rule was for

In `test_filtering.py`, tests construct candidate tuples with frozensets. Empty-labels candidates need a typed empty frozenset:

```python
candidate = ("a.md", frozenset[str]())
```

Without the type parameter, pyright can't infer the element type and flags the bare `frozenset()` as `frozenset[Unknown]`. With the type parameter, pyright is happy. The pattern is correct.

The rule proposed: forbid `frozenset[T]()` when the call is empty; require `frozenset()` plus a type annotation on the surrounding variable, or `cast(frozenset[T], ...)`, or some other shape that reads less awkwardly.

## Why it got reverted

Reading the rule's diagnostic was worse than reading the pattern. Every test that needed an empty typed frozenset now had to choose between:

- Drop the type parameter and explicitly annotate the binding: `empty: frozenset[str] = frozenset()`. Two lines instead of one.
- Wrap in a helper: `def _empty() -> frozenset[str]: ...`. Adds a helper for a pattern that occurs in tests only.
- Cast the result: `cast(frozenset[str], frozenset())`. Adds an import and reads as ceremony.

The pattern the rule was forbidding (`frozenset[str]()`) wasn't a bug. It was Python's standard syntax for typed-empty-generic literals. The rule was a style preference dressed as a defect.

The signal: when the agent read the rule's diff, the work to comply with it felt heavier than the work the rule was supposed to save. That's the feedback that landed the revert.

## Decisions captured

- Style preferences are not lint rules. A lint rule exists to prevent defects or to enforce constraints that have a clear cost-of-violation. `frozenset[str]()` has no cost-of-violation; the rule was personal style.
- Read the diff before committing to a rule. The 12-minute reversal happened because the next thing the agent did was read its own diff and notice it was making the code worse. Reading the diff is the cheapest signal you'll get.
- Rules that fire too widely lose authority. A linter that flags a dozen non-bugs trains the developer to scroll past linter output. Better to ship fewer rules and have each rule mean something.

## What this didn't change

The original pattern stays. `test_filtering.py` continues to use `frozenset[str]()` for typed empty frozensets in test data. Pyright is happy. The reader doesn't have to wonder what shape the empty frozenset is.

## Cross-references

- `[[journal/2026-05-24-1918-first-hoplite-modules]]` — the broader Python module work this commit lived inside.
- `[[journal/2026-05-24-1701-python-toolchain-and-writing-python-skill]]` — the toolchain that the rule was being added to.
