---
title: Docs link the schema, never repeat it
summary: Documentation references driftable content by file, never reproduces it. The architecture spec had pasted the schema DDL inline and drifted to describe a renamed table; both DDL blocks now link schema.sql, whose comments carry the rationale.
tags: [journal, hoplite, documentation, schema, decision]
created: 2026-05-29
---

# Docs link the schema, never repeat it

The first rule of documenting driftable content is to point at it, not copy it. The architecture spec proved the cost of breaking that rule.

## Observation

[Observation] [[docs/specs/hoplite-architecture.md]] had drifted to describe a `document` table the schema renamed to `node`, with `path` where the schema now has `uri`. The cause was structural, not neglect: the spec pasted the DDL inline, so it held a second copy of the schema that silently fell out of sync with the source.

## Decision

[Decision] Documentation references driftable content by file link, never reproduces it. Replaced both inline DDL blocks in the spec — the dump schema and the FTS table — with a markdown link to [`schema.sql`](../../plugins/hoplite/mcp/src/hoplite/schema.sql), the single source of truth. Its own comments now carry the per-table and per-index rationale, so the explanation sits next to the thing it explains and the two cannot drift apart.

## Deferral

[Deferral] The spec's deeper staleness — the in-memory framing, the `where`/`relatives`/`export`-as-debug tool model, `document`/`path` vocabulary in prose — is a separate rewrite, held until the store and tools layers exist. Rewriting the conceptual model now would document a design that does not exist yet, which is the same drift trap one level up.
