---
title: Bash heredoc bites the bash-fragility note
summary: While composing the runtime-thesis note arguing for replacing bash on the write path, record-note.sh failed on body apostrophes through a heredoc-quoting collision. The note arguing bash needs replacing triggered the exact failure mode that motivates the replacement.
tags: [journal, bash, mcp, dead-end]
created: 2026-05-22
---

# Bash heredoc bites the bash-fragility note

While composing the runtime-thesis note arguing for replacing bash on the write path, `record-note.sh` failed on body apostrophes through a heredoc-quoting collision. The note arguing bash needs replacing triggered the exact failure mode that motivates the replacement.

## Context

The session was composing `mcp-server-as-skill-system-runtime.md`, the note that extends `[[notes/prototype-the-plugin-mcp-server-in-python]]` with the indexer architecture and the thesis that MCP is the skill-system runtime. The body carried natural English — `agent's`, `link's semantic context`, others. Apostrophes in prose.

The write path was `record-note.sh` via the Bash tool, body delivered through a `<<'EOF'` heredoc.

## What happened

The single-quoted heredoc inside the Bash tool's outer quoting layer collided. Bash reported `unexpected EOF while looking for matching '`. The note refused to write.

The script that was supposed to be the workhorse for journaling about why this script needs replacing failed on the journal entry itself.

## Workaround

Write the body to a temp file, then `cat tempfile | record-note.sh ...`. Bypasses the heredoc layer entirely. The body is bytes through stdin; no quoting interpretation.

## Interpretation

The bash write path arguing it had no apostrophe-handling problem is the kind of claim that should be verified before publication. The note arguing the path is fragile was a verification artifact. The failure was the evidence.

This is not a one-off worth a defensive comment in the script. It is a recurring class of failure the proposed architecture exists to eliminate. The runtime thesis says: write-path tools land first, they must be apostrophe-immune by construction, no shell in the loop, no heredoc layer. The bite confirmed that the priority ordering was right.

## Decisions captured

- Bash write-path tools are not robust to natural-prose payloads. Any tool that takes user-authored markdown bodies through shell layers will hit this kind of trap eventually. The defense is structural — bypass the shell.
- The MCP server's write path will use JSON over stdin. No heredoc, no quoting layer, no shell interpretation. The tool gets bytes; bytes have no syntax to collide.
- The synchronous-mechanical edges-at-write branch of the indexer architecture is the foundation everything else stands on. Without it, the corpus doesn't grow; without growth, the rest of the runtime has nothing to index.

## Cross-references

- `[[notes/prototype-the-plugin-mcp-server-in-python]]` — the original motivation. Bash write-path scripts choke on quoting edge cases.
- `[[mcp-server-as-skill-system-runtime]]` — the thesis note whose composition triggered this incident.
- `[[bash-write-path-tripped-its-own-replacement-argument]]` — the full observation note.

## Next

The runtime thesis lands as the parent note for the MCP graph runtime data-model spec the following day. See `[[journal/2026-05-23-1807-data-model-spec-and-cold-review-iteration]]`.
