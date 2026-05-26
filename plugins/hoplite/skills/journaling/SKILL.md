---
name: journaling
description: Use when the user asks to log this, journal this, add a journal entry, record what we just did, wrap up the session in the journal, log today's work, log the outcome of an experiment, or record a decision — or when a cycle closes (experiment ends, decision lands, dead-end is ruled out) and the cycle is worth preserving. Entries go under docs/journal/.
---

# Journaling

A journal is the append-only, episodic narrative of an engineering project — what was attempted, learned, decided. Notes hold the current state; the journal preserves the path so future readers see why each tradeoff was chosen. Record intent before outcome — hypotheses written after the answer is known are hindsight.

## When to write

Included:

- Observations. Something noticed worth preserving.
- Decisions. A choice made and the reasoning behind it.
- Dead ends. A path ruled out so it's not retried.
- Deferrals. Work consciously postponed, with intent to return.

Excluded:

- Cross-repo facts, user profile, persistent preferences. Memory holds those.
- Conversational ephemera with no durable cycle behind it.
- Speculation the author isn't ready to commit to.

Same topic within 24 hours is the same cycle — extend the existing entry. Past 24 hours or different topic, new entry. Topic match is a judgment call; default to new.

## What an entry is

One cycle, one entry. Two cycles require two entries.

Once written, the entry is immutable. Use compensating entries for new discoveries and correct errors in-place.

## Entry anatomy

Filename: `docs/journal/<YYYY-MM-DD>-<HHMM>-<slug>.md` — slug is the H1 title, kebab-case lowercase. The filename owns the date; the body does not repeat it. Entry cross-references use the full filename (minus the `.md`) as the slug.

Cycle shapes: experiment, decision, session-summary, dead-end, milestone. Every entry opens with context — what was current going in, what was unknown. From there, draw the sections the cycle calls for:

- Attempted — what was tried, including the hypothesis or intent.
- Outcome — what happened.
- Decision — what was decided.
- Next — the next step, or `none` if the cycle closed cleanly.

Use the sections that fit; skip the rest. Experiments may want all four; session-summaries may want none.

Every entry carries a `tags` array. Three categories, in order:

1. Type tag — required: `journal`. Distinguishes from notes (`note`), references, decisions, and other artifact types.
2. Domain tags — what the cycle was about. Query the corpus (`hoplite_match_nodes({"tagged": "<slug>"})` or grep `docs/journal/*.md` frontmatter) to see the active vocabulary. A new domain tag is justified only when no existing slug fits.
3. Shape tags — optional. Capture the cycle shape: `experiment`, `decision`, `dead-end`, `session-summary`, `milestone`. Used sparingly.

Three to six tags total — enough that the entry surfaces in tag queries, few enough that each earns its place.

!`cat ${CLAUDE_PLUGIN_ROOT}/components/shape/artifact-structure.md`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/shape/frontmatter.md`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/hoplite/mcp-reference.md`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/prose/writing-prose.md`

## Voice

Write for future self — the author later, a future agent, or a teammate reconstructing the design path. Names, paths, numbers, dates appear in full; phrases like "the thing we discussed earlier" rely on context the reader doesn't carry.

Plainspoken — direct, terse, contractions OK, first-person acceptable. Professional and even-keeled; no puns, no performative warmth, no influencer cadence.
