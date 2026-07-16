---
name: taking-notes
description: Capture the current state of one idea as a note under docs/notes/.
disable-model-invocation: true
---

# Taking notes

Capture the current state of one idea as a note under `docs/notes/` — repo memory that outlives the context window to answer *where are we now?* A note is a **snapshot of present belief**: what you hold true today, what's left to do. Mutable by nature — rewrite it freely as understanding moves; a stale note is a prompt to update, never to version. (How you got here is the journal's job, not a note's.)

- One note per idea. Find the existing note and update it rather than duplicate; two ideas still get two notes.
- State, not path. Keep the current conclusion; the wrong turns that produced it belong in the journal. Never "we used to think X" — that's drift, cut it.
- Reduce to the claim. Title states the claim; summary is the smallest phrase that carries it; the body holds only what the claim needs now.
- Recoverable from the note alone. The reader has lost the context you hold now → name it all in full — files, functions, numbers, dates; never "the thing we discussed."
- Overwrite freely. Distill, correct, refine — belief moves, the note moves; no changelog, no hedging about the past. The one bar: a cut that drops a still-true claim is a deletion, not a refinement — pause and confirm before making it.
- Don't duplicate the source. What code, CLAUDE.md, or git already states → reference it, never copy it; copies drift. Cross-repo facts and user preferences → memory, not a note.
- Link what it sits beside. Wikilink the notes, terms, and sources the note turns on where the connection is durable, so it surfaces in their neighbourhood (edge/link syntax: `${CLAUDE_PLUGIN_ROOT}/references/expressing-edges.md`).

Write `docs/notes/<slug>.md` (slug = the title, kebab-case) to the frontmatter standard (`${CLAUDE_PLUGIN_ROOT}/references/frontmatter.md`): `title`, `summary`, `tags: [note, <domain>]`, `created`, `status` (`evolving` while in flux, `locked` when settled).
