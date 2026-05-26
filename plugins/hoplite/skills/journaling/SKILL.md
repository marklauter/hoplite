---
name: journaling
description: Use when the user asks to log this, journal this, add a journal entry, record what we just did, wrap up the session in the journal, log today's work, log the outcome of an experiment, or record a decision — or when a cycle closes (experiment ends, decision lands, dead-end is ruled out) and the cycle is worth preserving. Entries go under docs/journal/.
---

# Journaling

A developer journal is the durable, append-only, chronological record of an engineering project's progress — what was attempted, what was learned, what was decided.

## Why the journal matters

Code records the current state; the journal records how it got there. Notes record the current understanding of a topic; the journal records the cycle that produced that understanding — including the abandoned approaches and hypotheses that didn't survive contact with reality. Without the journal, the design path disappears and the same dead ends get walked again.

The journal is the only artifact in the corpus where intent precedes outcome. Recording the hypothesis after the result is known turns every prediction into hindsight — the journal exists to defeat that.

The journal answers the question — why is the system shaped like this?

## What an entry is

One cycle, one entry. A cycle is one experiment, one decision, one session wrap, one dead-end ruled out, one intent-versus-outcome comparison. Two cycles get two entries — collapsing them destroys the chronology the journal exists to preserve.

Entries are historically immutable. Once recorded, the original stays as written. A wrong entry is corrected by a new compensating entry that references and corrects it, not by replacing the original.

Cycle shapes: experiment, decision, session-summary, dead-end, milestone. Every entry opens with context — what was current going in, what was unknown. From there, draw the sections the cycle calls for:

- Attempted — what was tried, including the hypothesis or intent.
- Outcome — what happened.
- Decision — what was decided.
- Next — the next step, or `none` if the cycle closed cleanly.

Use the sections that fit; skip the rest. An experiment may want all four; a session-summary may want none of them.

After writing, a brief acknowledgment and short summary tell the user the entry landed.

## Naming

Filename: `docs/journal/<YYYY-MM-DD>-<HHMM>-<slug>.md`. Sortable ISO date and time, then a lowercase slug of the H1 title. The filename owns the date; the body does not repeat it. Entry cross-references use the full filename (minus the `.md`) as the slug.

## Same cycle, last 24 hours

Same topic within 24 hours is the same cycle — extend the existing entry. Past 24 hours or different topic, new entry. Topic match is a judgment call; default to new. Journal entries don't dedup the way notes do — same-topic entries on different days each capture one cycle, not one consolidated fact.

## What belongs and what doesn't

Included — cycles that produced something worth knowing:

- Observations. Something noticed worth preserving.
- Decisions. A choice made and the reasoning behind it.
- Dead ends. A path ruled out so it's not retried.
- Deferrals. Work consciously postponed, with intent to return.

Excluded:

- Cross-repo facts, user profile, persistent preferences. Memory holds those.
- Conversational ephemera with no durable cycle behind it.
- Speculation the author isn't ready to commit to. Entries are immutable once recorded — compose only what you're ready to preserve.

## Writing for future self

Future self has lost the context. Names, paths, numbers, dates appear in full; references like "the thing we discussed earlier" or "as I said" lean on context the reader doesn't carry.

## Tags

Every entry carries a `tags` array in its frontmatter. Three categories compose, applied in order:

1. Type tag — required: `journal`. Every entry authored by this skill includes `journal`. Distinguishes from notes (`note`), references, decisions, and other artifact types that may share the corpus.
2. Domain tags — what the cycle was about. Existing vocabulary in active use: `hoplite`, `mcp`, `python`, `claude-code`, `skills`, `bash`, `architecture`, `design`. Query the corpus (`hoplite_match_nodes({"tagged": "<slug>"})` or grep `docs/journal/*.md` frontmatter) to see the current set. A new domain tag is justified only when no existing slug fits.
3. Shape tags — optional. Capture the cycle shape when it shapes how the entry reads: `experiment`, `decision`, `dead-end`, `session-summary`, `milestone`. Used sparingly; only when the reader benefits from the framing.

Three to six tags total — enough that the entry surfaces in tag queries, few enough that each earns its place. Slugs are kebab-case lowercase.

!`cat ${CLAUDE_PLUGIN_ROOT}/components/shape/artifact-structure.md`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/shape/frontmatter.md`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/hoplite/mcp-reference.md`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/prose/writing-prose.md`

## Rhetorical context

- Writer: contributor
- Voice: plainspoken — direct, terse, contractions OK, first-person acceptable; no puns, no performative warmth, no influencer cadence
- Ethos: expert
- Stance: neutral
- Audience: future self — the author later, a future agent picking up the work, or a teammate reconstructing the design path
- Subject: one session — what was attempted, what happened, what was decided
- Genre: journal
- Tone: professional, even-keeled
- Register: journal — observation-based, chronological, append-only, first-person acceptable
- Intent: preserve the chronological record of cycles so future readers can reconstruct intent, outcome, and the design path the work moved through
