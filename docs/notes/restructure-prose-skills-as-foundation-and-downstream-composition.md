# Restructure prose skills as foundation and downstream composition

Tags: todo,skills,architecture,composition
Refactor writing-* skills so writing-prose is the shared foundation and downstream skills (taking-notes, journaling, writing-wiki, reviewing-wiki) compose on top of it.

## Observation

Current prose-artifact skills are split philosophy / guidance / validation within each skill, with each skill restating general editorial rules in its own words. `writing-prose`, `writing-wiki`, `taking-notes`, and `journaling` overlap on universals (positive framing, dedup, link discipline) while diverging on specifics (audience, tone, register, voice, intent). Paired writing/reviewing skills (`writing-wiki` / `reviewing-wiki`) can drift because nothing structurally couples them to a single philosophy.

## Interpretation

Abandon the per-skill philosophy/guidance/validation split in favor of foundation + downstream composition.

- `writing-prose` becomes the foundation. It states the general laws of good writing (positive framing, etc.) and declares that audience, tone, register, voice, and intent MUST be set by the downstream. It is unaware of any specific downstream.
- Foundation rules are **named and enumerable**, with RFC-style strength markers (MUST / SHOULD / MAY) so a downstream can cite the specific rule it is overriding.
- Downstream skills (`taking-notes`, `journaling`, `writing-wiki`, etc.) load the foundation first, set audience/tone/register/voice/intent for their artifact, then explicitly override or soften foundation rules where the use case demands it (e.g. journaling softens positive framing for private emotional honesty).
- Paired `writing-*` / `reviewing-*` skills both inherit from the foundation so authoring and review cannot drift apart.
- Coupling is one-way: foundation knows nothing about downstreams; exceptions live in the skill that needs them, never in the foundation.

**Knowledge, not command.** `writing-*` skills are content dumps, not action triggers. The metaphor: jacking knowledge into the agent's head, the way Neo learns kung fu — having the knowledge is a separate activity from being told to fight. Today `taking-notes` and `journaling` lean command-shaped (eager to perform when invoked, with "when to write a note" triggers fronted in the skill). The refactor should push them toward declarative knowledge: *how to write this artifact well, when the user asks for it*. Trigger conditions stay, but as a small section serving the agent's decision of whether the user's request applies — not as the spine of the skill. The spine is the editorial knowledge.

## Next

- Rewrite `writing-prose` as a foundation: enumerate the editorial laws with MUST / SHOULD / MAY markers; declare the audience/tone/register/voice/intent slots downstreams must fill.
- Add an explicit "load `writing-prose` first" instruction at the top of each downstream SKILL.md, and hint at the dependency in the frontmatter description for discovery.
- Refactor `taking-notes` and `journaling` to stop restating general writing guidance — keep only what is artifact-specific plus named overrides of foundation rules.
- Rebalance `taking-notes` and `journaling` from command-shaped to knowledge-shaped: lead with the editorial content (what the artifact is, how it reads well), demote the trigger phrases to a short "when this skill applies" section the agent consults to decide whether the user's request fits.
- Refactor `writing-wiki` and `reviewing-wiki` to share the foundation; verify philosophy no longer duplicates between the pair.
- Decide whether `reviewing-documentation` becomes a sibling foundation for review skills or just inherits directly from `writing-prose`.
