---
title: Bash write-path tripped its own replacement argument
summary: Writing the runtime-thesis note through record-note.sh tripped the heredoc-apostrophe collision the thesis argues to replace — concrete evidence the bash-stdin write-path fragility is recurring, not theoretical.
tags: [evidence, bash, mcp, write-path, scripts]
created: 2026-05-25
aliases: []
---

## Observation

Composing the runtime-thesis note `mcp-server-as-skill-system-runtime.md` — which extends the original `prototype-the-plugin-mcp-server-in-python.md` decision with indexer architecture — the agent-side write path failed. The body contained apostrophes (`agent's`, `link's semantic context`, others). Passed to `record-note.sh` via a `<<'EOF'` heredoc through the Bash tool, the inner quoted-EOF collided with the tool's outer quoting layer and bash reported `unexpected EOF while looking for matching '`. Workaround: write body to a temp file, then `cat tempfile | record-note.sh ...`.

## Interpretation

`prototype-the-plugin-mcp-server-in-python.md` motivates Python+MCP as robust transport for write-path tools because bash scripts choke on quoting edge cases. This is one of those edge cases, biting the agent writing about how to replace it. The recursion is the evidence: the failure is not a one-off historical incident worth a defensive comment in the script — it is a recurring class of failure the proposed architecture exists to eliminate.

Priority implication: within the runtime thesis, the write-path tools land first. They must be apostrophe-immune by construction — JSON over stdin, no shell in the loop, no heredoc layer. The synchronous-mechanical-edges-at-write branch of the indexer architecture is the foundation everything else stands on; it has to be solid before read, traverse, and reindex tools become useful.

## References

(see prototype-the-plugin-mcp-server-in-python.md) — original motivation: bash write-path scripts choke on quoting edge cases.
(see mcp-server-as-skill-system-runtime.md) — the thesis note whose composition triggered this incident.
