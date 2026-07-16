---
name: taking-notes
description: Capture an idea, problem, todo, or finding as a note under docs/notes/ — the mutable, current-state memory answering "where are we now?". Use whenever something worth keeping surfaces; rewrite the note freely as understanding moves.
---

# Taking notes

Capture the current state of one idea as a note under `docs/notes/` — repo memory that outlives the context window to answer *where are we now?* A note is a **snapshot of present belief**: what you hold true today, what's left to do. Mutable by nature — rewrite it freely as understanding moves; a stale note is a prompt to update, never to version. (How you got here is the journal's job, not a note's.)

- One note per idea. Find the existing note and update it rather than duplicate; two ideas still get two notes.
- Present belief only. Rewrite freely as belief moves — no changelog, no hedging, no "we used to think X"; the wrong turns belong in the journal. The one bar: a cut that drops a still-true claim is a deletion, not a refinement — pause and confirm before making it.
- Reduce to the claim. Title states the claim; summary is the smallest phrase that carries it; the body holds only what the claim needs now.
- Recoverable from the note alone. The reader has lost the context you hold now → name it all in full — files, functions, numbers, dates; never "the thing we discussed."
- Don't duplicate the source. What code, CLAUDE.md, or git already states → reference it, never copy it; copies drift. Cross-repo facts and user preferences → memory, not a note.
- Link what it sits beside. Wikilink the notes, terms, and sources the note turns on where the connection is durable, so it surfaces in their neighbourhood (edge/link syntax: `${CLAUDE_PLUGIN_ROOT}/references/expressing-edges.md`).

Write `docs/notes/<slug>.md` (slug = the title, kebab-case) to the frontmatter standard (`${CLAUDE_PLUGIN_ROOT}/references/frontmatter.md`): `title`, `summary`, `tags: [note, <domain>]`, `created`, `status` (`evolving` while in flux, `locked` when settled).

## Proofread

Reread the artifact before finishing. The register is engineering: the author is a software architect, the audience is software engineers and architects. Cut every tell of machine prose:

- Aphorisms. A closing line that sounds wise and says nothing → delete whole.
- Editorializing. "Importantly", "it's worth noting", "interestingly" — the reader decides what's notable; state the fact.
- Enthusiasm. "Powerful", "robust", "seamless", "comprehensive" → the measurable property, or nothing.
- Hedging. "Arguably", "perhaps", "somewhat" → commit to the claim or drop it.
- Announcing. Describing the content instead of saying it — "This note covers…", "Let's examine" → say the thing.
- One idea per sentence. A sentence you have to reread, clauses stacked past one thought → split it.
- Em dashes. More than one per paragraph → rewrite with periods.
- Empty contrast. "Not just X but Y", "X isn't about Y" → state the positive claim alone.
- Cohesion. Every paragraph advances the artifact's one claim; a stray that belongs elsewhere → move or cut.
- Consistency. Title, summary, and body make the same claim; a term means one thing throughout, and it's the glossary's meaning.

Fix what the sweep finds, then sweep the fix.
