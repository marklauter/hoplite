---
title: FastMCP WriteResult schema warning is cosmetic
summary: FastMCP logs a schema warning at startup about `WriteResult`'s `path` field default; functionality is unaffected and the warning is safe to defer.
tags: [note, todo, hoplite, mcp, fastmcp]
created: 2026-05-25
aliases: []
---

## Observation

At server startup, FastMCP emits a schema warning naming the `path` field default on `WriteResult`. The tool returns correctly: `structuredContent` is populated, and the `dump_index` test verifies row counts via direct SQL against the populated index.

## Interpretation

The warning concerns schema metadata, not runtime behavior — inference. Worth a follow-up to silence the warning (likely an explicit default or field annotation on `WriteResult.path`), but no functional defect blocks current work.

## Follow-up

Investigate the `WriteResult` model definition and adjust the `path` field so FastMCP's schema generator accepts it without warning. Verify against the `dump_index` test path.
