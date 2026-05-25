---
title: Source files as graph nodes
summary: The MCP graph runtime data model is forward-compatible with indexing source code alongside markdown notes; scanner, auto-derived labels, and edge-extraction logic change while storage layout, sidecar shape, tool API, and envelope semantics generalize without redesign.
tags: [note, hoplite, mcp, roadmap, source-code]
created: 2026-05-25
aliases: []
---

## What stays the same

Observation: the spec at `[[mcp-graph-runtime-data-model]]` keeps its structural choices markdown-agnostic.

- `corpus_root` config lets source files live anywhere — `src/`, `plugins/`, `lib/` — while the index stays under `docs/index/`.
- Sidecar shape is type-agnostic. `out_edges`, labels, summary, embedding all apply to any node regardless of source format.
- `match`, `invoke`, `read`, `traverse` work over any node type. The agent's discovery and navigation surface stays uniform.
- Folder-per-label membership and structured envelope semantics carry over directly.

## What needs to generalize

Inference: these are where the indexer and the conventions touch the markdown assumption.

- "Authored note" becomes "authored content." The H1/blank/summary/blank/body shape is markdown-only. Source files derive summary from docstring, first comment block, or filename. Body validation becomes file-type-conditional.
- Wiki-link parsing for `:mentions` is markdown-only. Code has its own reference graph — imports, definitions, references, inheritance — derivable from AST or LSP. These are real edge types in the authored-edge category since they're deterministic parses with no LLM involvement.
- `note` as the lone auto-derived label is too narrow. Becomes `note` for `docs/notes/`, `code` for source dirs, with sub-labels for language (`python`, `csharp`, `typescript`).
- `insert`, `update`, and `delete` are markdown-only. Source files get indexed but written through normal coding workflows (IDE, Claude Code's Edit tool, and so on), not the MCP write surface. The indexer scans and ingests; the developer modifies through other tools. Closer to LSP's read-mostly model.

## What gets interesting

Guess: the cross-boundary traversal is where most of the agentic value sits.

- "Show me the notes that mention this function" — traverse from a code node backward along `:references` to note nodes that wiki-link the symbol.
- "Show me the code paths the discussion in this note refers to" — traverse from a note node along `:mentions` to code nodes when the body wiki-links a symbol.
- A fourth framing-axis label (candidate name `definition`, framing prose along the lines of "you are reading the canonical source of behavior") joins the `instruction`/`reference`/`observation` trio when code lands. Code's contract for the agent is structurally different from prose contracts and benefits from its own envelope.

## Scope

Future, not day-one. Day-one corpus is markdown notes only. No spec changes needed now; the structural moves (folder-per-label, type-agnostic sidecar, structured envelope, typed edges, source-of-truth split) accommodate code natively when the indexer learns to scan source dirs.
