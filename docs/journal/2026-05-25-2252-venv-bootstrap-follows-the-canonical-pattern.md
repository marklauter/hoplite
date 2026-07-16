---
title: Venv bootstrap follows the canonical pattern; the race is upstream's
summary: Opened the session suspecting our venv-bootstrap layer was over-engineered or wrong. After tracing the design back through git, reading the official plugins reference end-to-end, and ruling out workarounds, the answer is the opposite — we adapted Anthropic's documented npm pattern verbatim, and the first-install race is inherent to that pattern, not our adaptation. Keep the design; document the restart-after-install ritual.
tags: [journal, mcp, python, claude-code, decision]
created: 2026-05-25
---

# Venv bootstrap follows the canonical pattern; the race is upstream's

Opened the session suspecting our venv-bootstrap layer was over-engineered or wrong. After tracing the design back through git, reading the official plugins reference end-to-end, and ruling out workarounds, the answer is the opposite — we adapted Anthropic's documented npm pattern verbatim, and the first-install race is inherent to that pattern, not our adaptation. Keep the design; document the restart-after-install ritual.

## Trigger

The conversation opened with "do you think this bootstrap-venv.py actually works?" The hook is well-formed — stdlib-only, idempotent manifest check, cleanup on pip failure, returns zero so SessionStart never blocks. The open question was whether the broader orchestration around it was a hack we invented or the canonical way to ship Python deps in a Claude Code plugin.

## Dead end: PATHEXT and `.py`-as-command on Windows

[Observation] First detour explored whether we could sidestep the `python3` requirement on Windows by invoking the launcher's `.py` file directly. Tested in PowerShell, cmd.exe, and Git Bash:

- Git Bash works — POSIX shebang plus execute bit via MSYS.
- PowerShell and cmd both refuse to dispatch `.py` unless `.PY` is in `PATHEXT`.
- `PATHEXT` on this Windows install was `.COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC;.CPL` — no `.PY`.
- Setting Python 3.13 as the default `.py` handler made the dispatch *open* the file via `ShellExecute`, but in a detached console. Output went to a popup that flashed and closed. Fatal for MCP server stdio, which needs the supervisor's pipes.

[Reference] Confirmed via https://discuss.python.org/t/windows-python-installer-not-changing-pathext/22011 that the official Python position is to add `.PY` to `PATHEXT` only for admin/all-users installs, with no plan to change. Upstream Python ecosystem limitation, not Claude Code's. Abandoned the approach. README already documents the Microsoft Store install workaround for the WindowsApps `python3.exe` shim trap that prompted this whole detour.

## Archaeology: original hello-world had no bootstrap

[Observation] Git history confirmed user memory:

- Commit `4fed242` (May 21) — original hello-world MCP plugin. `plugin.json` was `"command": "python", "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]`. Single dep (`mcp`). No `launch.py`, no `bootstrap-venv.py`, no `SessionStart` hook. Worked because system Python had `mcp` installed at the time.
- Commit `a41f227` (May 24) — added `.venv` to `.gitignore`. That was a *dev* venv for pyright/pytest/ruff, never shipped with the plugin.
- Commit `ac0db67` (May 25, earlier today) — introduced the SessionStart venv bootstrap plus `launch.py` dispatcher. The commit message cites the source directly: *"Per the Claude Code plugins reference, deps live under `${CLAUDE_PLUGIN_DATA}` and a SessionStart hook bootstraps them with manifest-diff detection. Adapted the doc's npm pattern to Python with venv + `pip install -e`."*

[Inference] The bootstrap layer entered because we added `pyyaml` as a runtime dep and system Python crashed on `import yaml`. Three alternatives were available at that decision point: document `pip install` as a prereq, vendor PyYAML, or replace it with a stdlib YAML subset parser. We took the venv-bootstrap path. Today's audit asked whether that was the right call.

## Research: the canonical pattern is documented and matches ours

A first-pass research agent reported "no canonical pattern exists." Wrong conclusion. A careful re-read of https://code.claude.com/docs/en/plugins-reference#persistent-data-directory turned up the exact pattern:

> The recommended pattern compares the bundled manifest against a copy in the data directory and reinstalls when they differ.

