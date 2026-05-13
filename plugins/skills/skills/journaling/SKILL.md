---
name: journaling
description: Use when the user asks to log this, journal this, add a journal entry, record what we just did, or wrap up the session in the journal. Produces dated, append-only entries under docs/journal/ that tell the story of how we got here — the engineering notebook to taking-notes' wiki.
---

# Journaling

Engineering-notebook-style entries — dated, append-only records of what was attempted, what happened, and what was decided. The chronological counterpart to the wiki notes; together they answer "where are we?" and "how did we get here?"

## Philosophy

Notes represent the current state of an idea; the journal tells the story of how we got there. The two skills are siblings — [[taking-notes]] is the wiki page, journaling is the engineering notebook. They cross-reference: an entry says "today we changed our understanding of X"; the note titled X carries the new state.

### Append-only; the past is fixed

The journal is the audit trail. Once an entry is written, it is not edited. Corrections, revisions, "we were wrong about that yesterday" — these are new entries that reference the old. Editing an entry erases the record of what we believed when we believed it.

### Time is the spine

Entries are ordered by time. The filename carries the date and the time-of-day; `ls` lists the journal chronologically by default. Topical structure is layered on with tags and cross-references, but the spine is time.

### The journey is the artifact

The journal captures process, not just outcomes. Failed attempts, abandoned approaches, hypotheses that did not survive contact with reality — these are journal content. The reader (future self, judge, teammate, next session) reconstructs the design space the work moved through. A journal that records only the successes is a journal that has nothing useful to teach.

### Intent before outcome

Write the hypothesis before running the experiment. Write the plan before doing the work. Then write the result. The temporal order matters — recording intent only after the outcome is known turns every prediction into hindsight. The discipline of stating what is expected, then comparing against what happened, is the loop that produces calibration.

### Datestamped provenance

Every entry knows when it was written. The date is in the filename and the head; the time-of-day disambiguates same-day entries and preserves intraday ordering. An entry without a date is uninterpretable — the reader cannot tell what the team knew at the time, what tools they had, what version of the world they were in.

### One cycle, one entry

An entry covers one OODA cycle, one experiment, one session, or one decision. The unit is whatever closes — what was attempted, what happened, what comes next. Stuffing three cycles into one entry destroys the chronology that the journal exists to preserve. Two cycles get two entries.

### Link to notes

The journal records change; the notes record state. When an entry causes a note to be created or updated, the entry links to the note by filename. The graph between journal and notes is the connective tissue — "as of `2026-05-12-1430-cache-investigation.md`, the note at `cache-ttl-300s.md` reflects the new understanding."

### Future self is the reader

The entry is written for someone who has lost the context — the same person tomorrow, a teammate, a judge, the next session after compaction. The writing assumes nothing about what the reader already knows. Specific names, specific paths, specific numbers, specific dates. Phrases like "the thing we discussed earlier" or "as I said" assume context the reader does not have.

### The entry is the artifact

Once the entry is written, the work of recording is done. The chat does not recite the entry back; the file under `docs/journal/` is the deliverable.

## Guidance

Concrete patterns for journaling against the principles above.

### Location and filename

- Entries live under `docs/journal/` at the repo root. The directory is committed to git; the revision history is a secondary log behind the journal itself.
- Filename: `YYYY-MM-DD-HHMM-<slug>.md`. The date-and-time prefix gives `ls` chronological order for free and prevents same-day collisions; the slug is the title lowercased, non-alphanumerics replaced with dashes, capped at 80 characters.
- The date, time, and slug are mechanically derived — `journal-entry.sh` generates them at write time. The writer chooses the title; the script chooses the filename.

### The entry template

```
# <one-line title — the entry topic>

Date: YYYY-MM-DD HH:MM
Tags: <comma-separated, optional>
<one-line summary>

## Context
<what state were we in coming into this — what was current, what was unknown>

## Attempted
<what was tried, including the hypothesis or intent>

## Outcome
<what happened — observable, measured, with citations>

## Decision
<what was decided based on the outcome>

## Next
<the next planned step, or `none` if the cycle closed cleanly>
```

Line 1 is the H1. Line 2 is blank. Lines 3-5 are the scannable head — date, tags, summary. Line 6 is blank, then the body sections.

