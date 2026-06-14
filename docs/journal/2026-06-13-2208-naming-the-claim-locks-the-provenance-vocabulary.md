---
title: Naming the claim locks the provenance vocabulary
summary: The feature-provenance vocabulary collapses to a five-term spine — claim, assert, infer, intrinsic, provenance — once naming the noun the model had been circling resolved the long-running declared/discovered-versus-authored/inferred friction.
tags: [journal, hoplite, affordances, glossary, decision]
created: 2026-06-13
---

# Naming the claim locks the provenance vocabulary

The feature-provenance vocabulary collapses to a five-term spine — claim, assert, infer, intrinsic, provenance — once naming the noun the model had been circling resolved the friction.

## Context

Refining the affordances doc kept snagging on a term collision: `declared`/`discovered`, the `edge_kind` values, versus `authored`/`inferred`, the feature-origin words. Both pairs named the same cut — author-supplied versus engine-supplied — but came from different docs, so the prose drifted between them. The friction was real and the resolution wasn't obvious: picking one pair over the other still left the underlying noun unnamed.

## The realization

The unlock was a noun. A video used "claim" where we had been saying "assert," and that surfaced what the model had been circling — the thing an author asserts is a *claim*: a citation, a summary, a property, a tag. "An author asserts a claim" fixed the verb and the noun at once.

From there the synonyms collapsed. `declared` and `authored` are the same act as assert. `discovered` is the same act as infer — with the carve-out that an agent *noticing* a gap is the everyday sense of discovery, valid but out of scope, because that act ends in an assertion, not an inference. `intrinsic` fell out as the odd one: a feature inherent to the document — its bytes, history, location, identity — is put forward by no one, so it is not a claim and carries no provenance. A claim is the subset of features that someone or something originates; claim ⊂ feature.

`provenance` then had a crisp, lockable definition — a claim's origin, asserted or inferred — that subsumed the older `instantiation` (explicit/implicit) framing, since named-versus-emergent tracks asserted-versus-inferred one to one.

## Decision

Five terms lock as the substrate: claim, assert, infer, intrinsic, provenance. Retired: declared and authored fold into asserted; discovered into inferred; instantiation into provenance. The glossary [[docs/hoplite/hoplite-glossary.md]] splits into Locked, Evolving, and Synonyms, the crosswalk keyed by the retired word so a stale term met in the wild still resolves. The `edge_kind` enum is renamed and seeded in the schema DDL as `asserted`/`inferred`, id order carrying the asserted-wins precedence.

## Next

The prose propagation sweep across the spec docs — affordances, authoring, navigation, graph, frontmatter, README, architecture, roadmap — still spells the retired terms; authoring's `declare`/`describe` spine needs a reframe under assert. Notes and journal stay frozen as historical record.