Followed by an npm example using a `SessionStart` hook with `diff -q` between bundled `package.json` and a snapshot copy in `${CLAUDE_PLUGIN_DATA}`. That is precisely the shape we built, translated from npm/`node_modules` to pip/venv. Commit `ac0db67`'s message had cited this exact section. We are following upstream guidance verbatim.

[Inference] The npm example carries the same first-install race we hit — `SessionStart` does not fire on `/plugin install`, so the MCP supervisor spawns the server before the hook has run, the server crashes on the missing dep, the user must restart Claude Code. Anthropic does not acknowledge the race in the doc but implicitly expects session-restart as the recovery (the failure-path comment in their example says "the next session retries"). The race is a property of the pattern, not of our adaptation.

Related upstream gaps surfaced by the research:

- [issue #11240](https://github.com/anthropics/claude-code/issues/11240) — request for `PreInstall`/`PostInstall` plugin lifecycle hooks. Closed as duplicate, so the need is recognized upstream but unfilled.
- [issue #424](https://github.com/anthropics/claude-code/issues/424) — request to make the MCP handshake timeout configurable. Currently hardcoded at 30 s.
- No per-OS `command` conditionals in `plugin.json`. Confirmed against the manifest schema and the official plugins repo.
- No reference implementation in `claude-plugins-official` ships a Python MCP server with bundled venv. `pyright-lsp` is LSP (not MCP) and installs globally. Hoplite is the first plugin to instantiate the documented pattern's Python variant.

## Decision: keep the design, document the ritual

Three paths considered:

A. Live with the canonical race. Document "restart Claude Code after first install" prominently and link the upstream reference. ← Chosen.

B. Detached-bootstrap workaround in `launch.py`. Self-bootstrap on cold start, spawn a detached subprocess, exit fast so the supervisor cannot time-kill the install. More code, no upstream blessing, obsoleted by a future `PostInstall` hook.

C. Skip the canonical pattern entirely. Tear out the venv layer, document `pip install mcp pyyaml` as a prereq. Simpler than A and B combined, but abandons the `${CLAUDE_PLUGIN_DATA}` isolation Anthropic blesses.

[Decision] Option A. Reasons: we are following the documented pattern verbatim; the race is inherent and unfixed upstream; one session restart is the implicit expected UX; our two-pure-Python-dep surface is too small to justify inventing a parallel mechanism; a future `PostInstall` hook would obsolete any custom workaround.

## Side decisions ruled out

Two adjacent ideas surfaced and got rejected:

A `userConfig` choice between venv and system Python — implementable via `userConfig.python_mode` plus env-var dispatch in `launch.py` and the hook. Rejected: two code paths to maintain forever, userConfig prompt adds friction, power users can already opt out by editing `plugin.json` locally. Disproportionate for two pure-Python deps.

A `windows-release` Git branch that swaps `python3` for `python` — Rejected: permanent merge tax, marketplace discoverability problem (one marketplace entry cannot conditionally pick branches), branch drift, no benefit to Linux/macOS users, obsoleted the moment Anthropic adds per-OS `command` conditionals to `plugin.json`.

## Outcome

- `README.md` Install section — added a "fully restart Claude Code after first install" callout with a direct link to https://code.claude.com/docs/en/plugins-reference#persistent-data-directory.
- `docs/python-bootstrap/ideas.md` — full design doc capturing the proposed-but-rejected detached-bootstrap workaround, the research findings, and the Option A decision with reasoning.
- `plugins/hoplite/hooks/bootstrap-venv.py`, `plugins/hoplite/mcp/launch.py`, `plugins/hoplite/hooks/hooks.json` — unchanged.
- Committed as `25e692b`.

## Next

- Watch issue #11240. When `PostInstall` lands, move the bootstrap there and drop the `SessionStart` entry. That is the real fix; ours becomes obsolete.
- Watch issue #424. With a configurable handshake timeout, inline bootstrap in `launch.py` becomes viable without detach gymnastics.
- Add a comment on #11240 (or file a fresh issue) describing this use case — Python MCP server with bundled venv — so Anthropic has receipts when prioritizing.

## See also

- [[docs/todos/venv-bootstrap-races-mcp-supervisor-on-plugin-install.md]] — symptom-and-cause note from earlier in the session.
- [[ghost/debug-the-venv-bootstrap-race-on-plugin-install]] — investigation TODO this cycle closes.
- [[ghost/python-bootstrap/ideas]] — the design doc capturing the proposed-but-rejected workaround and the Option A decision.
