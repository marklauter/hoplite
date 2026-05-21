---
name: writing-prose
description: Use when writing, refactoring, or composing prose for markdown-based artifacts. Covers editorial guidance for rhetorical context, density, structure, and formatting.
---

# Writing prose

Editorial, rhetorical context, and structural rules for composition — the authoring virtues that apply across all markdown-based artifacts.

## Rhetorical context and register

Composing an artifact rests on its rhetorical context — the writer, voice, ethos, stance, audience, subject, genre, tone, register, and intent the artifact carries. Register is one of those dimensions and also a bundled shorthand for voice and tone choices; genre, intent, and audience together usually fix it. The subsections below cover the defaults from which to start, the derivation procedure, and the catalog of named registers used as shared vocabulary.

### Default rhetorical context

- Writer: the user, an engineer — presumed knowledgeable about the subject.
- Voice: declarative, terse — direct claims without hedging.
- Ethos: expert — the writer is presumed authoritative within the subject's scope.
- Stance: neutral — describes rather than advocates, except in vision and design genres where position-taking is the point.
- Audience: ask the user before composing. Common choices — technical: engineer, oncall, operator, end user, learner; business: executive, stakeholder, customer, manager; general: future self, teammate.
- Subject: ask the user before composing.
- Genre: ask the user before composing. Common choices — technical: tutorial, how-to, explanation, reference, specification, vision or design, ADR, note, journal; business: memo, proposal, report, brief, post-mortem.
- Tone: professional, even-keeled — neither warm nor cold; addresses the reader as a colleague.
- Register: authoritative-declarative-terse — direct, position-taking, no hedging.
- Intent: ask the user before composing.

### Deriving a register

1. Identify the artifact's intent (its purpose) and audience (who reads it). The register follows.
2. Verify against siblings — they should be consistent with the derived register. If they conflict, surface the discrepancy to the user: align with siblings, update them, or deviate with reason.
3. When the intent or audience is unclear, ask the user.
4. When the register cannot be determined, use the default: authoritative-declarative-terse — direct, position-taking, no hedging.

### The named registers and their tells

Each entry below is a bundled shorthand useful as a shared vocabulary.

- Tutorial — friendly, walks the reader through one task at a time, builds understanding in sequence, second person, present tense, imperative steps.
- How-to — task-oriented, assumes the reader knows what they want, terse imperative steps, no teaching framing.
- Reference — dry, dense, factual, organized for lookup rather than reading, declarative, third person where appropriate, exhaustive on the surface area it covers.
- Explanation — understanding-oriented, conceptual, expository, often comparative or historical, longer-form prose.
- Vision or design — authoritative, declarative, position-taking, terse, explicit about what is open versus settled.
- Specification — normative, contractual, RFC-style with MUST/SHOULD/MAY, exhaustive on requirements.
- ADR — declarative, present-tense, describes the current state of a system, mutable but always current, replaces prior content as the state changes.
- Note — rough, exploratory, no audience commitment, ephemeral scratch that may be rewritten or deleted freely.
- Journal — observation-based, internal-facing, chronological, dated, append-only, immutable once written, first-person acceptable, records discoveries and issues at a point in time.

!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/editorial-principles.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`
