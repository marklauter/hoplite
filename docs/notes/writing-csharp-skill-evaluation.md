---
title: Writing-csharp skill evaluation
summary: Above average for the genre, but pays a structural tax — three parallel passes over the same skeleton (Philosophy / Guidance / Validation) inflate it to ~300 lines for ~150 lines of load-bearing content.
tags: [note, skills, writing-csharp, evaluation]
created: 2026-05-25
aliases: []
---

## Findings

Honest read: it's above average for the genre, but it pays a structural tax that the strongest writing-skills don't.

## What it gets right

- Doesn't waste tokens on C# basics. Every bullet is an opinionated call a reader could plausibly get wrong (`internal sealed` default, smart constructors over public ctors, ErrorOr in domain only).
- The infrastructure-only vs. domain-modeling carve-out for Results is the right move — most C# skills I've seen pretend the distinction doesn't exist and end up wrong half the time.
- Build gates are concrete: analyzer IDs, MSBuild props, the exact `dotnet format` scoping recipe. That's the kind of thing models hallucinate when it's vague.
- `${CLAUDE_PLUGIN_ROOT}/...` anchoring on the script — the trap from CLAUDE.md is avoided.
- ArchUnitNET-as-forcing-function is a genuinely good idea and the skill threads it through consistently.

## What's weak

1. **Three parallel passes over the same skeleton.** Philosophy / Guidance / Validation each repeat the same ten H3s. A reader threading "what about Results?" reads three sections to assemble one rule. That's ~300 lines for what's probably 150 lines of load-bearing content.
2. **Philosophy reads as essay, not rules.** "Push side effects to the boundary; keep the interior computational" is true but a model already knows it. The Guidance bullets do the actual work. Philosophy could collapse to a one-line gloss per principle, or move to a sidecar.
3. **Scope creep into project setup.** Coverage ratchets, CPM, `Directory.Packages.props`, BenchmarkDotNet thresholds — these are real, but they're *configuring a .NET solution*, not *writing C#*. A `setting-up-dotnet-solution` peer skill would carry them better and let writing-csharp focus. See [[write-the-scaffolding-csharp-skill]] and [[write-the-writing-architecture-skill]].
4. **Undefined custom primitives leak.** `IValue<TSelf, TValue>` and the `Unit` `readonly record struct` are presented as idioms, but they're presumably the author's. A reader following the skill in a fresh codebase will reach for them and find nothing. Either show the definition, point to where it lives, or mark them as "if your codebase has this pattern."
5. **Repetition across sections.** Primary constructors appear in Modern idioms *and* The easy path. TimeProvider in Pure functions *and* Performance. The parallel-axis structure forces the same idiom to be restated under each lens it touches.
6. **A few rules are stated more assertively than the surrounding C# community holds them.** `internal sealed` by default is a strong stance most .NET codebases don't share — fine to advocate, but the skill should acknowledge it's a deliberate choice rather than presenting it as a universal default.

## Recommendation

Cut Philosophy to a one-line gloss per principle (or sidecar it). Fold Validation bullets into the Guidance bullet they correspond to, so each rule is one entry that says *what to do, what the gate is, and why*. Move the solution-configuration material to a peer skill. That gets it to maybe 180 lines, single-pass, and the model loads less to get more.

Net: solid bones, opinionated in the right places, but the three-axis structure is doing real damage to information density.
