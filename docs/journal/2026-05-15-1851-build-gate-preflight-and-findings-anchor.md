---
title: Build-gate preflight and .findings anchored at the repo root
summary: Build-gate gains a preflight check that verifies the workspace at CWD before running anything; .findings/ moves out of skill-local directories to the git repo root so verdicts have a stable home regardless of where the agent invokes from.
tags: [journal, skills, build-gate, findings, milestone]
created: 2026-05-15
aliases: []
---

# Build-gate preflight and .findings anchored at the repo root

Build-gate gains a preflight check that verifies the workspace at CWD before running anything; `.findings/` moves out of skill-local directories to the git repo root so verdicts have a stable home regardless of where the agent invokes from.

## Intent

Two operational hygiene items that were friction-on-discovery rather than initial-design holes:

1. Build-gate ran without checking it was in the right workspace. An invocation from a sibling directory would still try to build, then fail confusingly somewhere downstream.
2. `.findings/` lived adjacent to the script that wrote it. Different reviewer scripts wrote to different findings directories depending on where they ran. There was no single place to look for "all findings from this review cycle."

Both fixes are small but load-bearing for the discipline they enable.

## What landed

- Build-gate preflight check for workspace at CWD. If the working directory isn't the expected workspace, the script refuses before doing any work. Fail-fast posture from the first day's build-script work extends to "fail before starting if the environment is wrong."
- `.findings/` anchored at the git repo root. The reviewer scripts now resolve the repo root (via `git rev-parse --show-toplevel`) and write findings there. Regardless of CWD, findings collect in one place.
- A `.gitignore` entry to keep the findings tree out of git.

## Decisions captured

- Preflight checks belong at the script's entry, not after the first error. The check costs microseconds; the alternative is debugging the downstream error to discover the upstream cause.
- Operational artifacts anchor to the git root, not the script. Whoever calls the script doesn't need to know where to find the output afterward — there's one canonical location, and `git rev-parse` makes finding it trivial.

## Next

A `triaging-findings` skill is the natural follow-on: once findings land in one stable place, routing them somewhere becomes worth automating.
