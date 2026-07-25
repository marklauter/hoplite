[![claude code](https://img.shields.io/badge/Claude%20Code-plugin-d97757?logo=anthropic)](https://docs.claude.com/en/docs/claude-code/plugins)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![hoplite](https://raw.githubusercontent.com/marklauter/hoplite/main/images/hoplite.small.png "Hoplite")
![MSL Armory](https://raw.githubusercontent.com/marklauter/hoplite/main/images/msl.armory.small.png "MSL Armory")

# Hoplite

*Another weapon from the MSL Armory*

A knowledge graph over a markdown corpus — a **map of meaning** your agent can read, traverse, and act on.

This repo is a Claude Code plugin marketplace (`hoplite`) shipping two plugins:

- **`hoplite-skills`** — the authoring skills, the frontmatter-validation hook, and the locked specs that govern both. Live today.
- **`hoplite-mcp`** — the knowledge-graph engine, as an MCP server. A stub; the engine is under design in the spec corpus at `docs/specs/`.

## What hoplite is

A directory of `.md` files with Obsidian-compatible YAML frontmatter is bare text on disk. Hoplite reads it as a layered map:

- **Substrate** — the bare graph. Every document is a `node`, every link an `edge`. Structure, no meaning.
- **Meaning** — the knowledge graph. A `document` is what a node holds: its frontmatter and content. A `relationship` is a typed link that says *how* two documents relate, not merely that they do. This is the map drawn on the structure.
- **Use** — `affordances`. What the map makes possible for an agent: search it, walk a neighborhood, filter edges by what a link means, rank by relatedness.

Provenance runs through the meaning layer. Every feature is a **fact** — intrinsic, read off the bytes — or a **claim** — asserted by the author or inferred by the engine. So the map separates the terrain from what was drawn on it.

Under the hood, the graph is **RDF-shaped**: a triple store where every statement is subject–predicate–object, every subject and object is a named node, and per-statement confidence rides as an RDF-star annotation. Frontmatter keys and link predicates form one open vocabulary. The full model is in [docs/specs/schema.md](docs/specs/schema.md).

Hoplite natively supports Google's [Open Knowledge Format (OKF)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/). OKF and Hoplite share the same substrate — markdown files with YAML frontmatter, linked into a graph — so an OKF bundle is already a valid Hoplite corpus: each concept file becomes a node, its frontmatter becomes properties, and its markdown links become edges.

The corpus of `.md` files is the only persistent state. Everything else derives from the files on demand. There is no CRUD surface on hoplite itself: content reads go through the agent's `Read` tool, writes through `Write` and `Edit`.

## Install

From inside Claude Code, with `<repo>` as the absolute path to your clone (the directory holding `.claude-plugin/marketplace.json`):

```text
/plugin marketplace add <repo>
/plugin install hoplite-skills@marklauter/hoplite
```

Or straight from GitHub, no clone:

```text
/plugin marketplace add marklauter/hoplite
/plugin install hoplite-skills@marklauter/hoplite
```

After source changes, update the marketplace, then the plugin:

```text
/plugin marketplace update hoplite
/plugin update hoplite-skills@hoplite
```

`/reload-plugins` alone keeps stale cached skill prose.

## Prerequisites

Python 3 — the frontmatter hook runs under system Python, stdlib only, no venv.

When you enable the plugin, it prompts for the **Python executable** to use (default `python3`). Set it to whatever launches Python 3 on your machine — `python3`, `python`, or a full path. To change it later, edit `pluginConfigs` in your `settings.json` or re-enable the plugin, then run `/reload-plugins` (or restart the session) so the new value takes effect.

On Windows, beware the `python3.exe` *App Execution Alias* at `%LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe`: it looks like Python but is a stub that opens the Microsoft Store page when invoked. If you installed Python from python.org, `python3` resolves to this stub and the hook fails — set the plugin's Python executable to `python` instead. To check what a name resolves to:

```powershell
where.exe python3   # a hit under WindowsApps\python3.exe is the stub
```

## What you get

### Skills

Eight skills over one authoring model — the corpus splits into a glossary (terms), specs (concepts), notes (current state), and a journal (history):

- `taking-notes` — capture the current state of one idea under `docs/notes/`; mutable, rewritten freely as understanding moves.
- `journaling` — record what happened as an immutable dated entry under `docs/journal/`; never corrected, only appended.
- `todo` — capture an action item under `docs/todos/`, born triaged: priority, effort, status set at capture.
- `triage` — work the backlog under `docs/todos/`: re-prioritise, mark blockers with `blocked-by` edges, close what's done.
- `decision` — record a hard-to-reverse trade-off as an ADR-equivalent note under `docs/decisions/`.
- `glossary` — reduce a term to its kernel — a word plus the smallest phrase that unpacks it — under `docs/glossary/`.
- `spec` — compose a resolved concept from locked terms into the smallest spec document that carries it.
- `domain-modeling` — the active discipline: interview, challenge terms, stress-test boundaries, then hand each kernel to the skill that owns its form.

### The specs

The locked specs ship inside the plugin at `plugins/hoplite-skills/references/` — the source of truth:

- [`frontmatter.md`](plugins/hoplite-skills/references/frontmatter.md) — flat Obsidian Properties: four special keys (`title`, `summary`, `aliases`, `tags`), every other key open vocabulary; a wikilink value is an edge, anything else a claim.
- [`expressing-edges.md`](plugins/hoplite-skills/references/expressing-edges.md) — the wikilink and edge grammar: inline links, frontmatter edges, inline predicates, anchors, ghosts.

`docs/specs/frontmatter.md` and `docs/specs/expressing-edges.md` are symlinks into the plugin, so the spec corpus reads the same files.

### The hook

`PostToolUse` matching `Write|Edit|MultiEdit` runs `check-frontmatter.py` on every `.md` written under `docs/`: each wikilink — frontmatter and body — is validated against the edge grammar, and malformed or unquoted links come back as an advisory the agent fixes in a follow-up edit. `edge_grammar.py` is the executable form of the expressing-edges spec, with its own test suite.

## Quick start

1. Install `hoplite-skills` (above).
2. Ask the agent to take a note — the `taking-notes` skill writes `docs/notes/<slug>.md` with valid frontmatter:

   ```markdown
   ---
   title: Coffee
   summary: Notes on brewing and beans.
   tags: [note, beverage]
   created: 2026-07-16
   status: evolving
   cites: "[[brewing-methods]]"
   ---

   Beans roast in three colors. Light, medium, dark. See [[brewing-methods]] for extraction.
   ```

3. Write a malformed wikilink and watch the hook object. The corpus opens unchanged in Obsidian: links resolve, properties render in the panel, tags drive the tag pane, and the unwritten `[[brewing-methods]]` shows as a ghost — an open loop waiting for a file.

## Development

Layout:

- `.claude-plugin/marketplace.json` — the `hoplite` marketplace.
- `plugins/hoplite-skills/` — skills (`skills/`), hook (`hooks/`), locked specs (`references/`).
- `plugins/hoplite-mcp/` — stub manifest; no server yet.
- `docs/specs/` — the spec corpus: architecture, graph model, schema, tool API, roadmap.
- `docs/glossary/` — the domain glossary, one node per term.
- `docs/notes/`, `docs/journal/`, `docs/decisions/`, `docs/todos/` — the agent's own corpus: current state, design history, decisions, and action items.

Running tests:

```bash
python -m pytest plugins/hoplite-skills/hooks/test_edge_grammar.py
```

Adding a skill: create `plugins/hoplite-skills/skills/<skill-name>/SKILL.md`, then `/plugin uninstall` + `/plugin install` to refresh the cache.

## Reference

- [docs/specs/README.md](docs/specs/README.md) — spec index.
- [docs/specs/hoplite-architecture.md](docs/specs/hoplite-architecture.md) — the system under design.
- [docs/specs/schema.md](docs/specs/schema.md) — the RDF-shaped storage model.
- [docs/specs/hoplite-tool-api.md](docs/specs/hoplite-tool-api.md) — the planned MCP tool surface.
- [docs/specs/hoplite-roadmap.md](docs/specs/hoplite-roadmap.md) — what comes after.
- [docs/glossary/README.md](docs/glossary/README.md) — the domain glossary, one node per term.
