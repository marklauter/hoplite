---
title: SKILL.md to component, and the repo split
summary: The hoplite SKILL.md body extracts to a component injected by taking-notes and journaling; non-hoplite content prunes; armory renames to hoplite for the new repo; the skill restores as a thin wrapper; the standalone skill renames to using-graph. Tag discipline backfills the corpus with the `note` tag. PowerShell rewrite leaves a UTF-8 BOM that strips off on a follow-up pass.
tags: [journal, hoplite, skill, component, repo-split, milestone]
created: 2026-05-25
aliases: []
---

# SKILL.md to component, and the repo split

The hoplite SKILL.md body extracts to a component injected by `taking-notes` and `journaling`; non-hoplite content prunes; armory renames to hoplite for the new repo; the skill restores as a thin wrapper; the standalone skill renames to `using-graph`. Tag discipline backfills the corpus with the `note` tag. PowerShell rewrite leaves a UTF-8 BOM that strips off on a follow-up pass.

## Intent

Two things happen in this session, partly tangled together:

1. The hoplite skill body (the "what Hoplite is, here are the four tools" reference content) is needed by every authoring skill, not just the standalone `/armory:hoplite` skill. The injection composition pattern from earlier in the month applies cleanly — extract the body into a shared component, inject it into the consumers, the standalone skill becomes a thin wrapper.
2. Hoplite as a project deserves its own repo. The Claude repo (`D:\claude\claude`) carries the whole armory plugin including writing-prose, writing-bash, reviewing-code, github-issues — a broad skill family. Hoplite is the centerpiece of one of those skills' workflows, but it has its own MCP server, its own corpus, its own dev cadence. The split: hoplite-the-knowledge-graph moves to its own repo (`D:\hoplite\hoplite`); the armory plugin in the Claude repo retains the broader skill family.

The two threads collide in this session because both involve restructuring the hoplite skill files and renaming things.

## What landed (chronological)

- 2026-05-25 18:49 — Hoplite: extract SKILL.md to a component; inject into authoring skills. The skill body migrates to `components/hoplite/mcp-reference.md`; `taking-notes` and `journaling` add the cat-injection line; the standalone skill becomes the trigger description plus an inject.
- 2026-05-25 19:15 — Hoplite: prune non-hoplite content; rename armory → hoplite. In the new hoplite repo, the plugin gets renamed from `armory` to `hoplite` since the broader armory family stays in the Claude repo.
- 2026-05-25 19:18 — Moved.
- 2026-05-25 19:21 — Hoplite: restore the skill as a thin wrapper over the component. After the prune, the skill needs to exist again as a trigger handle for the agent — the component on its own has no slash-command name. The skill restores as the SKILL.md frontmatter plus the inject line.
- 2026-05-25 19:23 — Removed.
- 2026-05-25 19:29 — Rename skill hoplite → using-graph. The slash command name conflicted with the plugin name (`hoplite:hoplite` reading as a slash-command identifier). Renaming the skill to `using-graph` clears the collision: `hoplite:using-graph` is unambiguous.
- 2026-05-25 19:29 — Delete.
- 2026-05-25 19:33 — Hoplite: backfill `note` tag onto every doc under `docs/notes/`. Every doc in the notes tree should carry the `note` tag for tag-predicate queries. Backfill walks the tree, opens each doc, adds the tag if missing.
- 2026-05-25 19:33 — Notes: capture venv-bootstrap-races-mcp-supervisor; teach tag discipline. The bootstrap-race note moves to its own file; a teaching note about tag discipline lands alongside.
- 2026-05-25 19:34 — Hoplite: strip UTF-8 BOM from notes after PowerShell rewrite. The tag-backfill pass used PowerShell to rewrite files; PowerShell's default Out-File writes UTF-16 LE with BOM, and earlier in the day a similar pass had been done with `-Encoding utf8` which on Windows PowerShell 5.1 still writes UTF-8 with a BOM. The BOMs broke YAML frontmatter parsing. Sweep pass: open every doc, strip the BOM if present, rewrite.
- 2026-05-25 19:52 — Note: todo for debugging the venv bootstrap race on plugin install. The race that the morning's bootstrap work documented but didn't fix.

## Decisions captured

- Hoplite is its own repo. The Claude repo stays read-only from the hoplite side. Changes to the broader armory family happen there; changes to hoplite happen here. Bidirectional sync is manual, not automated, because the two projects have different cadences.
- Reference content for a tool surface lives in a component, not in a skill. The skill is the trigger (description in frontmatter, slash-command name); the body content the agent loads is the component. Multiple skills can inject the same component without duplicating the content.
- Slash-command names avoid plugin-name collision. `hoplite:hoplite` looks like a typo and parses ambiguously. `hoplite:using-graph` is unambiguous. Naming the plugin and one of its skills the same name creates friction for no benefit.
- Tag discipline applies to legacy docs. The `note` tag isn't only for newly-authored notes; the indexer expects every `docs/notes/*.md` to carry it, including the ones that existed before the discipline did. Backfill closes the gap.
- PowerShell on Windows is BOM-hostile. Any time PowerShell writes a `.md` file, expect a BOM. Either redirect through a python `-c` one-liner that writes without BOM, or follow up with a strip-BOM sweep. The Windows-default-encoding trap shows up reliably enough that a hook or a CI check would be worth building. See `[[feedback_no_node_stack]]` (in memory) for the broader "treat the Windows tooling stack with caution" posture this fits.

## What this set up

The hoplite repo is now self-contained. The armory plugin in the Claude repo continues to depend on the hoplite plugin (the SKILL.md cat-injection line points at the hoplite plugin's component path, expecting a co-installed hoplite plugin). Both ship from the same marketplace catalog; both install side-by-side.

## What this didn't fix

The plugin's marketplace manifest and the README in the hoplite repo still carry some armory-era language. The recompose / triage pass that follows in the same session cleans this up. See `[[journal/2026-05-25-2247-post-1-0-hygiene]]`.

## Cross-references

- `[[journal/2026-05-21-0403-injection-composition-pivot]]` — the original injection pattern this extraction reuses.
- `[[journal/2026-05-25-0202-dead-then-redesign-in-memory-graph-and-four-tools]]` — the design that produced the four-tool surface this skill references.

## Next

Post-1.0 hygiene: README dev layout updates, editorial-principles slim, component injection rules tighten, docs/mcp recomposes into docs/hoplite. See `[[journal/2026-05-25-2247-post-1-0-hygiene]]`.
