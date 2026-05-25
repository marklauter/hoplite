---
title: Write the scaffolding-csharp skill
summary: New skill for setting up new C# projects — solution layout, Directory.Build.props, central package management, ArchUnit test scaffolding, the works.
tags: [note, todo, skills, csharp, scaffolding]
created: 2026-05-25
aliases: []
---

## Observation

A new C# project at this codebase's standards involves a lot of identical setup: `Directory.Build.props` with strict analyzers and nullable, `Directory.Packages.props` for central package management, the per-layer test project pattern, ArchUnitNET tests as structural gates, the build script. None of this is captured as a skill today; each new project is hand-assembled.

## Interpretation

A `scaffolding-csharp` skill would codify the "new project" workflow:

- Solution structure (domain-driven onion layout — `Domain`, `Domain.PortX`, `Domain.PortX.AdapterY`, with paired `*.Tests` projects).
- `Directory.Build.props` with `<Nullable>enable</Nullable>`, `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>`, `<AnalysisMode>All</AnalysisMode>`, coverage thresholds.
- `Directory.Packages.props` with CPM enabled and `CentralPackageTransitivePinningEnabled`.
- Initial ArchUnitNET test scaffolding for the standard rules (sealed concrete classes, no public instance fields, namespace shape, layer dependencies).
- The `build-gate.sh` script wired in.
- A starter `Domain` smart-constructor / Result type if appropriate.

Open question: ship as a skill (instructions Claude follows) or as a real `dotnet new` template (one command bootstraps)? Probably the skill drives a `dotnet new` template once one exists — the skill teaches the standards, the template carries them out.

## Next

- Inventory the projects Mark already builds against these standards; extract the common scaffold from the most recent example.
- Decide skill vs. template (or both — skill that invokes the template, then customizes).
- Draft as a code-family skill alongside `writing-csharp` (which has its own shape; structural divergence between prose and code families is accepted per the `writing-prose` refactor decisions).
- Coordinate with `writing-csharp` — scaffolding sets up the environment that writing-csharp's rules then apply to.
