---
title: Property keys intern into vocabulary tables that feed Survey
summary: "Interning the corpus vocabulary for the Survey affordance. Node property keys intern into property_key. The edge side began as a mirror (edge_property_key) but the cycle turned — edges carry stereotypes, not key/value properties — so edge_property collapsed to an interned stereotype vocabulary plus an edge_stereotype junction. The through-line is one rule: intern the survey-find namespace (keys, stereotype labels) and walk the rest off the (keyid, value) index."
tags: [journal, hoplite, graph, schema, stereotypes, decision]
created: 2026-05-31
---

# Property keys intern into vocabulary tables that feed Survey

Going in, `node_property` and `edge_property` stored the attribute name as a repeated `key TEXT` column. Refining the apex overview ([[docs/specs/hoplite.md]]) pinned Survey as the first read affordance — retrieve the schema vocabulary, properties and stereotypes, before composing a predicate. The schema had no substrate for it: surveying the property vocabulary meant `SELECT DISTINCT key` over the widest tables in the graph.

## Decision

Intern the keys. A `property_key (id, key UNIQUE COLLATE NOCASE)` table holds the node-side vocabulary; `node_property.key TEXT` becomes `keyid INTEGER REFERENCES property_key(id)`. The edge side mirrors it exactly — `edge_property_key` and an interned `keyid` on `edge_property`. Primary keys and the reverse-lookup indexes lead with `keyid` instead of `key`; resolving a key string to its id through the vocabulary table precedes the seek.

[Inference] Two grounds, not one. Normalization: `tags` stops repeating its string on every node that carries it. Survey: the intern table *is* the corpus's property namespace made readable — an agent reads a few dozen rows to learn what predicates are composable, instead of scanning thousands. The read affordance, not just storage economy, is what earns the table.

[Inference] Separate tables per side, not one shared vocabulary. The model's symmetry is "repeats identically on both sides," and the sides are already two tables (`node_property`, `edge_property`) — so the interning tables mirror that split rather than collapse it. It also keeps the vocabularies independently surveyable: "what node properties exist?" (`tags`, `status`, `created`) is a different question from "what edge properties exist?" (chiefly `stereotype`).

## Known limit

[Observation] The key table surfaces the key *namespace*, not stereotype values. A stereotype is an `edge_property` row keyed `("stereotype", <value>)` (see [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]]), so the labels Survey also promises — `cites`, `supports`, `supersedes` — live in the `value` column, not the key. Surfacing the stereotype vocabulary is a distinct lookup (`DISTINCT value WHERE key = 'stereotype'`), unsolved by interning keys. Flagged, deferred.

## Revision (same cycle): edges carry stereotypes, not properties

[Inference] The Known limit above prompted the real question — do edges have properties at all, or only stereotypes? Under the current model an edge carries stereotypes plus the intrinsic `kind` and `confidence` columns, and nothing else. The stereotypes note had already ruled edge-level properties beyond stereotype out of scope (the `edge.tags: [important]` addressing problem). So `edge_property` as a general EAV table was speculative generality with no authoring surface, and `edge_property_key` interned a namespace of exactly one (`stereotype`) — a degenerate EAV that existed only because I mirrored `node_property`'s shape onto the edge side.

[Decision] Collapse the edge side. `edge_property` and `edge_property_key` drop, replaced by a dedicated junction: `stereotype (id, label UNIQUE COLLATE NOCASE)` interns the open-vocab labels, and `edge_stereotype (edgeid, stereotypeid)` links edges to them — a set per edge, `PRIMARY KEY (edgeid, stereotypeid)`. This resolves the Known limit: the stereotype vocabulary is now a direct read of `stereotype`, not a `DISTINCT value` scan.

[Inference] The node/edge property symmetry the model claimed — "repeats identically on both sides" — was partly false. Both sides carry description, but in different shapes: a node carries an open key/value vocabulary, an edge carries a stereotype label set. The model canon's spine claim was rewritten to "both are described; not described identically."

## Survey is find and walk over the schema

[Inference] Survey is the read graph's `match` shape turned on the schema — the same find and walk. Find reads the namespace: `property_key` on the node side, `stereotype` on the edge side, a small interned list. Walk descends a node key to its values, the distinct `value` rows under one `keyid`, served by the `(keyid, value)` reverse index. Keys are the nodes of a vocabulary graph, `key → value` the edge, the values the reachable set.

[Inference] That settles what interns and what doesn't: intern the find namespace, not the walk values. Node property values stay inline because categorical-vs-scalar resolves in the walk itself — a key reaching a handful of values is a vocabulary (`tags`, `status`), one reaching thousands of near-unique values is a scalar (a timestamp, a score) — so the schema needs no `categorical` flag. The edge side has a single description dimension and nothing beneath it, so its survey is find alone: the `stereotype` read, no walk to follow.

## Next

[Inference] All DDL, so it couples into the in-flight SQLite walker rewrite alongside the edge-kind interning that work already owes ([[docs/journal/2026-05-31-1437-edge-kinds-collapse-to-declared-discovered.md]]). The loader seeds `property_key` and `stereotype`, translates key → keyid and label → stereotypeid on insert (the `edge_kind` interning pattern), and writes `edge_stereotype` rows from parsed `edge.<stereotype>` frontmatter and `[[stereotype:path]]` wikilinks. The stereotypes note still describes the old `edge_property` storage (`(edge_id, "stereotype", <value>)`) — fold that correction into the express-only shrink it already needs. Until the walker lands against SQLite, the schema leads and the behavioral code trails.
