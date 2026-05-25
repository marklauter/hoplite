---
title: Build an inter-agent chat CLI
summary: A CLI the agent shells out to that posts and reads from a Slack channel or Discord — making inter-agent coordination human-visible and cross-machine.
tags: [todo, tooling, agents, messaging]
created: 2026-05-25
aliases: []
---

## Observation

The harness already supports three messaging shapes for agents:

- **Notes** (`docs/notes/`, durable async). Wiki-style files committed to git. Survive compaction. Discoverable via `list-notes.sh` filtered by tag. Cost: no notification — receiving agent has to scan.
- **Loop** (`/loop <interval> /check-inbox`, polling opt-in). Each agent runs its own poll loop against a directory convention like `inbox/<agent-role>/`. Senders write; receivers read on next tick. Symmetric — both sides do the same thing. Minimum interval is 60s, so handoffs are minutes-grain, not real-time. No infrastructure beyond a path convention and one slash command.
- **Background watcher with Monitor** (push, in-session). Run `inotifywait -m -e create inbox/<my-role>/` (Linux) or a portable polling tail (`ls | comm -23 - seen.txt`) as a `run_in_background` Bash. Use the Monitor tool to stream stdout lines as notifications — each emitted path is a new message that wakes the agent immediately. Lifecycle caveat: the watcher lives in the spawning session; it stops when that session ends.

All three are local-filesystem-bound and require both agents to be in the same repo and same host.

## Interpretation

The CLI-to-chat direction widens the scope. Instead of (or alongside) filesystem inboxes, the agent calls something like `chat send <channel> <message>` and `chat read <channel>` that talks to Slack or Discord. The benefits:

- **Human-visible.** The same channel that agents use is the channel humans can read in their existing Slack/Discord client. No "open the repo to see what the agents said." Mark sees the conversation in real time on his phone.
- **Cross-machine.** Agents on different boxes share the channel without sharing a filesystem.
- **Push for free.** Slack/Discord already handle notification infrastructure. No watcher process; just polling reads or webhook-driven listens.
- **Persistence handled.** The chat backend stores history; the CLI doesn't manage a local message store.
- **Mobile reach.** Same as human-visible — humans can intervene from anywhere.

Cost:

- Network dependency. Offline = no messaging.
- Auth/secrets — bot token in env or config. Solvable but real.
- Rate limits — Slack and Discord both have them; the CLI needs backoff.
- Markdown rendering — GitHub-flavored markdown the agent writes will look different in Slack's mrkdwn or Discord's variant. The CLI may need a converter or a fenced-block escape.
- Less diffable than notes; harder to grep history.

Likely shape of the CLI:

- Subcommands: `send <channel> <message>`, `read <channel> [--since <timestamp>]`, `listen <channel>` (long-running, emits one line per message — Monitor-compatible).
- Auth via `CHAT_TOKEN` env var or a config file at `~/.config/chat-cli/config.toml`.
- Channel-as-role convention: `#test-agent`, `#orchestrator`, `#human-and-agents`. The role names the channel; subscribers are whoever's listening.
- A `mention` field so messages can address specific agents in a broadcast channel.
- Output formats: human-readable for `read`, one-line-per-message NDJSON or markdown for `listen` (so Monitor reads it cleanly).

The three modes layer cleanly:

- Notes for durable repo-scoped knowledge that should survive across sessions and humans.
- Loop polling for in-repo agent-to-agent coordination that doesn't need human visibility.
- Chat CLI for anything humans should see, anything cross-machine, anything needing real-time push.

## Next

- Decide Slack or Discord first. Slack has the better webhook story for bots; Discord has the better free-tier for hobby use.
- Sketch the CLI surface — subcommand list, argument shapes, output formats. One page.
- Prototype against a single channel before generalizing. The `listen` subcommand is the load-bearing one — it has to emit one line per message cleanly so Monitor can stream it.
- Decide whether the CLI is shipped as part of this plugin (a script under `scripts/`) or as a separate repo/binary the agent shells to.
- The test-agent handoff use case from this session — sharing test cases between agents working on the same repo — is a good first concrete user.
