---
name: todo
description: Use when triaging notes tagged `todo` — assigning priority and effort, marking blockers, closing items the corpus has caught up with, or sweeping for action items the author hasn't yet labeled. Reach for it when the user asks to triage, prioritize, work the backlog, or review what's outstanding.
---

# Todo

A todo is a note tagged `todo` — an action item the corpus is tracking. The tag is immutable; state lives in three frontmatter properties so a todo's lifecycle stays queryable without rewriting its history.

## When to triage

Included:

- A note lands with the `todo` tag and no triage fields — assign priority, effort, dependencies, status.
- A note acquires action-item shape after the fact — add `todo` to its tags and triage.
- A todo's work landed — close it. The corpus catches up with the world.
- The user asks to sweep — find notes that read as action items but lack the `todo` tag, then triage them.

Excluded:

- Authoring the note itself. `taking-notes` handles composition; this skill operates on the result.
- Tracking deadlines, calendars, or assignment. The corpus records work shape, not who or when.

## What a todo is

The `todo` tag identifies a document as an action item — UML-stereotype-style label, immutable once applied. Removing the tag erases the document's identity as a todo. State lives in three properties; the tag answers "is this a todo?", the properties answer "how urgent, how costly, what's blocking, where in the lifecycle."

## Todo anatomy

Filename: the source note's path is unchanged. Todos live wherever the underlying note lives — `docs/notes/<slug>.md` for most.

Three properties on the document:

- `document.priority` — `high` | `medium` | `low`. The triager's read of urgency.
- `document.effort` — `high` | `medium` | `low`. Implementation cost as best understood at triage time. Verification often revises it; that is expected.
- `document.status` — lifecycle:
  - `open` — work to do.
  - `closed` — done. The body carries a `## Resolution` section naming where the change landed.
  - `deferred` — parked. Re-triage when conditions change (a blocker resolves, the corpus reaches the scale that justifies the work).
  - `declined` — decided not to do. The body explains why so the decision survives.

Dependencies are edge stereotypes:

- `edge.blocked_by: [<path>, ...]` — todos that must close before this one is workable. Mirrors the `edge.<stereotype>` namespace shared with `edge.contradicts` and `edge.not-related`.

Tags: `todo` plus the underlying note's domain tags. Status is a property, not a tag — adding `closed` or `resolved` as tags duplicates `document.status` and rots.

## Epics

A todo tagged `epic` decomposes into child todos. The epic's body wikilinks each child; `mentions` edges materialize the hierarchy. `where({"tagged": "todo & epic"})` enumerates epics; `relatives({from_: <epic>, edge_types: ["mentions"], tagged: "todo"})` walks the children.

The epic's own `document.status` reflects the rollup of its children — `open` while any child stays `open` or `deferred`, `closed` once every child is `closed` or `declined`. The triager sets the rollup explicitly until a computed-property pass automates it.

## Triage as a pattern

Priority and effort are both the triager's read at triage time, and both are revisable. Effort calls earn confidence when the triager reads the code the note points at, not just the note itself.

Verification — reading the named file, function, or commit — often surfaces three shapes:

- Closure. The fix already landed; set `document.status: closed` and add a `## Resolution` section pointing at where.
- Fork. The note hides two unrelated changes; split into two notes and triage each.
- Revised effort. What the note self-described as "localized" turns out to need migration, tests, or a schema change.

Sweep mode finds action-shaped notes that lack the `todo` tag. Tag them and triage them.

!`cat ${CLAUDE_PLUGIN_ROOT}/components/shape/artifact-structure.md`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/shape/frontmatter.md`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/hoplite/mcp-reference.md`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/prose/writing-prose.md`

## Voice

Same voice as the underlying note — declarative, present-tense, terse. Reasoning lives in the body; frontmatter records the triager's call. A `## Resolution` section closes a todo by naming where the change landed — file path, function, or commit, concrete enough that a reader can verify without re-walking the conversation.
