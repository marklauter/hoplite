---
title: Dream agent extends Karpathy's LLM wiki with synthesis
summary: Background agent samples the corpus, traverses neighborhoods, and writes branching landing notes — pushing Karpathy's lint workflow from suggestion to synthesis, with dream-authored content isolated under docs/dreams/ and a dream tag.
tags: [note, architecture, roadmap, hoplite, dream]
created: 2026-05-25
aliases: []
---

## Concept

The dream cycle: pick a document at random, traverse its mentions and related neighborhood, study the region, then write a new branching note that summarizes the cluster and exposes navigation hints to foreground agents. A node x with neighbors a, b, c and topically-related l, m, n gets a hub note that says "x's region covers Y; for the contract see [[ghost/notes/a]]; for the decision history see [[ghost/notes/b]]; for the adjacent angle see [[ghost/notes/l]]."

Foreground (non-dreaming) agents traverse through these hubs to get progressive disclosure — a multi-layer index that compresses what would otherwise demand reading the whole cluster.

## Relationship to Karpathy's LLM wiki

Karpathy's [[ghost/notes/karpathy-llm-wiki]] proposes three workflows: ingest, query, lint. Lint identifies orphans, contradictions, stale claims, and missing cross-references — and *suggests* investigations for a human or follow-up session to act on.

Dream extends lint from suggestion to action. Same diagnostic signal — orphan clusters, missing landing pages, related-but-uncrosslinked regions — and the dream agent writes the missing scaffolding directly rather than reporting it.

The architectural cost: synthesis-as-action means LLM-authored content lands in the wiki absent per-write human review. Isolation rules become non-negotiable.

## Isolation rules

Dream-authored content stays separable from user-authored notes:

- Folder — dream notes live under `docs/dreams/`. Authored notes stay under `docs/notes/`, `docs/hoplite/`, and so on.
- Tag — every dream note carries `dream` in its tags list. Tag predicates (`tagged: !dream`) let foreground agents filter dreams in or out per query.
- Frontmatter provenance — each dream note records the source paths it synthesized from and a content hash or git SHA per source, so a later pass detects divergence and re-dreams or retires.
- Generational cap — dreams sample only authored notes, never other dreams; keeps the graph from drifting into recursive LLM slop.
- Mutation boundary — the dream agent creates new notes and adds wikilinks within its own creations; user-authored notes remain immutable to it.

## Adjacent ideas

- Paper-ingest workflow ([[ghost/notes/paper-ingest-needs-reference-notes]]) — closes Karpathy's ingest loop. A reference note holds the external source URL and metadata; a later agent fetches the page and writes the synthesis as a 5-paragraph essay or longer treatment.
- Lint-first stepping stone — before letting dream write hub notes, run it report-only: emit `docs/dreams/lint-<date>.md` with proposed actions for human review. Closes Karpathy's lint cleanly; promotion to synthesis comes after the report format stabilizes.
