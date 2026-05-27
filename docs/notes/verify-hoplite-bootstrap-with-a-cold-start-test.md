---
title: Verify hoplite bootstrap with a cold-start test
summary: Three regression scenarios for the SessionStart venv bootstrap — cold cache, manifest drift, pip-install failure. Each exercises one branch of the bootstrap design; together they pin the contract.
tags: [note, hoplite, todo, mcp, verification]
created: 2026-05-25
aliases: []
document.priority: medium
document.effort: low
document.status: open
---

# Verify hoplite bootstrap with a cold-start test

Three regression scenarios for the SessionStart venv bootstrap — cold cache, manifest drift, pip-install failure. Each exercises one branch of the bootstrap design; together they pin the contract.

The SessionStart hook builds a Python venv at `${CLAUDE_PLUGIN_DATA}/venv` on first install and on `pyproject.toml` drift. Three paths need end-to-end runs to lock in the design: cold cache, manifest drift, install failure.

## Cold cache happy path

Wipe the persistent data directory:

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\plugins\data\hoplite-msl-hoplite"
```

Start a fresh Claude Code session in this repo. Watch stderr for the bootstrap timeline:

- `[hoplite-bootstrap] creating venv at ...`
- `[hoplite-bootstrap] installing hoplite + deps via pip (editable)`
- `[hoplite-bootstrap] bootstrap complete`

Inventory `~/.claude/plugins/data/hoplite-msl-hoplite/` and confirm both `venv/` and `pyproject.toml` exist. Call a hoplite MCP tool to confirm the server speaks.

This is the regression the whole design exists to fix. Run it first.

## Manifest drift

Touch `plugins/hoplite/mcp/pyproject.toml` — bump the version field, change a whitespace, any byte-level change. Restart. The hook rebuilds the venv. Revert.

## Install failure — pip-fail teardown

Add `nonexistent-pkg-xyz-12345` to `pyproject.toml`'s `dependencies` list. Restart.

Expected behavior:

- Bootstrap logs `pip install failed (rc=...)` to stderr.
- Bootstrap calls `shutil.rmtree(venv, ignore_errors=True)` to tear the partial venv down (`plugins/hoplite/hooks/bootstrap-venv.py:79`).
- Snapshot manifest unlinks so the next session retries from scratch.
- `launch.py` polls for 60s, finds no interpreter, emits its missing-venv error pointing at the `[hoplite-bootstrap]` lines.

What this guards against: a previous failure mode where a freshly-created venv survived a failed pip install, `launch.py` found an empty interpreter, and the server crashed on `import yaml` — the original symptom with extra latency. The fix at `bootstrap-venv.py:79` (rmtree on pip non-zero exit) closes that hole; this scenario is the regression test that keeps it closed.

Revert the bogus dep, restart, confirm clean rebuild.
