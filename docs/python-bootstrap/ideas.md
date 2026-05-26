---
title: Python bootstrap design ideas
summary: Candidate redesign for the venv bootstrap to close the SessionStart-vs-MCP-supervisor race. Captures the proposed shape and open questions before we compare against Anthropic's FastMCP best practices.
tags: [doc, hoplite, bootstrap, mcp, lifecycle, design]
created: 2026-05-25
aliases: []
---

## Problem recap

See [[venv-bootstrap-races-mcp-supervisor-on-plugin-install]] and [[debug-the-venv-bootstrap-race-on-plugin-install]] for the symptom-and-cause writeups.

Short version: `SessionStart` doesn't fire on `/plugin install`, so the MCP supervisor spawns `launch.py` before any venv exists. The launcher polls for 60 s but the supervisor times out the MCP handshake at 30 s. Even on session restart, the bootstrap and the supervisor race — the user often has to manually fire the hook script with env vars set, then `/reload-plugins`.

## Proposed design (claude/hoplite-internal, pre-research)

`launch.py` becomes the single bootstrap orchestrator. On every spawn it does a cheap two-part check:

1. Does the venv interpreter exist at `${CLAUDE_PLUGIN_DATA}/venv/{Scripts,bin}/python[.exe]`?
2. Does `${CLAUDE_PLUGIN_DATA}/pyproject.toml` byte-match `${CLAUDE_PLUGIN_ROOT}/mcp/pyproject.toml`?

**Fast path** (both yes): `subprocess.run([venv_python, "-m", "hoplite.server"])` and inherit its return code. Same as today.

**Bootstrap path** (either no): spawn `bootstrap-venv.py` as a **detached background subprocess** (POSIX: `start_new_session=True`; Windows: `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`), then exit `1` immediately with a stderr message along the lines of:

```
[hoplite-launch] venv missing — started bootstrap in background (~30-60s).
[hoplite-launch] Run /reload-plugins after a minute to retry.
```

The detach is the load-bearing piece. `launch.py` exits in milliseconds so the supervisor's 30 s handshake timeout never matters. The bootstrap subprocess survives the supervisor's cleanup because it's in its own process group, and finishes building the venv regardless of what `launch.py` did. On the next `/reload-plugins`, `launch.py` re-runs, finds a populated venv, and spawns the server.

## What this changes

