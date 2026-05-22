---
name: journaling
description: Use when the user asks to log this, journal this, add a journal entry, record what we just did, wrap up the session in the journal, log today's work, log the outcome of an experiment, or record a decision — or when an OODA cycle closes (experiment ends, decision lands, dead-end is ruled out) and the cycle is worth preserving. Entries go under docs/journal/.
---

# Journaling

A developer journal is the durable, append-only, chronological record of an engineering project's process: what was attempted, what was learned, what was decided. The journal lives under `docs/journal/` so a future reader — the author later, a teammate, the next session — can reconstruct the design path the work moved through.

A journal entry is one cycle within the journal — one experiment, one decision, one session wrap, one dead-end ruled out, one intent-versus-outcome comparison. Each entry is dated and historically immutable: once recorded, it stays as written.

Recording an entry has four steps: observe the cycle that just closed, search for a recent entry on the same topic in the last 24 hours, compose the content, and save the file.

## Observe the cycle — what to journal

Record an entry when:

1. The user asks. They request a journal entry; you compose one.
2. A cycle closes. An OODA loop completes a turn — experiment ended, decision landed, dead-end ruled out, intent-vs-outcome comparison ready, session wraps. You propose an entry; the user approves or denies before you compose.
3. Auto-capture mode is on. The user has asked you to auto-capture cycle closures without the approval gate; signals are the same as #2.

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

## Compose the entry — body disciplines

Intent before outcome. State the hypothesis or plan before recording the result. The temporal order matters: recording intent after the outcome is known turns every prediction into hindsight. The discipline of stating expectation, then comparing against what happened, is the loop that produces calibration.

Future self is the reader. The reader has lost the context — the same author tomorrow, a teammate, a future agent, the next session after compaction. Assume nothing about what the reader already knows. Specific names, specific paths, specific numbers, specific dates. Phrases like "the thing we discussed earlier" or "as I said" rely on context the reader does not have.

The journey is the artifact. Capture failed attempts, abandoned approaches, hypotheses that did not survive contact with reality. A journal that records only the successes has nothing useful to teach the reader reconstructing the design path.

Cross-reference notes. An entry that changes the current understanding of a topic names the note inline: `[[cache-ttl-300s]]`. An entry that produces a new topic worth its own page either creates the note then or flags the candidate: `candidate note: cache-eviction-policy`. The journal links forward to notes; notes do not link back.

## Save the file — path and template

Entries are saved at `docs/journal/<YYYY-MM-DD>-<HHMM>-<slug>.md` via the Write tool — sortable ISO date and time, then a lowercase slug of the H1 title. Use the current date and time at the write moment. Glob the target filename first; if a same-minute same-slug file exists, choose a more specific title or wait a minute. After saving, confirm with a minimal acknowledgment — for example, `entry saved: <filename>` — and let the file stand. No recital or recap.

Template:

```
# <one-line title — the entry topic>

<one-line summary>

## <a section title>
<content>

## <another section title>
<more content>
```

Body shape (H2 sections, titles and content) is yours. Context/Attempted/Outcome/Decision/Next fits experiment-style entries; session-summary, decision, and milestone entries take whatever shape fits the cycle.

The fixed line-position contract: line 1 is the H1 title, line 2 is blank, line 3 is the one-line summary, line 4 is blank, line 5 onward is the body. This positional convention is the scanner contract — `Read limit=3` pulls an entry's headline; `Grep -A 2 '^# ' docs/journal/` pulls every title-and-summary pair without parsing. The date stays in the filename, not in the body.

Cross-references to entries use the full date-prefixed slug — `[[2026-05-20-1430-cache-investigation]]`. Cross-references to notes use the note slug — `[[cache-ttl-300s]]`.

## Title and summary

Title. Name the cycle explicitly. Concrete over abstract. The title is identity, slug, and search anchor — discriminating enough that a title grep returns the right entry. Title is what the cycle was, not what the entry is about. When the user supplies a title, use it. Otherwise derive from the cycle's content and outcome. For a question that gained an answer mid-cycle: pivot the title from interrogative to declarative within the same entry if the cycle closed cleanly; or record the answer as a new compensating entry that references the original question.

Summary. One to three sentences on the line after the H1, with a blank line between. Front-load the most informative phrase. Name what the cycle produced that the title omits. Skip meta-framing ("this entry covers...").

## Well-formed entries

The journal earns its value from chronological integrity and recovered context. Date in the filename, summary present, body distinct from summary, one cycle per entry. Fix new entries on the way in; never edit a recorded entry — compose a compensating entry instead.

Defects:

- An entry without a one-line summary under the H1. Every entry opens with title then summary.
- An entry whose body restates the summary verbatim. The summary is the lede; the body is the cycle.
- An entry that covers two cycles. Split it — a new entry for the second cycle.
- A modification of an already-recorded entry (other than an in-cycle append within 24h). The original stays; compose a compensating entry that references and corrects it.

!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/editorial-principles.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`

## Rhetorical context

- Writer: contributor
- Voice: declarative, terse — first-person acceptable
- Ethos: expert
- Stance: neutral
- Audience: future self — the author later, a future agent picking up the work, or a teammate reconstructing the design path
- Subject: one OODA cycle — what was attempted, what happened, what was decided
- Genre: journal
- Tone: professional, even-keeled
- Register: Journal — observation-based, chronological, append-only, first-person acceptable
- Intent: preserve the chronological record of cycles so future readers can reconstruct intent, outcome, and the design path the work moved through
