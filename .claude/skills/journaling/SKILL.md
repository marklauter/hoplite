---
name: journaling
description: Record what happened — an experiment, decision, or dead-end — as an immutable dated entry under docs/journal/, answering "how did we get here?". Write it in the moment, warts and all; never corrected.
---

# Journaling

Record one event in the project's path as a dated entry under `docs/journal/` — repo memory that outlives the context window to answer, on demand, *how did we get here?* An entry is an **immutable record of what happened**: what you tried, expected, and learned. It records an event, not a state, so it never goes stale and is never corrected — write it once, warts and all. (Where you are *now* is a note's job, not an entry's.)

- **Event, not state.** Record what happened and what you believed then, not what's true now.
- **Intent before outcome.** Write the hypothesis and expectation before you know the result; a hypothesis recorded after the answer is hindsight, and worthless.
- **One cycle, one entry.** An experiment, a decision, a dead-end, a day. Immutable once written — a correction is a new entry, never an edit.
- **Warts and all.** The wrong turns are the value; they stop the next traveller retrying them.
- **Recoverable from the entry alone.** The reader has lost the context you held then → name it all in full — files, functions, numbers, dates; never "the thing we discussed."
- **Link the path's landmarks.** Wikilink the notes, entries, and terms the cycle turns on where the connection is durable, so the path stays walkable from either end (edge/link syntax: `docs/hoplite/expressing-edges.md`).

Write `docs/journal/<YYYY-MM-DD>-<HHMM>-<slug>.md`: `title`, `summary`, `tags: [journal, <domain>]`, `created`. Open with the context going in, then what you tried, expected, and learned.
