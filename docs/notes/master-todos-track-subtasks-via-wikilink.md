---
title: Master todos track sub-tasks via wikilink
summary: A master todo that decomposes into sub-tasks needs an explicit hierarchy signal — two candidate shapes (body wikilinks or an `edge.subtask` frontmatter list) both have tradeoffs. Open question; the todo convention does not commit yet.
tags: [note, todo, hoplite, skills, open-question]
created: 2026-05-27
document:
  priority: low
  effort: medium
  status: closed
---

# Master todos track sub-tasks via wikilink

A master todo that decomposes into sub-tasks needs an explicit hierarchy signal — two candidate shapes (body wikilinks or an `edge.subtask` frontmatter list) both have tradeoffs. Open question; the todo convention does not commit yet.

## Why it matters

Some todos are atomic — one change, one place, one closure. Others are composite — a milestone that lands when its parts land. Today's convention is flat: both shapes look identical in `where({"tagged": "todo"})`. A composite todo's `document.status` is forced to lie about a partial result — `open` while sub-parts close, `closed` only after the last lands. The corpus has no way to ask "what depends on this master" or "what's the rollup status."

## Candidate shapes

**A. Wikilinks in the body.** The master's body lists each sub-task as `[[docs/notes/sub-task-slug.md]]`. The `mentions` edge materializes the relationship; `relatives({from_: master, edge_types: ["mentions"]})` walks the children. Existing graph mechanics carry the load; no schema change.

Cost: the relationship is implicit. A reader has to know that wikilinks in *this* master mean sub-task and not "see also." Not queryable as a stereotype — `where` cannot distinguish a sub-task mention from a casual cross-reference.

**B. `edge.subtask` frontmatter list.** The master carries `edge.subtask: [docs/notes/a.md, docs/notes/b.md]` in frontmatter, parallel to `edge.blocked_by`. The relationship is explicit and queryable as a stereotype.

Cost: another stereotype to teach. The frontmatter grows. Two places to author hierarchy (frontmatter for declaration, body for narrative) instead of one.

## What this question depends on

[Inference] The right answer depends on whether the corpus grows enough composite todos for the explicit-stereotype overhead to pay off. At today's scale (single-digit composites, if any), wikilinks in the body suffice and inferred-from-`mentions` walks find them. At higher composite density, the explicit stereotype earns its keep.

## Rollup-status semantics

Independent of which shape lands, a master's `document.status` needs an agreed rollup rule:

- `open` while any sub-task is `open` or `deferred`.
- `closed` when every sub-task is `closed` or `declined`.
- A master in `deferred` while sub-tasks remain `open` overrides the rollup — the parent decision dominates.

The rollup belongs in the executor (a future HQL leaf or a thin computed-property pass), not in author-time discipline. Authors set sub-task status; the master's status updates from the leaves.

## When to resolve

Open until the first composite todo lands and forces the decision. Until then the convention stays flat — a master todo is just a todo whose body happens to mention other todos.

## Resolution

Option A wins. A composite (parent) todo carries both the `todo` tag (identity as a todo) and the `epic` tag (composite shape). Children carry `todo` only. The relationship is authored as body wikilinks from the epic to each child — no new frontmatter stereotype. `where({"tagged": "todo & epic"})` lists epics; `relatives({from_: <epic>, edge_types: ["mentions"], tagged: "todo"})` walks the children.

The `edge.subtask` frontmatter shape (Option B) stays unauthored. Adding `epic` as a sibling stereotype to `todo` keeps the convention extending sideways rather than growing a new stereotype namespace prematurely.

Rollup status remains a triager judgment for now — set the epic's `document.status` to reflect the children. A computed-property pass can automate later once enough epics land to make the rule worth executing.

## See also

- [[docs/notes/add-contradicts-as-an-authored-edge-kind.md]] and [[docs/notes/add-not-related-as-a-structural-negative-edge-kind.md]] — the stereotype precedent. The `edge.<stereotype>` namespace `edge.subtask` would join.
- [[docs/notes/hoplite-predicates-are-hql-rewrites-over-typed-relations.md]] — once HQL lands, the rollup rule reads naturally as a computed relation over sub-task status.
