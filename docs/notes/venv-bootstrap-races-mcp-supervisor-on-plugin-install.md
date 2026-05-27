---
title: Venv bootstrap races MCP supervisor on plugin install
summary: SessionStart hooks don't fire on /plugin install. The MCP launcher polls for the bootstrapped venv and times out before the venv can be built — first install of any hoplite-shaped plugin fails until a session restart or manual bootstrap.
tags: [note, todo, hoplite, bootstrap, mcp, lifecycle, bug]
created: 2026-05-25
aliases: []
priority: medium
effort: medium
---

# Venv bootstrap races MCP supervisor on plugin install

SessionStart hooks don't fire on `/plugin install`. The MCP launcher polls for the bootstrapped venv and times out before the venv can be built — first install of any hoplite-shaped plugin fails until a session restart or manual bootstrap.

## Symptom

After `/plugin install hoplite@msl.hoplite` (or any rename or reinstall flow that produces a fresh `${CLAUDE_PLUGIN_DATA}` directory), the MCP supervisor reports `Failed to reconnect to plugin:hoplite:catalog: MCP server connection timed out after 30000ms`. The data directory at `~/.claude/plugins/data/hoplite-msl-hoplite/` exists but is empty — no `venv/`, no `pyproject.toml` snapshot.

`/reload-plugins` doesn't help; the supervisor reattempts the launcher and times out again on the same gap.

## Cause

[Observation] The venv is built by `hooks/bootstrap-venv.py`, registered as a SessionStart hook in `hooks.json`. SessionStart fires on Claude Code session start — not on `/plugin install`. The install sequence:

1. Cache populates at `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`.
2. `installed_plugins.json` records the install.
3. The MCP supervisor immediately spawns the launcher via the `mcpServers.command` entry in `plugin.json` (`python3 ${CLAUDE_PLUGIN_ROOT}/mcp/launch.py`).
4. `launch.py` polls `${CLAUDE_PLUGIN_DATA}/venv/Scripts/python.exe` (or `.../bin/python` on POSIX) for up to 60 seconds.
5. No venv exists. The launcher times out and exits non-zero.
6. Supervisor reports the connection timeout.

[Observation] The venv only builds on the next session start, when SessionStart finally fires. Meanwhile the user sees a broken plugin and has no obvious next step.

[Observation] Hit at least three times during the rename storm this session: skills → hoplite, hoplite → armory, and the fresh install of `hoplite@msl.hoplite` in the new repo.

## Workaround

Manually fire the bootstrap with the same environment Claude Code would set:

```bash
CLAUDE_PLUGIN_ROOT=~/.claude/plugins/cache/<marketplace-dot-to-dash>/<plugin>/<version> \
CLAUDE_PLUGIN_DATA=~/.claude/plugins/data/<plugin>-<marketplace-dot-to-dash> \
python3 ~/.claude/plugins/cache/<marketplace-dot-to-dash>/<plugin>/<version>/hooks/bootstrap-venv.py
```

Then `/reload-plugins` to make the supervisor re-attempt the launcher. The venv now exists; the launcher finds the interpreter and spawns the server.

Alternative: restart Claude Code entirely. SessionStart fires on startup, builds the venv, server comes up clean.

## Design candidates

Three approaches that close the gap without an upstream change in Claude Code:

1. **Inline bootstrap in `launch.py`.** When the venv interpreter is missing, the launcher builds the venv itself instead of polling and failing. Drops the SessionStart hook entirely. [Inference] Risk: the MCP supervisor expects an MCP handshake within its timeout window; a cold-start pip install takes 30-60s and would starve the handshake. Would need a way to signal "still loading" to the supervisor, or to background the install and have the supervisor retry.

2. **Pre-build at install time.** If Claude Code's plugin lifecycle exposes a post-install hook (separate from SessionStart), wire the bootstrap there. [Guess] As of today, no such hook documented in the plugins reference. Worth checking the docs again after any Claude Code update.

3. **Bigger launcher poll window + clear stderr.** Keep SessionStart, extend `launch.py`'s poll from 60s to (say) 180s, emit a stderr line explaining "first install waits for SessionStart on next session restart." Doesn't fix the underlying race but makes the symptom less mysterious.

[Inference] Option 1 is the most user-friendly if the supervisor-starvation problem is solvable. Option 3 is the cheapest stopgap.

## Day-one mitigation

Update the README troubleshooting section to call this out explicitly: "after first install of the plugin, restart Claude Code (full session restart, not `/reload-plugins`) so the SessionStart hook builds the venv." Defer the real fix until the symptom recurs in a context where it's harder to work around.

## Next

- Add a troubleshooting paragraph to `README.md` documenting the first-install dance.
- Investigate whether the Claude Code plugins reference has added a post-install hook since last check.
- If option 1 (inline bootstrap in launch.py) becomes viable, prototype it and measure the supervisor handshake timing under a cold pip install.
