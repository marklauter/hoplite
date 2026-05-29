---
title: Tags classify, properties carry state
summary: A tag answers "what is this document?" — its type, classification, shape. A property answers "what state is this document in?" — fields that change as the lifecycle progresses. State-as-tag (resolved, closed, draft tags) conflates identity and state and churns the wrong axis when lifecycle moves.
document:
  tags: [note, hoplite, frontmatter, design, principle]
  created: 2026-05-27
---

# Tags classify, properties carry state

A tag answers "what is this document?" — its type, classification, shape. A property answers "what state is this document in?" — fields that change as the lifecycle progresses. State-as-tag (`resolved`, `closed`, `draft` tags) conflates identity and state and churns the wrong axis when lifecycle moves.

## The principle

[Observation] The corpus historically used the `resolved` tag to mark notes whose work landed. The note [[docs/notes/wikilink-resolver-leaves-alias-and-anchor-in-the-target.md]] carries this tag today, and the `todo` tag was dropped from it when closing.

[Inference] That pattern conflates two axes. Identity ("this is a todo") and state ("the todo is closed") get carried by the same value. Rewriting the tag set to track lifecycle erases the document's classification as it moves through state. Queries like `where({"tagged": "todo"})` then lose any note that has been closed, even though closed todos are exactly the corpus most worth surveying when reviewing completed work.

[Inference] The fix is structural. Tags carry identity; they are immutable once applied. State lives in dot-prefixed properties (`document.status`, `document.priority`, `document.effort`) that update freely as the document moves through its lifecycle.

## The taxonomy under the principle

[Observation] The `journaling` skill already names three tag categories: type (`journal`), domain (what the entry is about), shape (`experiment`, `decision`, `dead-end`). The type tag is the document's stereotype. The shape tag classifies the artifact's structure. Both are identity. Domain tags describe what the document discusses — also identity-shaped, because the topic does not change once written.

[Inference] State does not appear in any of the three tag categories. The three are all forms of immutable classification. State sits one layer down, in `document.<key>` properties added on top of whichever tag categories apply.

## Parallel to edge stereotypes

[Inference] This rule rhymes with the stereotype work in [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]]. Edge stereotypes are open-vocabulary labels stored in `edge_property` that classify what kind of `mentions` an edge is. The pattern generalizes: stereotypes classify, properties on the stereotyped artifact carry state.

- Edge layer — `Edge.kind` (closed enum) plus `edge_property` rows keyed by `"stereotype"` (open vocab). Edge confidence is a mutable property; the stereotype label is identity.
- Document layer — type / shape / domain tags (immutable identity) plus `document.<key>` properties (mutable state). The `todo` tag is identity; `document.status` is state.

[Inference] The same separation holds in both layers. Identity goes in the classifier slot (kind, stereotype, tag); state goes in the property bag.

## When this matters in practice

- A note tagged `todo` whose work landed gets `document.status: closed`. The tag stays; the property changes. `where({"tagged": "todo"})` continues to surface it; a status filter scopes the query when needed.
- A journal entry never carries lifecycle state. Journals are immutable by convention — once written, they record the past. State properties are unnecessary; the artifact is already pinned in time by the filename's date stamp.
- A decision artifact (when the corpus grows one) would carry `document.status: pending | accepted | rejected | superseded`. The `decision` tag stays; the status updates as the decision moves.
- A draft artifact does not exist as a tag. The state is `document.status: draft` on a note (or other type-tagged artifact); the type does not change when the draft turns final.

## Out of scope

[Inference] One adjacent question — whether a shared component captures the v1 state vocabulary (`document.status`, `document.priority`, `document.effort`) for reuse across the eventual todo, decision, and design-proposal artifact types — is parked. Today the convention lives inside the todo skill. If other artifact types pick up the same properties, hoisting to a shared component is a small refactor.

## See also

- `templates/components/shape/frontmatter.md` — the principle landed here as authoring guidance.
- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] — the parallel at the edge layer. Stereotypes classify; edge confidence carries state.
- [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]] — the cycle that promoted `confidence` from an `edge_property` lookup to a first-class column on `Edge`, the precedent for treating state as first-class while leaving classification labels in the property bag.
