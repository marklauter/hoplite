---
title: EAV property graph refactor — properties replace per-column metadata
summary: Schema flattens to nodes + node_properties + edges + edge_properties; member edges abolished and tags become properties on documents; the walker, the tool surface, and the skill prose all migrate to the EAV shape; FTS5 stays contentless. Single-day refactor of the graph's internal shape after the previous evening's redesign settled.
document:
  tags: [journal, hoplite, mcp, schema, eav, architecture, milestone]
  created: 2026-05-25
---

# EAV property graph refactor — properties replace per-column metadata

Schema flattens to nodes + node_properties + edges + edge_properties; member edges abolished and tags become properties on documents; the walker, the tool surface, and the skill prose all migrate to the EAV shape; FTS5 stays contentless.

## Intent

The morning's working code from the redesign had a fixed-column shape on `documents`: explicit columns for `path`, `title`, `summary`, `created`, `tags`, etc. Adding any frontmatter field meant adding a column. The corpus carries author-defined frontmatter — `status`, `priority`, `due`, anything an author wants — and a fixed-column schema can't accommodate that.

The refactor: move to an entity-attribute-value (EAV) shape. The `documents` table holds identity and immutable bookkeeping; `node_properties(node_id, key, value)` holds every frontmatter field; same shape for edges via `edge_properties`. New frontmatter fields require no schema change.

Tags came up as a parallel concern. The morning's design had tags as nodes connected to documents via `member` edges. With properties available, tags collapse to `key='tags', value=<slug>` rows on documents. The `member` edge type abolishes.

## What landed (chronological)

- 2026-05-25 06:40 — Edges: nodes table + four-column Edge. Preliminary restructure — `nodes` table joins `documents`; `Edge` becomes a four-column `(src, dst, type, edge_id)` row. Sets the stage for the EAV move.
- 2026-05-25 11:15 — Docs: EAV property graph spec — `node_properties`, `edge_properties`, contentless FTS. Spec lands first. The DDL gets fully written before the code change.
- 2026-05-25 11:35 — Hoplite: EAV property graph — schema + walker + tools. The implementation. Schema migration, walker rewrite (per-doc body load + per-property emit), tool-surface adjustments for the new query shape.
- 2026-05-25 11:37 — Hoplite skill + components: align prose with EAV refactor. The skill body and the hoplite component update to describe the new shape: tags are properties; edges are `mentions` and `related` only; the `member` edge type is gone.

## What changed schema-wise

The dump schema after the refactor:

```sql
CREATE TABLE documents (
  id          INTEGER PRIMARY KEY,
  path        TEXT NOT NULL UNIQUE,
  body        TEXT NOT NULL,
  resolved    INTEGER NOT NULL DEFAULT 1,
  minhash     BLOB
);

CREATE TABLE node_properties (
  node_id     INTEGER NOT NULL REFERENCES documents(id),
  key         TEXT NOT NULL,
  value       TEXT NOT NULL,
  PRIMARY KEY (node_id, key, value)
);

CREATE TABLE edges (
  id          INTEGER PRIMARY KEY,
  src         INTEGER NOT NULL REFERENCES documents(id),
  dst         INTEGER NOT NULL REFERENCES documents(id),
  type        TEXT NOT NULL
);

CREATE TABLE edge_properties (
  edge_id     INTEGER NOT NULL REFERENCES edges(id),
  key         TEXT NOT NULL,
  value       TEXT NOT NULL,
  PRIMARY KEY (edge_id, key, value)
);

CREATE VIRTUAL TABLE documents_fts USING fts5(
  body, summary,
  content='', tokenize='porter unicode61'
);
```

The composite primary key on `node_properties` allows multi-valued properties — `tags: [a, b, c]` becomes three rows, all with `key='tags'`, distinct values.

## What collapsed

- The `member` edge type. Previously documents linked to tag nodes via `member` edges. Now tag membership is a property query: `SELECT node_id FROM node_properties WHERE key='tags' AND value='<slug>'`. Tag nodes go away entirely; tags exist only as property values.
- The per-column-per-frontmatter-field schema. Adding `status` or `priority` or any author-defined field no longer touches the schema.
- The `Tag` dataclass as a graph node. Tags are strings that appear as property values; they don't carry identity beyond that.

Two edges remain: `mentions` (wikilinks) and `related` (MinHash). Both connect documents to documents; nothing else.

## What survived from the morning

- Paths as ids.
- All derived state in memory.
- 4-tool MCP surface.
- FTS5 over body + summary.
- MinHash signatures held in RAM.

## Decisions captured

- EAV for properties, not for everything. Identity and core bookkeeping stay in columns on `documents`; only the frontmatter-defined fields go through the EAV layer. Putting `path` and `body` through EAV would have cost more in lookup time than it saved in schema flexibility.
- Tags are properties, not edges. The `member` edge concept was an inherited assumption from the original tag-nodes-as-first-class design. Once the redesign removed envelope framing per tag, tags' only remaining role was categorical membership — which is what properties do. The edge type was extra mechanism with no extra meaning.
- Property values are strings. No native type system on values; date strings stay strings; numeric properties stay strings. The corpus has no need for typed values at this scale, and adding types would have required a discriminator column or value tables per type.
- FTS5 stays contentless. The full-text body lives on the `documents.body` column; `documents_fts` is a contentless mirror that holds tokenization without duplicating storage. Saves ~5 MB of duplicated text at 1000 docs.

## Cross-references

- `[[journal/2026-05-25-0202-dead-then-redesign-in-memory-graph-and-four-tools]]` — the predecessor redesign. EAV is a follow-on refinement to the in-memory graph shape that landed there.

## Next

The dump command had a long-latent bug: FTS5 rowid wasn't bound to `documents.id`, so dump paths resolved against the wrong rows. Fix lands later the same afternoon. See `[[journal/2026-05-25-1724-fts5-rowid-bug-and-timestamped-dumps]]`.
