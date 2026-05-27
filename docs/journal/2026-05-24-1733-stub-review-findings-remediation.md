---
title: Stub-review findings remediation
summary: Echo-style stubs for the hoplite MCP tool surface went through a real review pass at 17:33 — 21 minutes after the stubs landed at 17:12. The review surfaced shape and contract issues that would have ridden through to the real implementations untouched if the stubs had been treated as throwaway.
tags: [journal, hoplite, mcp, review, decision]
created: 2026-05-24
aliases: []
---

# Stub-review findings remediation

Echo-style stubs for the hoplite MCP tool surface went through a real review pass at 17:33 — 21 minutes after the stubs landed at 17:12. The review surfaced shape and contract issues that would have ridden through to the real implementations untouched if the stubs had been treated as throwaway.

## The pattern

The stubs ([[docs/journal/2026-05-24-1918-first-hoplite-modules.md]]) wired every MCP tool through the FastMCP server with echo-style fakes — the tool received its arguments, the body returned a fixture matching the expected shape, every codepath the agent would exercise existed end-to-end without any real storage layer behind it. The agent integration could land before the storage layer existed.

The natural thing would have been to treat the stubs as throwaway scaffolding. Move on to the real implementations; review the real code. The pattern at 17:33 instead was: review the stubs.

## What the review surfaced

Stubs ship the tool surface — argument names, argument types, return shapes, error semantics. All of those are the contract the real implementation has to match. Issues the review caught at the stub layer:

- Argument naming. `from_` (with the trailing underscore to avoid the Python keyword) versus `start_id` versus `origin`. The stub picked one; the review surfaced that the choice would propagate. Settling it at the stub layer meant the real implementation wouldn't have to rename.
- Return-shape consistency. `Hit` vs `TraversalHit` — the structural sibling shapes that `match_nodes` and `traverse_nodes` return. The review caught fields that should have aligned between the two but had drifted in the stubs.
- Error semantics. Did calling a tool with a missing required arg raise, return an empty result, or return a structured error? The stubs had drifted across two of those answers; the review settled on raise-with-a-clear-message for required args.
- Tool description prose. The text the MCP supervisor exposes to the agent — what shows up in the agent's tool palette. The stubs had placeholder descriptions; the review pulled real prose from the spec.

The stub-review fix commit (17:33) closed all four classes in one pass.

## Decisions captured

- Stubs are not throwaway. The surface they expose is the contract. Reviewing the contract before the implementation lands prevents the implementation from inheriting contract defects.
- Review the stub the way you'd review the real code. Same lenses (shape, contract, error semantics, naming, prose). The review depth scales with what the artifact commits to, not with how much code is behind it.
- Stub-then-fill is faster than implement-then-rework. Wire the surface first, even with fakes; then build out behind it. The agent integration tests against the stubs, surfacing contract issues early. The real implementation slots into a settled contract.

## What this is a piece of

The leaves-first-trunk-second ordering ([[docs/journal/2026-05-24-1918-first-hoplite-modules.md]]) included a sub-ordering: build the leaves, stub the surface, review the surface, build the trunk. The 21-minute gap between stub and stub-review was deliberate — the review pass was scheduled into the sequence.

The pattern recurred in subsequent work. The dump-tool stubbed first, then reviewed, then implemented. The traverse-tool stubbed, reviewed, implemented. Each stub-review pass caught contract issues that would have been more expensive to fix downstream.

## Cross-references

- `[[journal/2026-05-24-1918-first-hoplite-modules]]` — the broader module work this fits inside.
- `[[journal/2026-05-24-1701-python-toolchain-and-writing-python-skill]]` — the toolchain that gated each commit including the stubs.
