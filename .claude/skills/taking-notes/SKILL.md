---
name: taking-notes
description: Capture an idea, problem, todo, or finding as a note under docs/notes/ — the mutable, current-state memory answering "where are we now?". Use whenever something worth keeping surfaces; rewrite the note freely as understanding moves.
---

# Taking notes

Capture the current state of one idea as a note under `docs/notes/` — repo memory that outlives the context window to answer, on demand, *where are we now?* A note is a **snapshot of present belief**: what you hold true today, what's left to do. Mutable by nature — rewrite it freely as understanding moves; a stale note is a prompt to update, never to version. (How you got here is the journal's job, not a note's.)

- **One note per idea.** Find the existing note and update it rather than duplicate; two ideas still get two notes.
- **State, not path.** Keep the current conclusion; the wrong turns that produced it belong in the journal. Never "we used to think X" — that's drift, cut it.
- **Reduce to the claim.** Title states the claim; summary is the smallest phrase that carries it; the body holds only what the claim needs now.
- **Overwrite freely.** Belief changed → the note changes. No changelog, no hedging about the past.

Write `docs/notes/<slug>.md` (slug = the title, kebab-case): `title`, `summary`, `tags: [note, <domain>]`, `created`, `document.status` (`evolving` while in flux, `locked` when settled). Call `refresh()` after.
