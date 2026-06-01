---
title: Property keys intern into vocabulary tables that feed Survey
summary: Node and edge property keys now intern into dedicated tables — property_key and edge_property_key — rather than repeating their strings on every property row. The grounds are double: normalization, and a readable substrate for the Survey read affordance. Kept separate per side to preserve node/edge symmetry and keep the two vocabularies independently surveyable.
document:
  tags: [journal, hoplite, graph, schema, decision]
  created: 2026-05-31
---

# Property keys intern into vocabulary tables that feed Survey

Going in, `node_property` and `edge_property` stored the attribute name as a repeated `key TEXT` column. Refining the apex overview ([[docs/hoplite/hoplite.md]]) pinned Survey as the first read affordance — retrieve the schema vocabulary, properties and stereotypes, before composing a predicate. The schema had no substrate for it: surveying the property vocabulary meant `SELECT DISTINCT key` over the widest tables in the graph.

## Decision

Intern the keys. A `property_key (id, key UNIQUE COLLATE NOCASE)` table holds the node-side vocabulary; `node_property.key TEXT` becomes `keyid INTEGER REFERENCES property_key(id)`. The edge side mirrors it exactly — `edge_property_key` and an interned `keyid` on `edge_property`. Primary keys and the reverse-lookup indexes lead with `keyid` instead of `key`; resolving a key string to its id through the vocabulary table precedes the seek.

[Inference] Two grounds, not one. Normalization: `tags` stops repeating its string on every node that carries it. Survey: the intern table *is* the corpus's property namespace made readable — an agent reads a few dozen rows to learn what predicates are composable, instead of scanning thousands. The read affordance, not just storage economy, is what earns the table.

[Inference] Separate tables per side, not one shared vocabulary. The model's symmetry is "repeats identically on both sides," and the sides are already two tables (`node_property`, `edge_property`) — so the interning tables mirror that split rather than collapse it. It also keeps the vocabularies independently surveyable: "what node properties exist?" (`tags`, `status`, `created`) is a different question from "what edge properties exist?" (chiefly `stereotype`).

## Known limit

[Observation] The key table surfaces the key *namespace*, not stereotype values. A stereotype is an `edge_property` row keyed `("stereotype", <value>)` (see [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]]), so the labels Survey also promises — `cites`, `supports`, `supersedes` — live in the `value` column, not the key. Surfacing the stereotype vocabulary is a distinct lookup (`DISTINCT value WHERE key = 'stereotype'`), unsolved by interning keys. Flagged, deferred.

## Next

[Inference] This is DDL, so it couples into the in-flight SQLite walker rewrite alongside the edge-kind interning that work already owes ([[docs/journal/2026-05-31-1437-edge-kinds-collapse-to-declared-discovered.md]]). The loader must seed both key tables and translate key → keyid on insert, the same shape as seeding `edge_kind`. Until the walker lands against SQLite, the schema leads and the behavioral code trails.
