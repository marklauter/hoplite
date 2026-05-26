---
title: Injection composition — the !`cat` pivot
summary: SKILL.md learns it can inject other markdown files via `!`cat <path>`` at load time; editorial-principles becomes a component injected by writing-prose, taking-notes, and journaling; foundation/downstream coupling stops being convention and becomes mechanism.
tags: [journal, skills, composition, injection, decision, milestone]
created: 2026-05-21
aliases: []
---

# Injection composition — the !`cat` pivot

SKILL.md learns it can inject other markdown files via `` !`cat <path>` `` at load time; editorial-principles becomes a component injected by `writing-prose`, `taking-notes`, and `journaling`; foundation/downstream coupling stops being convention and becomes mechanism.

## Intent

The foundation/downstream contract from the `writing-prose` refactor was working at the contract level, but the mechanism was still "read both files yourself." Editorial principles lived inside `writing-prose`; downstream skills could declare their overrides but still had to either restate the editorial rules or trust the agent to load `writing-prose` separately. The coupling was conceptual; the wire was missing.

The session opened with two skill-composition notes that had drifted apart in scope. The plan was to merge them into one canonical design. Partway through, the merge surfaced something more interesting than the merge itself.

## What happened (chronological)

- 2026-05-21 01:32 — Discoveries. Working through the merge surfaced that Claude Code's skill loader expands backtick-cat constructions in SKILL.md at load time. A skill that writes `` !`cat path/to/component.md` `` gets the file inlined into its body before the agent ever sees it.
- 2026-05-21 02:01 — Merged skill-composition notes; absorbed v1 design plus the injection discovery into one canonical note.
- 2026-05-21 04:01 — MCP hello-world server added to the plugin (see `[[2026-05-21-0401-mcp-runtime-thesis-and-hello-world]]`).
- 2026-05-21 04:03 — Adopt inject-composition. Extracted editorial-principles into a shared component. Refactored `writing-prose`, `taking-notes`, and `journaling` as injecting consumers.
- 2026-05-21 17:15 — Notes burst capturing follow-ups.
- 2026-05-21 21:37 — Refactored skills (further alignment).
- 2026-05-21 21:52 — Refactor skills complete.

## What changed

The shape:

- The editorial-principles content moved out of `writing-prose` into `plugins/.../components/editorial-principles/`. The component owns the editorial rules.
- `writing-prose` injects the component, declares it the foundation, and keeps its rhetorical-context machinery as the part of the skill specific to authoring.
- `taking-notes` and `journaling` inject the editorial-principles component directly. They do not re-import `writing-prose`. The foundation is no longer the skill the downstreams compose against — it is the component the foundation and the downstreams each consume.

This is structurally different from what the writing-prose refactor had assumed three days earlier. The foundation/downstream pattern is now:

- Foundation skill = author of a contract.
- Components = reusable content fragments that any skill (foundation or downstream) can inject.
- Downstream skill = consumer that injects the same component plus its own genre-specific overrides.

The coupling is one-way through the component, not through the foundation skill.

## Decisions captured

- Injection happens at SKILL.md load time, before agent invocation. The agent reads a single composed body; it never sees the `!cat` lines or the component file paths. The composition is mechanism, not protocol.
- Components are content fragments, not skills. They have no frontmatter, no slash-command name, no description. They are markdown that gets inlined into a host SKILL.md.
- Components start at H2. The host SKILL.md owns the H1 and the trigger description; the component contributes a section under H2 or deeper. See the `feedback_component_starts_at_h2` memory.
- One-way coupling beats foundation-to-downstream coupling. Downstreams don't inherit anything from the foundation skill itself — they inherit by consuming the same components the foundation consumes. The foundation skill stays a peer that happens to inject the most components.

## What this collapsed

- The "downstream must re-derive editorial rules" problem. Three skills now share one component body; an edit to the editorial rules touches one file.
- The "load writing-prose first" protocol pressure. Downstream skills are self-contained; they inject what they need at load time.
- The argument about whether the foundation/downstream contract should be enforced by the loader. It doesn't need enforcement when downstreams reach for the components directly.

## What this set up

Components became the canonical pattern for the next month. Every editorial concern, every frontmatter contract, every cross-skill reference now gets factored into a component. The taking-notes and journaling SKILL.md files of today inject editorial-principles plus frontmatter plus (later) the hoplite tool reference.

The pattern also reframed what later became the hoplite skill / hoplite component split: the `using-graph` skill ends up as a thin wrapper over a `components/hoplite/mcp-reference.md` component that the authoring skills also inject. See `[[2026-05-25-1849-skill-md-to-component-and-the-repo-split]]`.

## Open question carried forward

`${CLAUDE_PLUGIN_ROOT}` and the bare-cat injection have a permission-gate interaction: `!cat $VAR/file` triggers a different prompt than `!cat /literal/path/file`. This bites later when components themselves try to use `${CLAUDE_PLUGIN_ROOT}` internally. The eventual rule lands a week later: components contain no cat injections and no `${CLAUDE_PLUGIN_ROOT}` references; the host SKILL.md resolves the path before passing it. See `[[2026-05-25-2247-post-1-0-hygiene]]`.

## Next

The bash heredoc apostrophe trap bites later in the week while composing notes about why bash needs replacing — concrete evidence the runtime thesis was right. See `[[2026-05-22-2300-bash-heredoc-bites-the-bash-fragility-note]]`.
