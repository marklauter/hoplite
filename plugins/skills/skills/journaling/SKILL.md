---
name: journaling
description: Use when the user asks to log this, journal this, add a journal entry, record what we just did, wrap up the session in the journal, log today's work, log the outcome of an experiment, or record a decision — or when an OODA cycle closes (experiment ends, decision lands, dead-end is ruled out) and the cycle is worth preserving. Entries go under docs/journal/.
---

# Journaling

A developer journal is the durable, append-only, chronological record of an engineering project's process: what was attempted, what was learned, what was decided. The journal lives under `docs/journal/` so a future reader — the author later, a teammate, the next session — can reconstruct the design path the work moved through.

A journal entry is one cycle within the journal — one experiment, one decision, one session wrap, one dead-end ruled out, one intent-versus-outcome comparison. Each entry is dated and historically immutable: once recorded, it stays as written.

Recording an entry has four steps: observe the cycle that just closed, search for a recent entry on the same topic in the last 24 hours, compose the content, and record the entry.

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

Before recording, scan entries from the last 24 hours via `scan.sh --since <today-1>` plus title, tag, or summary predicates to locate any recent entry on the same topic.

- Same topic exists within the last 24 hours. Use `record-entry.sh --append <title>` to extend the body of the existing entry — the new content continues the same cycle.
- Different topic within the last 24 hours. Record a new entry with the default mode.
- Same topic outside the 24-hour window. Record a new entry. Today's cycle is its own entry; the older entry stays untouched and may be referenced by filename.

Topic match is a judgment call from title, tags, and summary of the recent entries. When in doubt, start a new entry.

The journal is historically immutable. If an existing entry is wrong, compose a new compensating entry that references and corrects the prior one. The original stays as-written. Other agents — those not running this skill — must never modify journal entries. They may read and scan; all writes go through `record-entry.sh`.

## Compose the entry — head and body

