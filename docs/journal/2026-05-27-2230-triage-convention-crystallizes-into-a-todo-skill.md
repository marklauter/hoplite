---
title: Triage convention crystallizes into a todo skill
summary: A list-the-open-todos request opened a triage pass that landed an ad-hoc frontmatter shape, then a verification pass that exposed three already-resolved items and one closure that was wrong. The corrections crystallized into a real convention — `document.priority`, `document.effort`, `document.status`, immutable `todo` tag — and a new skill at `plugins/hoplite/skills/todo/` that codifies it.
tags: [journal, hoplite, skills, todo, milestone]
created: 2026-05-27
---

# Triage convention crystallizes into a todo skill

A list-the-open-todos request opened a triage pass that landed an ad-hoc frontmatter shape, then a verification pass that exposed three already-resolved items and one closure that was wrong. The corrections crystallized into a real convention — `document.priority`, `document.effort`, `document.status`, immutable `todo` tag — and a new skill at `plugins/hoplite/skills/todo/` that codifies it.

## Context

Session opened authoring one note — the SQLite reify proposal at [[docs/notes/reify-in-memory-graph-as-file-based-sqlite.md]] — then a request for the list of open todos. Fifteen notes tagged `todo`. No triage signal: priority unknowable, effort unknowable, dependencies implicit. A backlog, but shapeless.

## Attempted

Triaged the fifteen plus four more discovered by scan — notes that read as action items but lacked the tag. First convention was ad hoc: `priority`, `effort` as plain frontmatter keys, `"edge:blocked_by"` as a quoted YAML key for dependencies, `resolved` tag for closures.

Then a verification pass on the four items called low effort. Read the actual code rather than the notes' self-descriptions. Three turned up resolved or near-resolved: the wikilink anchor/alias fix landed at `plugins/hoplite/mcp/src/hoplite/graph.py:143`; four of the seven mcp-reference refinements were live in `plugins/hoplite/components/hoplite/mcp-reference.md`; the FastMCP slots workaround sat at `plugins/hoplite/mcp/src/hoplite/models.py:76-77`. The fourth — bootstrap cold-start tests — confirmed open and accurate.

Closed the three. One closure was wrong: four of seven gaps in mcp-reference is four, not seven. Reopened.

## Decision

Two refinements converted ad hoc into convention.

Edge stereotypes use `edge.<relation>:` — dot, unquoted. Parallels `edge.contradicts` and `edge.not-related` already living in the stereotype notes. The colon-separated quoted form was a YAML escape the dot form does not need.

Document state lives in three properties: `document.priority`, `document.effort`, `document.status`. Values: `high | medium | low` for priority and effort; `open | closed | deferred | declined` for status. The `todo` tag turns immutable — UML-stereotype-style label that answers "is this a todo at all," nothing more. State (closing, deferring, declining) updates the property, not the tag set. The `resolved` tag retires; conflating identity and state in the tag axis was the wrong shape.

The principle generalizes beyond todos: tags classify, properties carry state. Tags answer "what is this document?" and stay stable across the lifecycle. Properties answer "what state is this in?" and change as the work progresses. The frontmatter component now records this distinction under "Tags classify; properties carry state" so the next stereotype skill avoids the same trap.

## Outcome

Twenty-two frontmatters carry the new shape: the original nineteen triaged this session plus the new master/subtask open-question note plus the reopened mcp-reference plus the closed wikilink-resolver. `resolved` tag count across the corpus: zero.

The new skill at `plugins/hoplite/skills/todo/SKILL.md` lands in the journaling shape — declarative, ambient-reference, four cat injections, around seventy lines. Sits beside [taking-notes](../../plugins/hoplite/skills/taking-notes/SKILL.md) (which authors notes that might be tagged `todo`) as the lifecycle manager for those todos.

The master-todo / sub-task hierarchy question lives at [[docs/notes/master-todos-track-subtasks-via-wikilink.md]] with status `open`, low priority. Two candidate shapes documented (body wikilinks versus `edge.subtask` frontmatter list). Convention stays uncommitted until a real composite todo forces the choice.

## Next

Three notes landed concurrently during the session — the user's parallel work on the stereotype model and cross-repo scaling story. Each carries `todo` but no triage fields, so each needs a pass under the new convention:

- [[docs/notes/hoplite-scales-to-the-cross-repo-knowledge-graph.md]]
- [[docs/notes/ship-the-stereotype-edge-annotation-layer.md]]
- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]]

After triage, the convention's first real test is a status transition — a `deferred` item that comes back to `open`, or a `declined` that survives unchanged. The lifecycle becomes fully visible after one of each.