- `plugins/hoplite/mcp/launch.py` — add manifest check + detached bootstrap spawn.
- `plugins/hoplite/hooks/hooks.json` — drop the `SessionStart` entry; `PostToolUse` stays.
- `plugins/hoplite/hooks/bootstrap-venv.py` — unchanged; still works when invoked from launch.py (it doesn't care about the caller).
- `docs/notes/debug-the-venv-bootstrap-race-on-plugin-install.md` — resolve with a journal entry once the fix lands and the cold-install path is verified end-to-end.

## Why drop SessionStart

It's the source of both bugs:

- It doesn't fire on `/plugin install`, so first-install always loses the race.
- When it does fire on session start, it races concurrently with the MCP supervisor's `launch.py` spawn — no ordering guarantee in the plugin spec.

With `launch.py` as the only bootstrap entry point, there's exactly one code path and no concurrency to coordinate. No lock files, no SessionStart, no second-guessing what fired when.

The cost: after a `pyproject.toml` edit (dev workflow only — `pyproject.toml` is the manifest of the bundled MCP server's deps), the first MCP call of the next session takes 30-60 s and needs `/reload-plugins`. End users never see this — they never edit the bundled `pyproject.toml`.

## Open questions

1. **Move `bootstrap-venv.py` to `mcp/bootstrap.py`?** Once it's no longer a hook, the `hooks/` location is misleading. Worth the rename, or skip for churn-avoidance?
2. **Should `launch.py` block-wait briefly (say, 10 s) for an in-flight bootstrap to finish before exiting?** Cheap improvement to the "user is fast and bootstrap is almost done" case — they'd avoid a third `/reload-plugins`. Minor complexity, real UX win.
3. **Does the MCP supervisor actually retry on connection-failure?** If yes, even the user-action requirement goes away — the supervisor's retry catches the now-ready venv automatically. If no, manual `/reload-plugins` is required. **Unknown** without docs or source-read.
4. **What's the supervisor's handshake-timeout behavior?** Does it `kill -9` the launcher, or just give up waiting? If it kills the child process group too, our detached subprocess might also die — `setsid` / `CREATE_NEW_PROCESS_GROUP` defends against that, but only if the supervisor doesn't escalate to `-9` on the whole tree.

## Why we should research first

We are about to ship a hack that detaches a subprocess and exits non-zero on cold install. That's clever, but Anthropic ships FastMCP and Claude Code. They built both sides of this contract. If there's a documented lifecycle pattern for "Python-based MCP server with venv-pinned deps shipped as a Claude Code plugin," we should follow it, not invent our own.

Specifically, before implementing the design above, find:

- Anthropic / Claude Code documentation on **plugin lifecycle hooks** beyond SessionStart. Specifically: is there an `OnInstall`, `OnPluginAdd`, or pre-MCP-spawn hook documented since we last checked?
- FastMCP's own examples and templates for **server startup**, especially any pattern for "server may not be ready when first connection arrives."
- MCP supervisor behavior on **connection failure** — retry policy, kill behavior, exit-code interpretation.
- Reference implementations: any official Anthropic plugin (or community plugin in `claude-plugins-official` / partner orgs) that ships a Python MCP server with bundled deps. How do they handle bootstrap?
- Whether FastMCP supports a "still-loading, please-retry" handshake response that the supervisor would honor. (Unlikely given MCP's stdio shape, but worth confirming.)

If any of the above exists and contradicts the design here, throw this design out and follow upstream guidance.

## Research outcome (claude-code-guide agent + reference re-read, 2026-05-25)

Initial agent search said "no upstream canonical pattern." That conclusion was wrong — a careful re-read of the [official plugins reference](https://code.claude.com/docs/en/plugins-reference#persistent-data-directory) found the canonical pattern explicitly documented:

> The recommended pattern compares the bundled manifest against a copy in the data directory and reinstalls when they differ.

Followed by an npm/`package.json`/`node_modules` example using a `SessionStart` hook with `diff -q` against a snapshot in `${CLAUDE_PLUGIN_DATA}`. **That is exactly the pattern we already have**, translated from npm to pip — the commit message for `ac0db67` even cited the reference. We are following upstream guidance correctly.

Other findings from the research:

1. **Install-time hook does not exist.** [Issue #11240](https://github.com/anthropics/claude-code/issues/11240) requests `PreInstall`/`PostInstall`/`PreUninstall`/`PostUninstall` — closed as duplicate, so the gap is recognized upstream but unfilled.
2. **30 s MCP supervisor timeout is hardcoded.** `MCP_TIMEOUT` affects startup but not the client handshake. [Issue #424](https://github.com/anthropics/claude-code/issues/424) tracks. LSP servers have `startupTimeout`; MCP does not.
3. **MCP spec has no "still loading" handshake.** Per the [lifecycle spec](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle.md), the server must complete `initialize`+`initialized` within the supervisor's timeout. Binary: handshake in time or fail.
4. **`Setup` hook exists but only fires for `--init-only` / `-p --init` / `-p --maintenance` (headless/CI use).** Not for interactive `/plugin install`.
5. **No per-OS `command` conditionals in `plugin.json`.** Flat manifest.
6. **No reference implementation ships a Python MCP server with bundled venv.** `pyright-lsp@claude-plugins-official` is LSP, not MCP, and installs globally. We are the first plugin in the documented pattern's Python variant.
7. **The canonical pattern's first-install race is inherent.** Anthropic's own npm example would also fail first install — `SessionStart` doesn't fire on `/plugin install`, so an MCP server depending on `node_modules` would crash on its first spawn. The doc does not acknowledge this but implicitly expects a session restart (the failure path line says "the next session retries").

## Decision (2026-05-25): Option A — accept the canonical pattern

We **keep the current design unchanged**:

- `hooks/bootstrap-venv.py` (SessionStart hook) — unchanged
- `mcp/launch.py` (resolve venv python, run server) — unchanged
- `hooks/hooks.json` (registers SessionStart + PostToolUse) — unchanged

The detached-bootstrap workaround in this doc is **not implemented.** It would go beyond what upstream documents and create a maintenance branch the rest of the ecosystem doesn't share. Given that:

- We are already following Anthropic's documented pattern verbatim;
- The pattern's first-install race is inherent and unfixed upstream;
- The race is fully resolved by a single Claude Code restart (the implicit expected UX);
- Our dep surface (two pure-Python packages) doesn't justify inventing a parallel mechanism;
- A future `PostInstall` hook ([#11240](https://github.com/anthropics/claude-code/issues/11240)) would obsolete any custom workaround anyway —

the right action is to **document the restart-after-install ritual prominently** and otherwise leave the system as designed. That documentation now lives in `README.md` under Install, with a direct link to the canonical pattern.

### What also got documented (not in this doc)

- `README.md` Install section: explicit "fully restart Claude Code after first install" callout with the upstream reference.
- `README.md` Prerequisites section (pre-existing): Windows-Store-Python guidance and the WindowsApps `python3.exe` stub trap.
- `README.md` Troubleshooting section (pre-existing): venv-rebuild path for stuck states, plus the Windows shim cross-reference.

## What to watch for upstream

- **[Issue #11240](https://github.com/anthropics/claude-code/issues/11240) lands a `PostInstall` hook.** When it does, move the bootstrap there and drop the SessionStart entry. That's the real fix; ours becomes obsolete.
- **[Issue #424](https://github.com/anthropics/claude-code/issues/424) makes the MCP handshake timeout configurable.** With a longer timeout, inline bootstrap in `launch.py` becomes viable as an alternative — no detach gymnastics needed.
- **A Python-specific worked example lands in the plugins reference.** If Anthropic publishes one, our adaptation should be compared against it for any subtleties we missed.

If any of these land, revisit this doc and update the decision.

## Closed open questions

The original "Open questions" section listed two items that no longer apply now that we're not implementing the workaround:

- ~~Move `bootstrap-venv.py` to `mcp/bootstrap.py`?~~ — Not moved. It's still a SessionStart hook; `hooks/` is the correct location.
- ~~Should `launch.py` block-wait briefly for an in-flight bootstrap?~~ — Already does (60 s poll). Per-research, the 30 s supervisor timeout makes anything past 30 s dead weight, but the existing poll is harmless and gives manual `bootstrap-venv.py` invocations a chance to complete before the launcher gives up.

The third question — "does the MCP supervisor auto-retry after connection-failed?" — is unanswered but no longer load-bearing. The user-driven recovery (full Claude Code restart) is the documented expectation regardless.



## See also

- [[venv-bootstrap-races-mcp-supervisor-on-plugin-install]] — symptom and cause from the 2026-05-25 session.
- [[debug-the-venv-bootstrap-race-on-plugin-install]] — investigation TODO that produced this doc.
- `plugins/hoplite/mcp/launch.py` — current launcher.
- `plugins/hoplite/hooks/bootstrap-venv.py` — current SessionStart hook.
- `plugins/hoplite/hooks/hooks.json` — registers both hooks today.
