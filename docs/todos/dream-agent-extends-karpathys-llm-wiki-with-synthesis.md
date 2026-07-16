---
title: Dream agent extends Karpathy's LLM wiki with synthesis
summary: Background agent samples the corpus, traverses neighborhoods, and writes branching landing notes — pushing Karpathy's lint workflow from suggestion to synthesis, with dream-authored content isolated under docs/dreams/ and a dream tag.
tags: [todo, architecture, roadmap, dream]
created: 2026-05-25
priority: low
effort: high
status: open
---

# Dream agent extends Karpathy's LLM wiki with synthesis

A background agent samples the corpus, traverses neighborhoods, and writes branching landing notes — pushing Karpathy's lint workflow from suggestion to synthesis, with dream-authored content isolated under `docs/dreams/` and a `dream` tag.

## Concept

The dream cycle picks a document at random, traverses its mentions and related neighborhood, studies the region, then writes a new branching note. The note summarizes the cluster and gives navigation hints to foreground agents. A node x with neighbors a, b, c and topically-related l, m, n gets a hub note that says "x's region covers Y; for the contract see `[[docs/notes/a.md]]`; for the decision history see `[[docs/notes/b.md]]`; for the adjacent angle see `[[docs/notes/l.md]]`."

Foreground (non-dreaming) agents traverse through these hubs to get progressive disclosure. The hubs form a multi-layer index that compresses what would otherwise require reading the whole cluster.

## Relationship to Karpathy's LLM wiki

Karpathy's [[docs/proxies/karpathy-llm-wiki.md]] proposes three workflows: ingest, query, lint. Lint identifies orphans, contradictions, stale claims, and missing cross-references. It suggests investigations for a human or follow-up session to act on.

Dream extends lint from suggestion to action. It reads the same diagnostic signal: orphan clusters, missing landing pages, related-but-uncrosslinked regions. The dream agent writes the missing scaffolding directly rather than reporting it.

This has an architectural cost. Synthesis-as-action means LLM-authored content lands in the wiki without per-write human review. Isolation rules become non-negotiable.

## Isolation rules

Dream-authored content stays separable from user-authored notes:

- Folder. Dream notes live under `docs/dreams/`. Authored notes stay under `docs/notes/`, `docs/specs/`, and so on.
- Tag. Every dream note carries `dream` in its tags list. Tag predicates (`tagged: !dream`) let foreground agents filter dreams in or out per query.
- Frontmatter provenance. Each dream note records the source paths it synthesized from and a content hash or git SHA per source. A later pass uses these to detect divergence, then re-dreams or retires the note.
- Generational cap. Dreams sample only authored notes, never other dreams. This keeps the graph from drifting into recursive LLM slop.
- Mutation boundary. The dream agent creates new notes and adds wikilinks within its own creations. User-authored notes remain immutable to it.

## Adjacent ideas

- Paper-ingest workflow ([[ghost/notes/paper-ingest-needs-reference-notes]]) closes Karpathy's ingest loop. A reference note holds the external source URL and metadata; a later agent fetches the page and writes the synthesis as a 5-paragraph essay or longer treatment.
- Lint-first stepping stone. Before letting dream write hub notes, run it report-only: emit `docs/dreams/lint-<date>.md` with proposed actions for human review. This closes Karpathy's lint cleanly. Promotion to synthesis comes after the report format stabilizes.
