---
name: todo
description: Capture an action item as a todo — a note tagged `todo` under docs/todos/, born triaged with priority, effort, and status. Use whenever a task, follow-up, or fix worth tracking surfaces; `triage` works the backlog afterwards.
---

# Todo

Capture one action item as a note under `docs/todos/` — repo memory that outlives the context window to answer *what should happen next?* A todo is a note tagged `todo`: the tag is immutable identity, and the lifecycle lives in three properties set at birth, so the note enters the backlog already triaged. Mutable like any note — rewrite it freely as the work's shape moves. (Working the backlog — re-prioritising, blocking, closing — is the `triage` skill's job.)

- One todo per action. Find the existing todo and update it rather than duplicate; two unrelated changes still get two todos.
- Born triaged. Set `priority` (high|medium|low), `effort` (high|medium|low), and `status: open` at capture. Judge effort from the code the todo points at, not from the note.
- Reduce to the action. Title states what should happen; summary is the smallest phrase that carries it; the body holds only what acting on it needs — the why, the where, the shape of done.
- Recoverable from the note alone. The reader has lost the context you hold now → name it all in full — files, functions, numbers, dates; never "the thing we discussed."
- Don't duplicate the source. What code, CLAUDE.md, or git already states → reference it, never copy it; copies drift.
- Blocked from birth → link it. A todo that can't start until another closes → a `blocked-by` edge property whose value is a quoted wikilink, like `blocked-by: "[[<target>]]"` (a block-style list when there are several; edge/link syntax: `${CLAUDE_PLUGIN_ROOT}/references/expressing-edges.md`).
- Link what it sits beside. Wikilink the notes, terms, and sources the todo turns on where the connection is durable, so it surfaces in their neighbourhood (same edge/link syntax).

Write `docs/todos/<slug>.md` (slug = the title, kebab-case) to the frontmatter standard (`${CLAUDE_PLUGIN_ROOT}/references/frontmatter.md`): `title`, `summary`, `tags: [todo, <domain>]`, `created`, `priority`, `effort`, `status: open`.

## Proofread

The artifact is not done until it has been proofread. Before presenting it, committing it, or ending the turn, invoke the `proofreading` skill (`hoplite-skills:proofreading` via the Skill tool) and follow its instructions on the artifact.
