---
name: writing-prose
description: Use when writing, refactoring, or composing prose for markdown-based artifacts. Covers editorial guidance for rhetorical context, density, structure, and formatting.
---

# Writing prose

Foundational editorial knowledge lives here — the authoring virtues that apply across all markdown-based artifacts. Downstream skills specify the rhetorical context for the artifact under composition — writer, voice, ethos, stance, audience, subject, genre, tone, register, intent. Downstream skills may deviate with justification.

## Rhetorical context — meta-rules for downstream skills

### Register follows intent and audience

Register emerges from the artifact's intent and audience. Downstream skills may explicitly name it; otherwise, derive it.

1. Identify the artifact's intent (its purpose) and audience (who reads it). The register follows.
2. Verify against siblings — they should be consistent with the derived register. If they aren't, something is off (yours or theirs).
3. When the intent or audience is unclear, ask the user.
4. When the register cannot be determined, use the default: authoritative-declarative-terse — direct, position-taking, no hedging.

The named registers and their tells:

- Tutorial — friendly, walks the reader through one task at a time, builds understanding in sequence, second person, present tense, imperative steps.
- How-to — task-oriented, assumes the reader knows what they want, terse imperative steps, no teaching framing.
- Reference — dry, dense, factual, organized for lookup rather than reading, declarative, third person where appropriate, exhaustive on the surface area it covers.
- Explanation — understanding-oriented, conceptual, expository, often comparative or historical, longer-form prose.
- Vision or design — authoritative, declarative, position-taking, terse, explicit about what is open versus settled.
- Specification — normative, contractual, RFC-style with MUST/SHOULD/MAY, exhaustive on requirements.
- ADR — declarative, present-tense, describes the current state of a system, mutable but always current, replaces prior content as the state changes.
- Note — rough, exploratory, no audience commitment, ephemeral scratch that may be rewritten or deleted freely.
- Journal — observation-based, internal-facing, chronological, dated, append-only, immutable once written, first-person acceptable, records discoveries and issues at a point in time.

### Lead with what the reader needs

The reader who stops after the first paragraph still leaves with the right impression.

- Open with a lede — one or two sentences naming what the document is for and what the reader gets from reading it.
- Usage before internals. Public surface before architecture. How to do it before how it works.
- Conclusions before justifications. State the position, then explain.

### Self-contained pages

Each page stands on its own.

- Include enough context that a reader who follows zero links still understands the page. The link is for the reader who wants depth.
- Link to canonical definitions for shared terms; do not restate them inline. The page that defines the term owns the definition.
- When a concept is genuinely page-specific, define it inline on its first use.

## Composition — authoring virtues and how to apply them

(TODO)

## Validation — edit your own work before handing off

(TODO)
