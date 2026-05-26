---
name: journaling
description: Use when the user asks to log this, journal this, add a journal entry, record what we just did, wrap up the session in the journal, log today's work, log the outcome of an experiment, or record a decision — or when a cycle closes (experiment ends, decision lands, dead-end is ruled out) and the cycle is worth preserving. Entries go under docs/journal/.
---

# Journaling

A developer journal is the durable, append-only, chronological record of an engineering project's process: what was attempted, what was learned, what was decided. The journal lives under `docs/journal/` so a future reader — the author later, a teammate, the next session — can reconstruct the design path the work moved through.

A journal entry is one cycle within the journal — one experiment, one decision, one session wrap, one dead-end ruled out, one intent-versus-outcome comparison. Each entry is dated and historically immutable: once recorded, it stays as written.

The user invokes journaling explicitly; entries are never auto-captured. Recording an entry has three steps: search for a recent entry on the same topic in the last 24 hours, compose the content, and save the file.

One cycle, one entry. Stuffing two cycles into one entry destroys the chronology the journal exists to preserve. Two cycles get two entries.

Exclude from the journal:

- State-of-the-idea content — that belongs in a note (taking-notes), not the journal. The journal records change; notes record current state.
- Cross-repo facts, user profile, persistent preferences — that belongs in memory.
- Conversational ephemera with no durable cycle behind it. The journal captures cycles that produced something worth knowing: an observation, a decision, a dead end, a deferral.
- Speculation the author isn't ready to commit to. Entries are historically immutable — once recorded, the original stays as-written. Compose only what you're ready to preserve.

## Search for a recent entry — last-24h same-topic check

Before recording, Glob `docs/journal/<today>-*.md` and `docs/journal/<yesterday>-*.md` (dates from the current-date context) to locate any recent entry on the same topic. Inspect titles and summaries to judge topic match.

- Same topic exists within the last 24 hours. Extend the body of the existing entry — the new content continues the same cycle. Use the Edit tool; preserve the header.
- Different topic within the last 24 hours. Save a new entry.
- Same topic outside the 24-hour window. Save a new entry. Today's cycle is its own entry; the older entry stays untouched and may be referenced inline by filename.

Topic match is a judgment call. When in doubt, start a new entry.

The journal is historically immutable. If an existing entry is wrong, compose a new compensating entry that references and corrects the prior one. The original stays as-written. Never use Write to replace an existing journal entry — only Edit to extend the body within the same cycle.

## Tag the entry — type, domain, status

Every entry carries a `tags` array in its frontmatter. Three categories of tags compose, applied in order:

1. **Type tag — required: `journal`.** Every entry authored by this skill includes `journal` as a tag. Distinguishes from notes (`note`), references, decisions, and other artifact types that may share the corpus.
2. **Domain tags — what the cycle was about.** Pick from the existing vocabulary when possible — query the corpus (`hoplite_match_nodes({"tagged": "<slug>"})` or grep `docs/journal/*.md` frontmatter) to see what's in use. Examples in active use: `hoplite`, `mcp`, `python`, `claude-code`, `skills`, `bash`, `architecture`, `design`. Add a new domain tag only when no existing slug fits.
3. **Shape tags — optional.** Capture the cycle shape when it shapes how the entry reads: `experiment`, `decision`, `dead-end`, `session-summary`, `milestone`. Use sparingly; only when the reader benefits from the framing.

Aim for three to six tags total — enough that the entry surfaces in tag queries, few enough that each tag earns its place. Slugs are kebab-case lowercase.

## Save the file

Entries are saved at `docs/journal/<YYYY-MM-DD>-<HHMM>-<slug>.md` via the Write tool — sortable ISO date and time, then a lowercase slug of the H1 title. Use the current date and time at the write moment. Glob the target filename first; if a same-minute same-slug file exists, choose a more specific title or wait a minute. After saving, confirm with a minimal acknowledgment — for example, `entry saved: <filename>` — and let the file stand. No recital or recap.

The filename owns the date. Cross-references to entries use the full date-prefixed slug — `[[2026-05-20-1430-cache-investigation]]`. Cross-references to notes use the note slug — `[[cache-ttl-300s]]`.

## Compose the entry — journal disciplines

Intent before outcome. State the hypothesis or plan before recording the result. The temporal order matters: recording intent after the outcome is known turns every prediction into hindsight.

The journey is the artifact. Capture failed attempts, abandoned approaches, hypotheses that did not survive contact with reality. A journal that records only the successes has nothing useful to teach the reader reconstructing the design path.

Cross-reference notes. The journal links forward to notes; notes do not link back. An entry that changes the current understanding of a topic names the note inline as `[[cache-ttl-300s]]`. An entry that produces a new topic worth its own page either creates the note then or flags the candidate: `candidate note: cache-eviction-policy`.

For a question that gained an answer mid-cycle: pivot the title from interrogative to declarative within the same entry if the cycle closed cleanly; or record the answer as a new compensating entry that references the original question.

Context/Attempted/Outcome/Decision/Next fits experiment-style entries; session-summary, decision, and milestone entries take whatever shape fits the cycle.

## Shape and editorial guidance

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
- Register: Journal — observation-based, chronological, append-only, first-person acceptable
- Intent: preserve the chronological record of cycles so future readers can reconstruct intent, outcome, and the design path the work moved through