Three head fields carry the entry: title, tags, summary. Discipline lives in the [Entry format](#entry-format) section below.

Two body disciplines apply regardless of the entry's shape:

Intent before outcome. State the hypothesis or plan before recording the result. The temporal order matters: recording intent after the outcome is known turns every prediction into hindsight. The discipline of stating expectation, then comparing against what happened, is the loop that produces calibration.

Future self is the reader. The reader has lost the context — the same author tomorrow, a teammate, a future agent, the next session after compaction. Assume nothing about what the reader already knows. Specific names, specific paths, specific numbers, specific dates. Phrases like "the thing we discussed earlier" or "as I said" rely on context the reader does not have.

The journey is the artifact. Capture failed attempts, abandoned approaches, hypotheses that did not survive contact with reality. A journal that records only the successes has nothing useful to teach the reader reconstructing the design path.

Cross-reference notes. An entry that changes the current understanding of a topic names the note inline: `[[cache-ttl-300s]]`. An entry that produces a new topic worth its own page either creates the note then or flags the candidate: `candidate note: cache-eviction-policy`. The journal links forward to notes; notes do not link back.

## Record the entry — record-entry.sh reference

To record an entry, use `record-entry.sh`. The script generates the date and time at write time, slugifies the title, and saves `docs/journal/YYYY-MM-DD-HHMM-<slug>.md`. After saving, confirm with a minimal acknowledgment — for example, `entry saved: <filename>` — and let the file stand. No recital or recap.

`record-entry.sh` — save a new entry or append to a recent one.

Signature:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/journaling/scripts/record-entry.sh [--append] <title> [<tags> <summary>]
```

Two modes:

- (no flag) — new entry. Refuses to save if a same-minute same-slug file already exists.
- `--append` — extend the body of the latest existing entry matching the slug. Header (H1, date, tags, summary) is preserved. Pass only `<title>` to derive the slug.

There is no `--overwrite` mode. The journal is historically immutable; corrections are new compensating entries that reference and correct the prior one.

Body is read from stdin and appended verbatim. Output: success is silent — the file is the artifact. Failure prints the validation error to stderr and exits non-zero.

## Finding entries — scan.sh reference

`scan.sh` is the canonical access mechanism for finding entries — it emits the structured header fields Explore, Glob, and Grep skip.

`scan.sh` — list and filter entries by structured predicates.

Signature:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/journaling/scripts/scan.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT] [--since YYYY-MM-DD] [--until YYYY-MM-DD]
```

Each flag is optional; flags AND together. No predicates lists every entry in chronological order.

- `--title PAT` — substring match, case-insensitive, against the H1 title
- `--tag TAG` — exact match against an entry in the comma-separated `tags:` line
- `--xtag TAG` — exclude entries whose `tags:` line contains TAG
- `--summary PAT` — substring match, case-insensitive, against the one-line summary
- `--since YYYY-MM-DD` — include only entries whose date prefix is on or after this date
- `--until YYYY-MM-DD` — include only entries whose date prefix is on or before this date

Output: one header block per match — title, date, tags, summary, filename. Empty `docs/journal/` prints `no entries`; predicates that match nothing print `no entries matching <predicates>`. Exit code 0 either way — clean empty result is success.

## Entry format

Entry files live under `docs/journal/` at the repo root. The filename is `YYYY-MM-DD-HHMM-<slug>.md`. The date and time prefix gives `ls` chronological order; the slug derives from the title.

An entry has two parts:

- Header — five lines: H1 title, blank line, `date:` line, `tags:` line (comma-separated), one-line summary. Composed by `record-entry.sh` from its args plus the current date and time. The slug, date, and time are mechanically derived; renaming is not a supported operation.
- Body — everything piped on stdin. H2 sections; titles and content are yours. Context/Attempted/Outcome/Decision/Next fits experiment-style entries; session-summary, decision, and milestone entries take whatever shape fits the cycle.

Cross-references to entries use the full date-prefixed slug — `[[2026-05-20-1430-cache-investigation]]`; cross-references to notes use the note slug — `[[cache-ttl-300s]]`.

The template `record-entry.sh` produces:

```
# <one-line title — the entry topic>

date: YYYY-MM-DD HH:MM
tags: <comma-separated, optional>
<one-line summary>

## <a section title>
<content>

## <another section title>
<more content>
```

### Head field discipline

Three head fields carry the discovery load: title, tags, summary.

#### Title

Name the cycle explicitly. Concrete over abstract. The title is identity, slug, and search anchor — discriminating enough that exact-match scan returns the right entry. Title is what the cycle was, not what the entry is about.

When the user supplies a title, use it. Otherwise derive from the cycle's content and outcome.

For a question that gained an answer mid-cycle: pivot the title from interrogative to declarative within the same entry if the cycle closed cleanly; or record the answer as a new compensating entry that references the original question.

#### Tags

Tags are facets that distill the entry's content or intent. Common dimensions: status (`closed`, `wip`), area (`auth`, `cache`, `infra`), thread (`auth-investigation`, `cache-ttl-thread`), entry type (`experiment`, `decision`, `session-wrap`). No controlled vocabulary — pick from what the cycle covers.

When the user signals entry type in the request ("log the experiment", "log the decision"), the named type becomes a tag. Multi-tag membership is the norm.

Tagging an entry with another artifact's slug creates a cross-reference — `scan.sh --tag <slug>` finds every entry that cites the target.

#### Summary

One sentence. Front-load the most informative phrase. Name what the cycle produced that title and tags omit. Distinguish it from siblings sharing the same tag. Skip meta-framing ("this entry covers...").

### Body principles

Two disciplines apply regardless of body shape, restated here as the operative form:

Intent before outcome. Record the hypothesis or plan before the result, in that order. The calibration loop depends on this temporal sequence.

Specific over vague. Names, paths, numbers, dates, citations. Pronouns and "the thing earlier" rely on context the reader does not have.

### Well-formed entries

The journal earns its value from chronological integrity and recovered context. Date in the head, summary present, body distinct from summary, one cycle per entry. Fix new entries on the way in; never edit a recorded entry — compose a compensating entry instead.

Defects:

- An entry without a `date:` line in the header. Every entry declares its provenance.
- An entry without a one-line summary in the head. The summary is what the scanner reads.
- An entry whose body restates the summary verbatim. The summary is the head; the body is the cycle.
- An entry that covers two cycles. Split it — a new entry for the second cycle.
- A modification of an already-recorded entry (other than `--append` within the same cycle). The original stays; compose a compensating entry that references and corrects it.

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
