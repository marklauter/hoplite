---
title: Set up linting workflows for GitHub wiki repos
summary: The current writer/reviewer/triage loop is all editorial; there is no mechanical or structural pre-pass. CI in the wiki repo is the natural place to add it without putting npm on the dev box.
tags: [note, todo, wiki, linting, github-actions, ci]
created: 2026-05-25
aliases: []
---

## Context

The wiki workflow today: writer creates uncommitted content, reviewer reads the diff and produces findings, triage skill walks the findings, repeat. Everything is editorial — voice, structure, accuracy, coherence. Nothing catches the mechanical class: heading hierarchy, fence languages, trailing whitespace, broken link syntax, anchor targets that don't resolve. The writer suggested commit + push and let a downstream agent review the rendered site; that's a different (also valuable) capability, not a substitute for linting.

Constraint: npm on the local dev box is a non-starter (supply-chain risk). CI runners are ephemeral, so npm-based tools are acceptable there — the install never touches the workstation.

## Candidate GitHub Actions

- `DavidAnson/markdownlint-cli2-action` — markdownlint wrapped as an action. npm under the hood, but isolated to the runner.
- `super-linter/super-linter` — GitHub's meta-linter, runs in Docker, bundles markdownlint plus ~40 others. Container is the isolation boundary.
- `errata-ai/vale-action` — Vale (Go binary, no npm) for prose rules. Closest mechanical counterpart to what [[apply-mechanical-vs-judgment-split-to-reviewing-prose-line-and-copy-lens]] is pulling out of the editorial reviewers.

## Proposed layered workflow

1. **Local loop (exists):** writer ↔ editorial reviewer ↔ triage. Voice, structure, accuracy, coherence.
2. **CI lint on push:** markdownlint or vale-action. Catches the mechanical class before render.
3. **Post-render review (new skill):** an agent that fetches the rendered wiki page and reviews what a reader sees, not what the source says. Catches the integration class — links that parse but point to nonexistent pages, sidebar entries that don't resolve, images with broken relative paths, mermaid/code blocks that lint clean but render wrong, anchor links to headings the wiki engine slugified differently than expected.

The three layers don't overlap: editorial = meaning, lint = syntax, rendered review = integration. Each catches a class the others can't see.

## Open questions

- Which ruleset matches our editorial conventions without fighting them? markdownlint defaults will flag things the writing-wiki skill explicitly allows.
- GitHub wiki repos are separate repos (`<project>.wiki.git`) without Actions support directly — workflows have to live on a mirror or a sibling repo that syncs. Figure out the mechanics.
- Does the rendered-site reviewer belong as a new skill (`reviewing-rendered-wiki`?) or as a mode of `reviewing-wiki`? Different inputs (live URLs vs local diff) argues for separate.

## Next

Spike the wiki-repo-can't-host-Actions problem first — that gates everything else. If the answer is "sync to a sibling repo," the lint workflow and the rendered-review skill both get designed around that pipeline.
