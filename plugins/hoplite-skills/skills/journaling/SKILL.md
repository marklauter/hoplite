---
name: journaling
description: Record what happened as an immutable dated entry under docs/journal/.
disable-model-invocation: true
---

# Journaling

Record one event in the project's path as a dated entry under `docs/journal/` — repo memory that outlives the context window to answer *how did we get here?* An entry is an **immutable record of what happened**: what you tried, expected, and learned. It records an event, not a state, so it never goes stale and is never corrected — write it once, warts and all. (Where you are *now* is a note's job, not an entry's.)

- Event, not state. Record what happened and what you believed then, not what's true now.
- Intent before outcome. Write the hypothesis and expectation before you know the result; a hypothesis recorded after the answer is hindsight.
- One cycle, one entry. An experiment, a decision, a dead-end, a day. Immutable once written — a correction is a new entry, never an edit.
- Warts and all. Record the wrong turns; they stop the next reader retrying them.
- Recoverable from the entry alone. The reader has lost the context you held then → name it all in full — files, functions, numbers, dates; never "the thing we discussed."
- Link the path's landmarks. Wikilink the notes, entries, and terms the cycle turns on where the connection is durable, so the path stays walkable from either end (edge/link syntax: `${CLAUDE_PLUGIN_ROOT}/references/expressing-edges.md`).

Write to the [Microsoft Writing Style Guide](https://learn.microsoft.com/style-guide/welcome/) — plain and scannable; say what a thing is before how to use it.

Write `docs/journal/<YYYY-MM-DD>-<HHMM>-<slug>.md` to the frontmatter standard (`${CLAUDE_PLUGIN_ROOT}/references/frontmatter.md`): `title`, `summary`, `tags: [journal, <domain>]`, `created`. No `status` — entries don't evolve. Open with the context going in, then what you tried, expected, and learned.
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
