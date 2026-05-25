# Split writing and reviewing skills into a sibling plugin

Extract the prose-shaped skills from `plugins/armory/` into a new `plugins/skills/` plugin so users can install the writing toolkit without the MCP bootstrap.

## Motivation

The `armory` plugin currently bundles two distinct concerns: the Hoplite MCP server (knowledge graph, venv bootstrap, ~5-10s cold-start cost) and the agent-facing skills that consume it. A user who wants only the writing skills pays the bootstrap cost for an MCP server they never call. A user who wants only the knowledge graph pulls in skill definitions they ignore. Splitting separates the install paths.

## Scope

Stays in `plugins/armory/`:

- `mcp/` — server source
- `hooks/bootstrap-venv.py` — SessionStart venv builder
- `hooks/check-frontmatter.py` — PostToolUse validator (binds the docs/ frontmatter contract to the MCP indexer)
- `components/hoplite/frontmatter.md` — the canonical frontmatter spec consumed by taking-notes and journaling

Moves to `plugins/skills/`:

- `skills/writing-prose/`, `skills/writing-python/`, `skills/writing-csharp/`, `skills/writing-wiki/`
- `skills/reviewing-prose/`, `skills/reviewing-csharp/`, `skills/reviewing-wiki/`
- `skills/taking-notes/`, `skills/journaling/`
- `skills/triaging-findings/`, `skills/managing-github-issues/`
- `components/editorial-principles/` (consumed only by writing-* and reviewing-*)
- `scripts/` (shared finding readers and writers)
- `tests/` (bash test runner)

## Dependency story

The `skills` plugin has an undeclared dependency on `armory`: `taking-notes` and `journaling` inject `plugins/armory/components/hoplite/frontmatter.md`, and the `check-frontmatter.py` hook lives in armory. Document the prereq in `plugins/skills/README.md`; the skills fail visibly when armory is missing rather than silently producing malformed docs.

Cross-plugin component reference resolves via absolute path `D:/claude/claude/plugins/armory/components/hoplite/frontmatter.md` (already the case today via the writing skills' injection slot). Verify the path survives the move.

## Marketplace change

`.claude-plugin/marketplace.json` grows a second plugin entry:

```json
"plugins": [
  { "name": "armory", "source": "./plugins/armory" },
  { "name": "skills", "source": "./plugins/skills" }
]
```

Each plugin keeps its own `.claude-plugin/plugin.json`. The skills plugin's manifest declares no `mcpServers` block and no `SessionStart` hook — it's pure markdown plus shared bash scripts.

## Open questions

- Does Claude Code resolve `${CLAUDE_PLUGIN_ROOT}/...` paths across plugin boundaries? If skill A in plugin X injects a component from plugin Y, the env var resolves to X's root — the absolute path is required. Confirm before the move.
- Should `components/editorial-principles/` live in `skills` (its consumers) or `hoplite` (alongside `components/hoplite/`)? Co-locate with consumers — moves to `skills`.
- Test runner: `plugins/armory/tests/run-tests.sh` discovers `*_test.sh` under the plugin root. Splitting means two runners or one runner invoked twice. Decide based on whether tests cross-reference.

## Next

- Confirm cross-plugin `${CLAUDE_PLUGIN_ROOT}` resolution behavior before committing to the layout.
- Create `plugins/skills/.claude-plugin/plugin.json` with the same keywords and author block.
- `git mv` the directories listed above.
- Update marketplace.json with the second entry.
- Update README.md to describe both install commands and the prereq.
- Sweep absolute path references in any moved file.
