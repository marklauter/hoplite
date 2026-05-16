# CLAUDE.md

Claude Code marketplace shipping one plugin, `skills`, at `plugins/skills/`. README covers install; `plugins/skills/tests/run-tests.sh` documents the bash test runner inline.

## Script-location trap

Scripts live in two places:

- `${CLAUDE_PLUGIN_ROOT}/scripts/` — readers and writers shared across reviewer skills.
- `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/` — owned by one skill.

A SKILL.md that names a script without anchoring its path leaves the agent looking under the skill dir, finding nothing, and reporting "scripts not installed." Every script reference in a SKILL.md needs an explicit `${CLAUDE_PLUGIN_ROOT}/...` path.
