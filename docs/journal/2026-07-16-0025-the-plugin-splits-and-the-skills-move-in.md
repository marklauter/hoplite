---
title: The plugin splits and the skills move in
summary: "The msl.hoplite plugin died and the hoplite marketplace took its place: hoplite-skills carries the seven authoring skills, the hook, and the locked specs; hoplite-mcp is a stub."
tags: [journal, plugins]
created: 2026-07-16
---

# The plugin splits and the skills move in

Going in: the repo shipped one marketplace, `msl.hoplite`, wrapping one plugin. The plugin bundled a non-working MCP server with a venv bootstrap, one dead skill, and the live frontmatter hook. The seven authoring skills lived outside the plugin in `.claude/skills/`, where only this repo could use them. Mark ruled the split: delete the old plugin whole, stand up a `hoplite` marketplace with two plugins, `hoplite-skills` and `hoplite-mcp`, and keep the MCP a stub until the engine design settles.

The plan assumed the locked specs could stay at `docs/hoplite/` while the skills cited them by repo path. That broke on first contact: an installed plugin resolves nothing outside its own tree. Mark inverted the dependency. The specs moved into the plugin at `plugins/hoplite-skills/references/` as the source of truth, and `docs/hoplite/frontmatter.md` and `docs/hoplite/expressing-edges.md` became relative symlinks pointing in. Corpus wikilinks kept resolving; the plugin became self-contained. Expected risk: git on Windows checks out symlinks as text files unless `core.symlinks=true` and Developer Mode hold. Both held here. PowerShell's `New-Item -ItemType SymbolicLink` resolved the relative target against the working directory instead of the link location, so the links went in with `cmd /c mklink`.

Before the move, a review of the hook found it had drifted from the locked vocabulary: `edge_grammar.py` said *stereotype* where [[expressing-edges]] says *predicate*, including in an agent-facing diagnostic. Two extraction gaps rode along, fixed in the same commit: a zero-indent YAML block list lost its wikilinks, and an unclosed trailing code fence left its contents live. 101 tests pass.

Install taught the update model the hard way. The marketplace installs by its GitHub source name (`hoplite-skills@marklauter/hoplite`) but updates by its short name. An update only registers when the version in `plugin.json` and the marketplace entry moves, so every content change now bumps both in the same commit. The README had sold the dead MCP server end to end; it was rewritten around what ships.

The skills themselves got three rulings. They are user-invocable only: `disable-model-invocation: true` on all seven, descriptions trimmed from Claude-routing trigger prose to one-liners for the `/` menu. A `## Done when` acceptance checklist landed on all seven and was reverted the same hour; Mark's read was that the glossary skill already defines done as nothing left to cut, and a checklist was the wrong shape. What replaced it: a `## Proofread` section on the five artifact-writing skills, sweeping for machine-prose tells — aphorisms, editorializing, enthusiasm, hedging, announcing, snaking sentences, em-dash excess, empty contrast, cohesion, consistency. The register is engineering: a software architect writing for engineers and architects.

Wrong turns worth keeping: the Done-when detour cost two versions; a Python `write_text` on Windows silently rewrote five skills to CRLF and inflated a diff to 269 lines before `write_bytes` restored LF; and the first append landed `## Proofread` without a blank line above it. This entry is the first artifact written under the installed plugin, hook and proofread both live.
