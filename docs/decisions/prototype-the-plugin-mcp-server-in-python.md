---
title: Prototype the plugin MCP server in Python
summary: Plain Python (stdio MCP server, no compiled binary) for the first MCP-server prototype in the skills plugin — chosen for source-inspectable distribution, near-universal runtime presence, and a tight dependency surface.
tags: [note, decision, mcp, python, plugin, claude-code]
created: 2026-05-25
---

# Prototype the plugin MCP server in Python

Plain Python (stdio MCP server, no compiled binary) for the first MCP-server prototype in the skills plugin — chosen for source-inspectable distribution, near-universal runtime presence, and a tight dependency surface.

## The decision

Use plain Python (stdio MCP server, no compiled binary) for the first MCP-server prototype inside the skills plugin. The source ships in the plugin directory; users read every line before granting trust.

## Resolution

Locked in: Shape C, native Python with bash deprecated. The MCP server is the only implementation; the bash scripts (`record-note.sh`, `record-entry.sh`) are gone. Hoplite ships under `plugins/hoplite/mcp/` as the source-of-truth runtime. See [[docs/specs/hoplite-architecture.md]] for the implementation shape that landed.

## What got ruled out and why

- TypeScript / Node. The npm supply chain is the dominant attack vector for JS tooling. Anthropic moved the Claude Code CLI off Node distribution onto a standalone native binary. That move was itself a signal that the org takes the surface seriously.
- C / Rust / Go / C# AOT. All produce a binary the user has to trust without inspecting. The plugin's value proposition is "all-source, plain files." Binaries break that property.
- C# framework-dependent. Clean code and an official MCP SDK, but it adds a ~200 MB .NET runtime install on every user machine. That is real friction. Revisit only if the Python prototype hits scaling pain.
- Native AOT C#. Sold as "single static binary, no runtime." In practice it fights most reflection-heavy .NET libraries, and the MCP SDK itself may or may not be AOT-clean. Risky for a prototype.

## Why Python won this constraint set

- Source-distributable and source-inspectable. The plugin ships `.py` files that users audit. This is the same trust property as the existing bash scripts.
- Native to most Linux distros and macOS. Windows users install once via winget. The runtime ask is small and the install path is well-trodden.
- A tight dependency surface is possible. A `pyproject.toml` with the MCP Python SDK plus standard library covers the slugify, header-format, and file-write tools. No transitive sprawl when the dep list stays disciplined.
- An official MCP SDK exists. No protocol-implementation lift.
- LLM support is excellent. It is the most-trained language in the world, so scaffolding and code review benefit.

## Prototype shape options (decision deferred)

The language is Python. The implementation shape is a separate choice to be made during prototyping. Three viable shapes follow.

### A. Thin wrapper over bash

The Python MCP server exposes `record_note` and `record_journal_entry` as tools. Each tool runs the existing bash scripts (`record-note.sh`, `record-entry.sh`) via `subprocess.run`, with the body piped through stdin as bytes. No shell, no quoting layer, immune to the apostrophe-in-heredoc trap.

- Pro: zero drift. Bash is the single source of truth; Python is just safe transport.
- Pro: bash CLI access for humans is preserved without change.
- Pro: smallest Python codebase to write and maintain.
- Con: subprocess fork on every tool call (negligible at this scale, but real).
- Con: two languages in the runtime stack to debug when something goes wrong.

### B. Native Python alongside bash

The MCP server reimplements slugify, header formatting, and file writes in Python. Bash scripts stay in the repo as a parallel CLI path for humans.

- Pro: single-language runtime for the agent path; no subprocess in the loop.
- Pro: idiomatic Python tests against the actual implementation, no shell coupling.
- Con: two implementations of the same logic. Drift risk over time (slugify rules diverge, header format gains a field in one but not the other).
- Con: maintenance burden doubles for any change to the recording contract.

### C. Native Python, bash deprecated

The MCP server is the only implementation. Bash scripts get removed. Human CLI access becomes `python -m skills_mcp record-note ...` (or a thin shim entry point).

- Pro: single source of truth, single language, zero drift.
- Pro: cleanest long-term shape.
- Con: removes a working CLI path. Humans (and any external scripts that call the bash directly) need to adopt the Python entry point.
- Con: commits to Python on the human-facing path, not just the agent-facing one. Earlier than the trust-and-runtime decision really requires.

### D. Shared library, both bash and Python call it

Extract the recording logic into a single language-neutral implementation, most plausibly a Python module that both the bash entry point (via `python -c` or `python -m`) and the MCP tool call. This inverts shape A: the bash script becomes the thin wrapper.

- Pro: single source of truth without removing the bash CLI.
- Con: bash invoking Python is awkward; the "all-bash, plain files" property of the script set erodes.
- Con: more architectural surface than the prototype needs.

### Initial lean

Shape B (native Python alongside bash for the prototyping window) buys the cleanest Python implementation while leaving the bash CLI untouched as a fallback. If drift between the two becomes a real maintenance pain after the prototype settles, migrate to C. Shape A is the safest if drift risk feels unacceptable from day one. Decide during the prototype, not now.

## Per-CLI lifecycle

The MCP server runs as a per-CLI subprocess on stdio transport. Every open Claude Code session spawns its own instance via the plugin manifest; the process lives as long as the CLI does. One client per server, paired by the parent-child relationship. No network, no port, no auth layer beyond "the CLI spawned me." This is closer to a single-tenant web worker than a multi-client server.

## Trust qualifier

"Source-inspectable" is true at the plugin layer but reduces in practice to "what packages did you list in `pyproject.toml`." No user audits thousands of lines of dependency code. Keep the dep list to the MCP SDK plus standard library plus at most one or two well-known additions, and the property holds for any reasonable threat model.

## References to read later

- MCP spec and overview: `modelcontextprotocol.io`. The protocol home page; covers concepts, message types, and transports (stdio, HTTP/SSE).
- Python MCP SDK: `modelcontextprotocol/python-sdk` on GitHub. The official SDK; includes server scaffolding, tool decorators, and example servers.
- MCP example servers: `modelcontextprotocol/servers` on GitHub. Official reference implementations across languages; useful for shape comparison and protocol-flow study.
- Claude Code plugin authoring: Anthropic's Claude Code docs (`docs.claude.com` or `docs.anthropic.com/claude-code`). Covers plugin manifest format, including MCP server registration.
- Claude Code distribution change: search for "Claude Code native binary distribution." The announcement that moved the CLI off Node and validated the supply-chain concern.

## Open follow-ups

- Confirm the Python MCP SDK's protocol-version compatibility with the Claude Code plugin loader.
