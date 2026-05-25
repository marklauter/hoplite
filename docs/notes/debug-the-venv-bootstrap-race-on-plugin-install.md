---
title: Debug the venv bootstrap race on plugin install
summary: First install of the hoplite plugin leaves the MCP server unreachable until the user manually fires the bootstrap or restarts the session a second time. Investigate the actual plugin lifecycle Claude Code documents, then redesign the bootstrap to fit.
tags: [note, todo, hoplite, bootstrap, mcp, lifecycle]
created: 2026-05-25
aliases: []
---

## Problem

Every fresh install of the hoplite plugin (or any rename/reinstall that creates a new `${CLAUDE_PLUGIN_DATA}` directory) leaves the MCP server unreachable. The launcher polls for a bootstrapped venv that doesn't exist; the supervisor reports `MCP server "plugin:hoplite:hoplite" connection timed out after 30000ms`. See [[venv-bootstrap-races-mcp-supervisor-on-plugin-install]] for the symptom-and-cause writeup from this session.

The user-facing workaround during this session: manually run the SessionStart hook script with the right env vars, then `/reload-plugins`. The user just confirmed: even after a session restart, they had to "manually start the mcp." That suggests the bootstrap-via-SessionStart story isn't actually working as designed even when it does fire.

This isn't how plugins should work. A fresh `/plugin install` of a published plugin should produce a working server without the user shelling out hooks by hand.

## What we observed during this session

- Three distinct first-install failures, identical pattern each time:
  1. After the `skills → hoplite` plugin rename. Workaround: manual bootstrap + reload.
  2. After the `hoplite → armory` plugin rename. Workaround: manual bootstrap + reload.
  3. After the fresh install of `hoplite@msl.hoplite` in the new repo. Workaround: manual bootstrap + reload.
- The bootstrap hook itself works when invoked manually with `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` set — it builds the venv, pip-installs the editable hoplite package, writes the snapshot pyproject.toml. The hook isn't broken; the orchestration around when it runs is.
- The user just reported: even after a full Claude Code session restart, the MCP server was unreachable until they manually started something. So the SessionStart-fires-on-restart assumption may be wrong — or the SessionStart hook ran but didn't beat the supervisor's connection attempt.

## Investigation prompts for a fresh session

1. **Read the Claude Code plugins reference for SessionStart timing.** What guarantees, if any, does Claude Code make about SessionStart running before MCP servers are spawned? Is there an ordering contract, or do they race? If they race, the bootstrap-via-SessionStart strategy is fundamentally fragile.
2. **Check for newer plugin lifecycle hooks.** When this design landed, the documented hooks were SessionStart and PostToolUse (plus a few others). Has Claude Code added install-time, activation-time, or marketplace-add-time hooks since? Any of those would close the gap.
3. **Verify SessionStart firing.** Add stderr logging to `hooks/bootstrap-venv.py` at the very top (before any work) so a future session can confirm whether the hook actually runs on session start. Inspect Claude Code's hook logs.
4. **Measure the supervisor's connection timing.** When the MCP supervisor spawns `launch.py`, how long does it wait for the stdio handshake? The launcher polls for 60 seconds for the venv, but the supervisor may give up earlier (the symptom message says "timed out after 30000ms" — 30 seconds). If the supervisor is shorter than the launcher's polling budget, the launcher's polling is dead weight.
5. **Check `claude-plugins-official` patterns.** How does `pyright-lsp@claude-plugins-official` handle its own bootstrap (if any)? Does it ship a prebuilt binary, lean on system Python, or bootstrap on first invocation? Patterns observed in official plugins may surface the canonical approach.

## Candidate fixes — to evaluate during the next session

Pulled from the symptom note, ranked by my current read of viability:

1. **Inline bootstrap in `launch.py`.** Launcher builds the venv on cold start instead of polling. Drops SessionStart entirely. Risk: cold pip install takes 30-60s; the MCP supervisor's handshake timeout may starve the install. Need a way to signal "still loading" or to run the heavy work outside the launcher's stdio pipe. Maybe: fork, launch the bootstrap as a detached subprocess, close stdio, exit non-zero with a "rebuilding venv, retry shortly" stderr message. The supervisor's next retry hits a ready venv.
2. **Use a documented post-install hook if Claude Code provides one.** Worth checking the docs before the next session decides.
3. **Bigger launcher poll window + clear stderr.** Stopgap. Keep SessionStart, extend polling to 180s, emit `[hoplite-launch] waiting for SessionStart hook to build venv... if this hangs, see <link>`. Hides the symptom but doesn't fix it.

## How to verify a fix

End-to-end test: from a fresh state, the first install of the plugin produces a working MCP server with the agent able to call `hoplite_match_nodes`, all within a single session start. No manual bootstrap. No second reload required.

Reproducible setup for testing the fix:

```bash
# Wipe state, leaving only an empty data dir for a clean cold-start
rm -rf ~/.claude/plugins/data/hoplite-msl-hoplite
rm -rf ~/.claude/plugins/cache/msl-hoplite
# In Claude Code: /plugin uninstall hoplite@msl.hoplite, then re-add the marketplace, then install
# Restart Claude Code session
# Observe whether the MCP tools register on first session start without intervention
```

Success: tools surface as `mcp__plugin_hoplite_hoplite__*` on first session start. No supervisor timeout. No user action between install and use.

## See also

- [[venv-bootstrap-races-mcp-supervisor-on-plugin-install]] — symptom-and-cause from this session.
- `plugins/hoplite/hooks/bootstrap-venv.py` — the SessionStart hook.
- `plugins/hoplite/mcp/launch.py` — the launcher that polls for the venv.
- `plugins/hoplite/hooks/hooks.json` — registers the SessionStart hook.