The Context/Attempted/Outcome/Decision/Next shape is the default for experiment-style entries. Session-summary entries, decision entries, and milestone entries use the sections that fit — the template is a starting point. The scannable head is non-negotiable; the body shape adapts.

### When to write an entry

Entries are user-directed, not agent-autonomous. The trigger is an explicit request from the user. Watch for phrases like:

Session-bracket triggers:

- "log this"
- "journal this"
- "add a journal entry"
- "record what we just did"
- "wrap up the session in the journal"
- "log today's work"

Cycle-close triggers:

- "log the outcome of..."
- "journal what happened when we tried..."
- "record the decision to..."
- "log this experiment"

The content is whatever cycle or session the request brackets — the request points back to it. When the request is ambiguous about scope, ask once: "as one entry covering the session, or one entry per experiment?" Default to finer-grained when the answer is unclear; over-splitting is recoverable, under-splitting is not.

### When not to write an entry

- The user did not ask. Journaling, like notes, is an explicit-request artifact.
- The content belongs in a note. State-of-the-idea content goes to [[taking-notes]]; the journal records what changed, not the new state.
- The content belongs in memory. Cross-project user preferences, persistent feedback, user profile facts go through the memory system, not the journal.
- The content is a recap of what was just said in chat with no durable signal. The journal captures cycles that produced something worth knowing about — observations, decisions, dead ends, decisions to defer.

### Cross-referencing notes

- An entry that changes the current understanding of a topic names the note: `updates [[cache-ttl-300s]]`.
- An entry that produces a new topic worth its own page either creates the note then or flags the candidate: `candidate note: cache-eviction-policy`.
- A note's content does not say "as of journal entry X" — notes are stateless about their journey. The journal links to notes; the notes do not link back.

### Dedup is not the goal

Unlike notes, journal entries do not dedup. Two entries on the same topic on different days are expected — they capture two cycles, not one fact. The discipline is to make each entry capture exactly one cycle, not to consolidate cycles after the fact.

## Validation

"What is written, remains" (the lab-notebook discipline, paraphrased). Validation here is the discipline that keeps the journal honest — every entry timestamped, every entry untouched after writing, every entry traceable to a real cycle.

### The script set

Three scripts ship under `${CLAUDE_PLUGIN_ROOT}/skills/journaling/scripts/`. Portable POSIX bash; runs on Linux, macOS, and Windows (Git Bash, WSL).

- `journal-entry.sh <title> <tags> <summary>` — body piped on stdin. Generates date and time-of-day at write time, slugifies the title, writes `docs/journal/YYYY-MM-DD-HHMM-<slug>.md`. No `--force` flag: the journal is append-only and the script does not overwrite existing entries.
- `list-journal.sh [<since-date> | <tag>]` — reads the head of each `docs/journal/*.md` and emits one block per entry: title, date, tags, summary, filename. With a date argument (`YYYY-MM-DD`), lists entries on or after that date. With a tag argument, filters to entries whose `Tags:` line contains it.
- `query.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT] [--since YYYY-MM-DD] [--until YYYY-MM-DD]` — multi-predicate scan. Each flag is optional; flags AND together. Title and summary match substring case-insensitive; `--tag` matches exactly within the comma-separated `Tags:` line; `--xtag` excludes entries where the named tag is present; date flags bracket the filename's date prefix lexicographically. Output mirrors `list-journal.sh`.

### Output discipline

- `journal-entry.sh`: success is silent — the file is the artifact. Failure prints the validation error to stderr and exits non-zero.
- `list-journal.sh`: success prints the formatted entry list, or `no entries` when `docs/journal/` is empty or missing. Filters print only matches; no matches prints an explanatory line.
- `query.sh`: success prints the formatted matches in the same block format as `list-journal.sh`, or `no matches` when nothing satisfies the predicates. Exit code is 0 in both cases.

### Gate policies

When an entry is malformed, the rule is: write a new corrective entry. The original stays.

- An entry without a `Date:` line is a defect. Every entry declares its provenance.
- An entry without a one-line summary in the head is a defect. The summary is what the scanner reads.
- An entry whose body restates the summary verbatim is a defect. The summary is the head; the body is the cycle.
- An entry that covers two cycles is a defect noted by a corrective entry; the original is not edited to fix it.
- Editing a past entry after it has been written is a defect. Corrections are new entries; if the past entry is materially misleading, the corrective entry names it and explains the correction.
