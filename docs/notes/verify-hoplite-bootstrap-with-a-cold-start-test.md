---
title: Verify hoplite bootstrap with a cold-start test
summary: Three-scenario verification for the SessionStart venv bootstrap — cold cache, manifest drift, install failure. The failure-recovery scenario exposes a known bug where a failed pip install leaves a usable-looking venv that crashes on import.
tags: [hoplite, todo, mcp, verification]
created: 2026-05-25
aliases: []
---

The SessionStart hook builds a Python venv at `${CLAUDE_PLUGIN_DATA}/venv` on first install and on `pyproject.toml` drift. Three paths need end-to-end runs to confirm the design holds: cold cache, manifest drift, install failure.

## Cold cache happy path

Wipe the persistent data directory:

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\plugins\data\skills"
```

Start a fresh Claude Code session in this repo. Watch stderr for the bootstrap timeline:

- `[hoplite-bootstrap] creating venv at ...`
- `[hoplite-bootstrap] installing hoplite + deps via pip (editable)`
- `[hoplite-bootstrap] bootstrap complete`

Inventory `~/.claude/plugins/data/skills/` and confirm both `venv/` and `pyproject.toml` exist. Call a hoplite MCP tool to confirm the server speaks.

This is the regression the whole design exists to fix. Run it first.

## Manifest drift

Touch `plugins/armory/mcp/pyproject.toml` — bump the version field, change a whitespace, any byte-level change. Restart. The hook rebuilds the venv. Revert.

## Install failure — exposes the known bug

Add `nonexistent-pkg-xyz-12345` to `pyproject.toml`'s `dependencies` list. Restart.

Current behavior (bug present): the bootstrap logs the pip failure and unlinks the snapshot, but the freshly-created venv survives. `launch.py` finds the empty venv interpreter, runs `python -m hoplite.server`, and the server crashes on `import yaml` — the original symptom returns with extra latency.

Behavior after the fix lands: the bootstrap also runs `shutil.rmtree(venv)` on pip failure. `launch.py` polls for 60s, finds no interpreter, and emits its missing-venv error pointing at the `[hoplite-bootstrap]` lines.

Revert the bogus dep, restart, confirm clean rebuild.

## The bug this scenario surfaces

`plugins/armory/hooks/bootstrap-venv.py:62-76` — when `pip install` fails, the snapshot is unlinked but the venv directory survives. Fix: add `shutil.rmtree(venv, ignore_errors=True)` after the `_log("pip install failed")` line, before `return rc`. Run the install-failure scenario once the fix lands.
