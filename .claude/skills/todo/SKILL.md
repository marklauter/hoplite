---
name: todo
description: Triage notes tagged `todo` — assign priority, effort, and status, mark blockers, close what's done. Use to work the backlog, prioritise, or sweep for unlabelled action items.
---

# Todo

A todo is a note tagged `todo` — an action item the corpus tracks. The tag is immutable; its lifecycle lives in three properties, so history stays queryable without rewriting it. Triage sets those properties; state is a property, never a tag.

- **Untriaged todo → assign.** A `todo` note with no triage fields → set `priority` (high|medium|low), `effort` (high|medium|low), `status: open`.
- **Judge effort from the code, not the note.** Reading the file the note points at surfaces three shapes: *closure* (already done → `closed` plus a `## Resolution` naming where it landed), *fork* (two unrelated changes in one note → split into two), *revised effort* (a "localized" fix that actually needs migration or tests).
- **Blocked → link it.** Todos that must close first → a `blocked_by` edge property whose value is a quoted wikilink, like `blocked_by: "[[<target>]]"` (a block-style list when there are several; edge/link syntax: `docs/hoplite/expressing-edges.md`).
- **Done → close.** Work landed → `status: closed`, body gets `## Resolution`. Parked → `deferred`, naming what would un-park it (a blocker resolves, the scale arrives). Won't-do → `declined`, body says why.
- **Recoverable from the note alone.** A `## Resolution` or a `declined` reason → name where it landed in full — file, function, or commit — concrete enough to verify without re-walking the conversation.
- **Action-shaped but untagged → sweep.** A note that reads as an action item but lacks `todo` → tag it, then triage.
- **Epic → decompose.** A `todo` tagged `epic` → wikilink its child todos; its status rolls up: `open` while any child is `open` or `deferred`, `closed` once every child is `closed` or `declined`.

`closed`/`resolved` as tags duplicate `status` and rot — keep state in the property. Triage operates on existing notes (`taking-notes` authors them) and tracks work shape, not who or when — no deadlines, calendars, or assignment.
