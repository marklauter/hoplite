---
title: Refactor taking-notes to ambient-instructions model
summary: taking-notes still reads as an imperative runbook (Recording a note has four steps...) that loads as marching orders; rework it the way journaling was reworked — declarative description that loads as reference.
document:
  tags: [note, todo, skills, taking-notes, claude-code]
  created: 2026-05-26
  priority: medium
  effort: medium
  status: open
---

# Refactor taking-notes to ambient-instructions model

The `taking-notes` skill still reads as an imperative runbook ("Recording a note has four steps...") that loads as marching orders; rework it the way journaling was reworked — declarative description that loads as reference.

## Why

When `taking-notes` loads — via description-match on phrases like "write this down for later", or via explicit slash invocation — the body's imperative shape ("Recording a note has four steps: spot the trigger, search for an existing note on the topic, compose the content, and save the file") causes the agent to charge through the procedure before the user has even asked for a note. The intent is *ambient*: information ready to use, not pre-executing. Journaling has been reworked along these lines; taking-notes was left because it's less symptomatic, but the same drag exists.

## Target shape

Match the shape `plugins/hoplite/skills/journaling/SKILL.md` now uses:

- Declarative voice throughout; no "has N steps" preambles, no Glob/Edit/Write imperatives in the body.
- Sections ordered to match the agent's question flow: orient → gate (when to write) → define → specify (anatomy) → voice → close.
- Anatomy (filename, sections, tags) grouped under one header; cat injections close out anatomy without their own header.
- Trim or remove paragraphs already covered by `plugins/hoplite/components/prose/writing-prose.md` (wikilink mechanics, ghost documents, link form rules).

## Reference

- Journaling rewrite to ambient reference: commit `68091aa`.
- Journaling section reorder: commit `38e000b`.

## Scope notes

User flagged taking-notes as less urgent than journaling — the imperative drag is real but milder. Dedup-by-edit and duplicate-hygiene rules are unique to notes and likely outlive the rewrite; the cycle/immutability vocabulary that drives journaling doesn't apply here. Plan the section ordering around the notes-specific questions: is this worth a note? does a note already exist? what shape does it take?
