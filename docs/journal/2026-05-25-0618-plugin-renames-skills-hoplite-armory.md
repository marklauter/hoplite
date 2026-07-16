---
title: Plugin renames — skills → hoplite → armory; frontmatter on the corpus
summary: The plugin name churns from skills to hoplite to armory in three commits over two hours while the skill and the MCP package stay named hoplite. Reindex gets labeled destructive. hoplite_dump_index default extension changes index.db → index.sqlite. Frontmatter gets added to 30 corpus docs so the new graph can index them.
tags: [journal, plugin, naming]
created: 2026-05-25
---

# Plugin renames — skills → hoplite → armory; frontmatter on the corpus

The plugin name churns from `skills` to `hoplite` to `armory` in three commits over two hours while the skill and the MCP package stay named `hoplite`. Reindex gets labeled destructive. `hoplite_dump_index` default extension changes `index.db` → `index.sqlite`. Frontmatter gets added to 30 corpus docs so the new graph can index them.

## Intent

Post-bootstrap, the plugin had two naming problems:

1. The plugin name was `skills`, inherited from when this was a generic skills plugin. With Hoplite now the centerpiece, `skills` no longer described what the package was.
2. The skill and the MCP package both wanted the name `hoplite`. The plugin can't share its name with one of its components without confusing the install URL and the marketplace listing.

The corpus also needed work: 30 documents under `docs/` predated the frontmatter contract. They had no `title`, no `summary`, no `tags` — none of what the indexer reads.

## What landed (chronological)

- 2026-05-25 04:59 — Rename plugin skills → hoplite; bootstrap on python3; reindex destructive. The first rename. The bootstrap script switches from `python` to `python3` because some Linux distros leave `python` unaliased while `python3` is reliably present. `reindex` gets labeled destructive in the tool description so the agent treats it with the appropriate caution.
- 2026-05-25 05:12 — Three small commits ("x", "upd"): churn during the rename propagation.
- 2026-05-25 05:14 — Fixed.
- 2026-05-25 06:03 — Rename plugin hoplite → armory; skill and mcp stay hoplite. The second rename. The skill is `hoplite`, the MCP package is `hoplite`, the plugin that ships them gets a separate name (`armory`). The original `armory` package gets reused — same name pattern as `msl.armory` from a week earlier. The split clears the name collision.
- 2026-05-25 06:11 — `hoplite_dump_index` default: `index.db` → `index.sqlite`. The extension is operationally honest: the dump is a SQLite file, not an opaque database blob.
- 2026-05-25 06:18 — Add Hoplite frontmatter to 30 corpus docs. The corpus learns the frontmatter contract. Each of the 30 docs gets `title`, `summary`, `tags`, `created`, `aliases` — the five mandatory fields.

## Decisions captured

- The plugin name is `armory`. The MCP-server name and the skill name are `hoplite`. The split is durable: armory is the shipping container, hoplite is the knowledge-graph project inside it. (This decision held inside the Claude repo until the project moved out to its own repo later that day; see `[[journal/2026-05-25-1934-skill-md-to-component-and-the-repo-split]]`.)
- `python3` over `python`. The `python` alias is unreliable across distros; `python3` is the convention.
- Reindex is destructive. The rebuild discards the in-memory graph and rebuilds from disk. The destructive label warns the agent against calling it casually mid-session — a long-running session pays the cold-start cost on every reindex.
- Dump extension matches the file format. `.sqlite` over `.db`. A developer who picks up the file knows what to open it with.
- Existing corpus joins the new contract. The 30 frontmatter additions weren't a one-off — the discipline is "every doc the indexer sees needs frontmatter." Anything missing it gets skipped with a warning.

## What this exposed

The rename cascade was painful. Plugin name appears in the marketplace manifest, the README install instructions, the manifest's `name` field, the plugin install URL, every skill that names the plugin in cat-injection paths, every hook command string. Two renames in two hours meant two passes through that surface. The frequency of "rename X → Y" commits over the project's history is high enough that any new naming should be more deliberate up-front; rapid iteration on names has a real cascade cost.

## Cross-references

- `[[journal/2026-05-16-1549-marketplace-rename-to-msl-armory]]` — the original armory naming decision.
- `[[journal/2026-05-25-0202-dead-then-redesign-in-memory-graph-and-four-tools]]` — the redesign that created the package the rename was for.

## Next

The EAV property graph refactor lands later the same morning, replacing the per-doc-property storage shape with a node_properties/edge_properties EAV pattern. See `[[journal/2026-05-25-1137-eav-property-graph-refactor]]`.
