---
title: Pivot from runtime cat to build-time mail merge
summary: Runtime `!`cat ${CLAUDE_PLUGIN_ROOT}/components/...`` injection breaks for consumers under the auto-mode classifier; the fix is to pre-inline components at build time and ship self-contained SKILL.md files.
tags: [journal, hoplite, skills, plugin, decision]
created: 2026-05-27
---

# Pivot from runtime cat to build-time mail merge

Runtime cat injection inside skill bodies works on this repo but fails in any consumer that installs the plugin. The auto-mode classifier reads `${CLAUDE_PLUGIN_ROOT}` paths as out-of-scope and denies the bash. The fix is to drop runtime expansion entirely — inline components at build time from a `templates/` source tree.

## Context

Going in: skills under `plugins/hoplite/skills/<name>/SKILL.md` injected reusable components via `!`cat ${CLAUDE_PLUGIN_ROOT}/components/<area>/<file>.md`` lines. Components lived at `plugins/hoplite/components/{shape,prose,hoplite}/`. The "one-level composition" convention in CLAUDE.md leaned on this: skill cats component, component cats nothing.

Unknown going in: whether the auto-mode classifier would allow that cat to run when the plugin is installed in a foreign repo, where `${CLAUDE_PLUGIN_ROOT}` expands to a path outside the consumer's working tree.

## Attempted

The user reported the error from a consumer repo:

> Shell command permission check failed for pattern "!`cat D:/hoplite/hoplite/plugins/hoplite/components/shape/artifact-structure.md`": Permission for this action was denied by the Claude Code auto mode classifier. Reason: Reading from an unrelated repo (D:/hoplite) outside the project scope — scope escalation.

Researched whether plugins can ship a default permissions allowlist that consumers inherit, and whether switching to `Read` or `@file` would dodge the classifier. Both came back negative — permissions live only in settings files, and the classifier flags any read from `${CLAUDE_PLUGIN_ROOT}` regardless of tool. Possible workarounds enumerated:

1. Inline every component into each SKILL.md (kills sharing).
2. Serve components through the MCP server as a tool/resource (MCP traffic isn't gated by the bash scope classifier).
3. Document a permission rule consumers must paste into their settings.
4. Build-time mail merge — keep `templates/components/` as the source of truth, expand into self-contained `plugins/hoplite/skills/*/SKILL.md` artifacts via a `build_skills.py` script.

## Decision

Go with option 4. The bug is the cat injection specifically — runtime bash reach into `${CLAUDE_PLUGIN_ROOT}` is what the classifier denies. Once the injection is done at build time, nothing in the shipped plugin reads `components/` anymore: the only other reader was `plugins/hoplite/hooks/check-frontmatter.py`, which pulled the canonical example out of `components/shape/frontmatter.md`; that becomes a module-level string constant inside the hook. With no remaining consumer, `plugins/hoplite/components/` has no reason to ship and gets deleted.

Marker syntax is `((<rel-path-from-templates>))` on its own line; the build script replaces each marker with the literal content of the referenced file before writing the shipped SKILL.md.

Rationale:

- No runtime expansion, so no classifier denial in consumers and no consumer-side settings to add.
- Components stay DRY — one source under `templates/components/`.
- The plugin install ships only what runs: skills, hooks, MCP server. No latent disk surface to reach into.
- One-level composition still holds; the script refuses markers inside component files.
- Anchor links across inlined components keep resolving because they all land in the same rendered document, same as today.

Cost accepted: `plugins/hoplite/skills/*/SKILL.md` becomes generated artifact rather than source. Needs a header comment marking it generated, and ideally a pre-commit or CI check that re-runs the build and fails on drift. The canonical-frontmatter example now lives in two places — `templates/components/shape/frontmatter.md` (authored prose) and `check-frontmatter.py` (string constant) — small duplication for a clean install boundary.

## Next

Implement `build_skills.py` at the repo root, build out `templates/skills/` and `templates/components/`, regenerate the shipped skill files, and update CLAUDE.md to retire the `${CLAUDE_PLUGIN_ROOT}/components/...` convention. Append outcomes to this entry as the work lands.
