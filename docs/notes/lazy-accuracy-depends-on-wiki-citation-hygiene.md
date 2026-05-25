---
title: Lazy Accuracy depends on wiki citation hygiene
summary: Audit mode reads source files only when the wiki cites them — wikis with poor citation hygiene get incomplete Accuracy coverage.
tags: [todo, skills, reviewing, wiki, audit-mode-followup]
created: 2026-05-25
aliases: []
---

## Observation

- Decision #4 from the audit-mode interview (2026-05-16): lazy source resolution. The Accuracy lens reads source files as cited in wiki prose (`path:line` references, code samples, named identifiers).
- A wiki claim like "the default timeout is 30 seconds" with no source citation produces no source read; the reviewer cannot verify the claim.
- The eager alternative — scan the whole wiki for code refs up front and build a source-file list — was deferred as a future `--deep` flag, not implemented.

## Interpretation

- Coverage of Accuracy in audit mode = (set of source-grounded claims) ∩ (set of claims with explicit citation). Uncited claims are invisible to the reviewer.
- This is a sharp incentive to cite source in wiki prose: every uncited claim is one the reviewer cannot defend. The principle "Source code is the accuracy authority" implies citation discipline is the wiki's responsibility, not the reviewer's.
- The Structure lens already flags missing citations in Accuracy-relevant prose. The two lenses cover each other — Structure catches the missing citation, Accuracy verifies the cited ones.

## Next

- Observe in real audits how often uncited claims slip past. If frequent, add a Structure-lens signal: "Claim about behavior, signature, or default with no source citation" as a must-fix.
- If a `--deep` mode becomes warranted, implement eager source scanning. Defer until the lazy approach demonstrably misses important defects.
