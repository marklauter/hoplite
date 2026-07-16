---
title: FastMCP WriteResult schema warning is cosmetic
summary: FastMCP logs a schema warning at startup about `WriteResult`'s `path` field default; functionality is unaffected and the warning is safe to defer.
tags: [todo, mcp, fastmcp]
created: 2026-05-25
priority: low
effort: low
status: open
---

# FastMCP WriteResult schema warning is cosmetic

FastMCP logs a schema warning at startup about `WriteResult`'s `path` field default; functionality is unaffected and the warning is safe to defer.

## Observation

At server startup, FastMCP emits a schema warning naming the `path` field default on `WriteResult`. The tool returns correctly: `structuredContent` is populated, and the `dump_index` test verifies row counts via direct SQL against the populated index.

## Interpretation

The warning concerns schema metadata, not runtime behavior. Worth a follow-up to silence the warning (likely an explicit default or field annotation on `WriteResult.path`), but no functional defect blocks current work.

## Follow-up

Investigate the `WriteResult` model definition and adjust the `path` field so FastMCP's schema generator accepts it without warning. Verify against the `dump_index` test path.

## Status (2026-05-27)

Likely resolved. `plugins/hoplite/mcp/src/hoplite/models.py:76-77` records the workaround: `slots=True` was removed from `WriteResult` because "FastMCP's Pydantic schema generator reads the slot member descriptor as a non-serializable default and warns at startup." The note's specific complaint — a default on `path` — does not match current code, where `path: str` carries no default. Confirm no warning fires at server startup (run with `claude --debug mcp` and inspect stderr); if clean, drop the `todo` tag and add `resolved`.
