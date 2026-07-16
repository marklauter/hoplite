---
title: A query is a triple pattern with positions bound by chain addresses
summary: "Query sketch from the namespace-chain design session: a pattern names statement positions (subject, predicate, object) and binds some of them to chain addresses; the unbound positions are the result. (:predicate:status :object:todo) returns every subject with a status of todo. Bindings resolve by shortest-unique chain, the same rule as wikilink slugs."
tags: [note, hoplite, query, design]
created: 2026-07-03
status: evolving
---

# A query is a triple pattern with positions bound by chain addresses

Mark's sketch, recorded before it evaporates:

```
(:predicate:status :object:todo)
```

returns every `:subject` whose `status` is `todo`.

The moving parts:

- **Position names** — `subject`, `predicate`, `object` — name the three statement positions. They are query grammar, not namespaces: `predicate` names the middle *position*, which a [[docs/glossary/relationship.md|relationship]] label or a claim key may fill.
- **Bound positions filter; unbound positions are the result.** The pattern above binds predicate and object; the subject is what comes back.
- **Bindings are chain addresses** resolved shortest-unique — `status` reaches `meta:claim:status`, `todo` reaches `status:todo` — the same discipline the wikilink grammar uses for slugs (a bare slug resolves anywhere; the shortest unique path disambiguates).

Open threads: composition (several patterns, boolean structure — this is the concrete-syntax seed for the [[docs/glossary/search-expression.md|search expression]]); whether unbound positions can be named for multi-position results; how a pattern narrows a [[docs/glossary/walk.md|walk]]; and the position names themselves — `subject`, `predicate`, `object` occupy the short-form token space, so the grammar either reserves them in query context or marks positions distinctly (a key coined `predicate` would make `:predicate:status` ambiguous).

Context: the addressing model this rides on is [[docs/specs/schema.md]] (namespace chains, `meta:meta` grounding).
