---
title: Schema proposal — flat scoping replaces recursive namespaces
summary: "Resource identity is one structural level — (kind, key, name) — not a recursive chain. Keys collide by design (same name, same resource); values scope per key; an edge is any statement whose object is a document. One parse rule replaces the resolver: the first colon splits key from value."
tags: [note, hoplite, schema, design]
created: 2026-07-08
status: evolving
refines: "[[docs/specs/schema.md]]"
---

# Schema proposal — flat scoping replaces recursive namespaces

A proposal against [[docs/specs/schema.md]]: keep the triple store, drop the recursive namespace dictionary. The namespace chains were built to prevent name collisions, but Hoplite does not govern the vocabulary — the user owns the schema, as [[docs/todos/predicates-are-an-open-vocabulary.md]] already rules. Prevention by addressing scheme was governance smuggled in through the resolver. Let names collide; scope the one place scoping pays.

## Four kinds of data

Everything related to a document is one of four things:

- **document** — a corpus path (`docs/notes/foo.md`), presented bare. A ghost is a document whose file does not exist yet — same kind, no literal rows.
- **property** — a key (`status`, `cites`, `priority`). One flat set; licensed for the predicate position.
- **value** — a value under its key (`draft` under `status`). Interned at first assertion, shared by every subject that asserts it.
- **edge** — a statement whose object is a document. Not a stored kind: edge-ness is a fact about a statement's `dst`, decided per statement, not per key.

The fourth kind dissolves the relationship/claim split in [[docs/specs/schema.md]]. `cites` is just a property whose asserted objects happen to be documents. Predicate licensing reduces to: the predicate position holds a property.

## Identity and collision

- **Keys collide by design.** Same name, same resource: two authors asserting `priority` intern one key. When they meant the same thing, that is convergence — shared vocabulary without coordination. When they meant different things, the cost is recall noise on predicate-led queries, the remedy is compositional (`status:draft` narrowed by `tag:spec`), and the drift is visible in survey. Nothing corrupts silently. This is Neo4j's contract: property keys are global strings, and disambiguation belongs to the query author.
- **Values scope per key.** `status: draft` and `quality: draft` intern two resources that share a string. Value identity is the pair `(key, name)`. A globally interned `draft` would make walking a value reach every homonym under every key — the walkability that justifies interning would turn into noise — and per-key range scans need values clustered under their key anyway.

Identity is `(kind, key, name)` where only values carry a key. One structural level. The maximum depth the corpus ever produces — key over value — is the maximum depth the schema models.

## Addressing: one colon

Three layers, kept distinct:

- **Authored** — frontmatter says `status: draft`. The author writes `draft`, nothing else.
- **Stored** — a resource row named `draft` with a foreign key to the `status` resource. The colon never touches disk; scoping is a column, not a prefix.
- **Addressed** — `status:draft`, the pair projected into one query-layer token.

One parse rule replaces the greedy resolver: a key cannot contain a colon, so **the first colon always splits key from value**. `created:2026-06-30T21:34` and `url:https://example.com:8080/x` resolve in one step — the remainder after the first colon is the whole name. Documents present bare; the wikilink grammar keeps colons out of targets, so paths and addresses stay disjoint by construction, per [[docs/decisions/colon-separates-vocabulary-addresses-from-paths.md]].

Hierarchy rides inside a name on the slash register, never in the address structure: paths (`docs/notes/foo.md`) and nested values (`tag:programming/rust`) are single names with internal slashes. The `(key, name)` index makes a lexicographic prefix scan the descendant query — `tag:programming/…` is the subtree, the same mechanism that makes `created:2026-06…` a date range.

## What this deletes from schema.md

- The `nsid` recursion and the `meta:meta` fixed point.
- Greedy-leaf resolution and the rightward-moving split.
- The shortest-unique short-form discipline and its ambiguity warnings.
- The importer's namespace-derived predicate-licensing invariant (now: predicate is a property).
- The `[[high]]`-shadows-`priority:high` caveat — resolution is no longer a search.
- Open question 3 (canonical presentation — one form per kind remains) and open question 4 (one key, two routings — moot once edge-ness is per-statement).

## What is unchanged

The `statement` table and its indexes, in-row `confidence` as the RDF-star annotation, the `literal` store and its `(predicateid, resourceid)` key, `resource_alias`, `fts`, first-assertion interning, walkable values, deterministic rebuild. The RDF reading holds: every position is still a resource, per [[docs/notes/every-triple-position-is-a-resource.md]] — this proposal replaces the addressing scheme over the resources, not the reversal that made them.

## Proposed resource DDL

```sql
create table resource (
  id integer primary key,
  kind text not null,        -- 'document' | 'url' | 'property' | 'value'
  keyid integer references resource(id),  -- the value's key; null for every other kind
  name text not null collate nocase
);
create unique index idx_resource_scoped on resource(kind, keyid, name) where keyid is not null;
create unique index idx_resource_flat on resource(kind, name) where keyid is null;
create index idx_resource_name on resource(name);
```

Two partial unique indexes because SQLite treats nulls as distinct in a plain unique constraint. `idx_resource_scoped` doubles as the per-key range index.

## Open questions carried forward

- Whitespace in enumerable values (`topic: property graphs`) — easier here (a value is the tail after the first colon, so a quoted-term form in the query grammar suffices) but still unruled.
- Anchors (`doc#section`) — own resource or the document's; unresolved, unchanged.
- Whether `url` stays its own kind or folds into document as the external/absolute case.
- Whether bare value short forms (`draft` without its key) survive, or every value address pays its one colon.
