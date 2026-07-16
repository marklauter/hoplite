---
title: Venv bootstrap race on plugin install
summary: SessionStart hook bootstraps a venv and pip-installs the MCP server; launch.py dispatches to it; subprocess.run replaces os.execv; poll-with-timeout defends against the MCP supervisor starting before the venv exists; venv tears down on pip failure so a half-installed state cannot wedge a session.
tags: [journal, hoplite, mcp, bootstrap, venv, plugin, milestone]
created: 2026-05-25
---

# Venv bootstrap race on plugin install

SessionStart hook bootstraps a venv and pip-installs the MCP server; launch.py dispatches to it; `subprocess.run` replaces `os.execv`; poll-with-timeout defends against the MCP supervisor starting before the venv exists; venv tears down on pip failure so a half-installed state cannot wedge a session.

## Intent

The MCP server is a Python package that needs to be importable when Claude Code's MCP supervisor launches it. The plugin manifest registers a command — something like `python -m hoplite` — and the supervisor invokes it on every session start. The package needs to be installed somewhere that command can find.

Two constraints shape the bootstrap:

- Plugins shouldn't pollute the user's global Python. The package and its dependencies belong in a venv specific to the plugin install.
- The supervisor starts fast. The bootstrap has to be ready before the supervisor tries to run the command, or the command fails with `ModuleNotFoundError`.

## What happened (chronological)

The session opens after the redesign, around 02:54. The new-shape implementation works against a local dev install; making it work on a fresh `/plugin install` is the next problem.

- 2026-05-25 02:54 — docs, hooks, skills. Catch-up commit; the new layout includes hooks.
- 2026-05-25 03:30 — format check.
- 2026-05-25 03:35 — Plugin: SessionStart venv bootstrap + launch.py dispatcher. First-cut bootstrap. SessionStart hook runs `python -m venv` then `pip install`. `launch.py` is the entry point the plugin manifest registers; it dispatches to the venv'd Python.
- 2026-05-25 03:38 — launch: `subprocess.run` instead of `os.execv`. The `os.execv` replaces the running process; the supervisor's expectations about the child PID break. `subprocess.run` is the cleaner shape — `launch.py` is a parent that fork-execs the venv'd Python and waits.
- 2026-05-25 03:42 — launch: poll-with-timeout for venv (race defense); bootstrap: subprocess.run. The race: SessionStart hook fires *before* the supervisor starts the MCP server, but the hook's pip install can take 30+ seconds on first install. The supervisor doesn't wait. If the supervisor wins the race, `launch.py` sees no venv. The defense: poll for the venv with a timeout, give the bootstrap time to finish.
- 2026-05-25 04:13 — Bootstrap: tear down venv on pip failure; quote `${CLAUDE_PLUGIN_ROOT}` in hooks. The venv-creation step is reliable; pip install can fail (network, version conflict, transient registry issue). A partial venv with `python` present but the package missing wedges the system — `launch.py` keeps trying to run, gets `ModuleNotFoundError`, retries forever. The fix: if pip fails, `rm -rf` the venv directory entirely. Next session retries from scratch. The quoting fix: `${CLAUDE_PLUGIN_ROOT}` in hook command strings without quotes broke on paths containing spaces (Windows `Documents and Settings` types of paths).

## Decisions captured

- Venv-per-plugin-install, not global. The venv lives under the plugin's install directory. The MCP server's dependencies don't touch the user's site-packages.
- SessionStart for bootstrap, not /plugin install. Claude Code does not fire SessionStart on `/plugin install` — only on session start. First install of a plugin doesn't bootstrap until the next session. This is a known limitation; the workaround at this stage is "install the plugin, then start a new session." A proper fix would need a Claude-Code-side change.
- subprocess.run, not os.execv. The supervisor expects launch.py to stay alive; replacing the process via execv breaks that expectation. The cleaner parent/child split also lets launch.py do post-run logging that execv would have lost.
- Poll-with-timeout instead of synchronous wait. The bootstrap and the launch run in different OS processes; the launch can't block on the bootstrap directly. A bounded poll loop converges in practice — bootstrap takes ~30 s, poll for 60 s with 1 s intervals, log if it times out.
- Pip failure = teardown. A clean teardown is much better than a half-state that has to be debugged. `rm -rf` the venv on any pip non-zero exit; let the next session retry.
- Quote `${CLAUDE_PLUGIN_ROOT}` in every hook command string. Paths with spaces are common on Windows; unquoted expansion splits the command.

## What this didn't fix

The fundamental race: SessionStart doesn't fire on `/plugin install`. A fresh install still requires the user to restart their session before the MCP server is available. The workaround is documented in the README; a real fix needs upstream support. See `[[debug-the-venv-bootstrap-race-on-plugin-install]]` in `docs/notes/`.

## What surprised me

The number of operating-system-level details a "Python package" install touches. Quoting in shell commands, race ordering across hook events, partial-state recovery on pip failure, parent/child process expectations from a supervisor that has its own assumptions. The MCP server itself is the easy part; the install glue is where the time went.

## Cross-references

- `docs/notes/debug-the-venv-bootstrap-race-on-plugin-install.md` — open TODO for the actual fix.
- `docs/todos/venv-bootstrap-races-mcp-supervisor-on-plugin-install.md` — captured during this work as a longer write-up of the race shape.
- `[[journal/2026-05-25-2252-venv-bootstrap-follows-the-canonical-pattern]]` — later same evening, a design-review pass confirmed the bootstrap layer matches Anthropic's documented pattern verbatim and the race is inherent to that pattern, not our adaptation. The design holds; the workaround is documented.

## Next

The plugin rename dance starts: skills → hoplite → armory across the next few commits. See `[[journal/2026-05-25-0618-plugin-renames-skills-hoplite-armory]]`.
