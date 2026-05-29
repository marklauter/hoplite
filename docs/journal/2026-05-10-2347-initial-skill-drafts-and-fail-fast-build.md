---
title: Initial skill drafts and the fail-fast build
summary: First skill drafts go in, then several editorial passes optimize them for an LLM audience, and a fail-fast build script lands so scripts surface failures instead of swallowing them.
document:
  tags: [journal, skills, bash, milestone]
  created: 2026-05-10
---

# Initial skill drafts and the fail-fast build

First skill drafts go in, then several editorial passes optimize them for an LLM audience, and a fail-fast build script lands so scripts surface failures instead of swallowing them.

## Intent

Start the repo as a Claude Code skills plugin. Author the first set of skills that capture how I want the agent to write — for me, for this codebase. Get them readable to the model on the first pass. Add a build script that fails loudly when something is wrong, because silent failure is the bash default and the default has to be inverted before anything else compounds on top.

## What landed

One drafting session followed by five tightening passes through the day:

- Draft skill — first attempt at SKILL.md shape.
- Optimize for LLM audience — rewrite for the model's reading patterns.
- Remove project-specific content — strip what only made sense in the source project the drafts borrowed from.
- Economy and positive framing pass — cut hedges, prefer positive assertions.
- Validation as signal and mechanism pass — distinguish what validation reports from what it does.
- Cohesion pass — read for paragraph-to-paragraph flow.

Then late the same night:

- Add fail-fast build script — `set -euo pipefail` discipline; any error halts the build immediately rather than letting subsequent steps run against half-built state.
- Build script reference — the SKILL.md learns the script exists and how to invoke it.

The next morning closed out with format fixes, an export-coverage pass, and a clarity sweep on the script notes.

## Decisions captured

- Skills are for an LLM audience first. Human readability is a side effect, not the design target. The rewriting passes were aimed at how the model reads, not at human polish.
- Build hygiene starts on day one. The fail-fast script is small but it sets the discipline: scripts in this repo report failure, not best-effort completion. Every later script inherits this posture.
- Editorial passes are cheap and worth doing. Six passes in one day was the right move — the cost was hours, the payoff was that downstream skill authors had a clean template to copy.

## Next

Reviewer-family skills (github-issues, code-review, doc skills) build on this base; the polish discipline established here becomes the validation rubric the later skills get measured against.
