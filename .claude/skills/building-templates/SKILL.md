---
name: building-templates
description: Use when editing the shipped plugin's skills or templated hook — the parts of plugins/hoplite/ that are mail-merged at build time from templates/. Covers the component-injection markers, the one-level composition rule, anchor cross-references, and the build step. Always edit the templates/ source and re-run the build; never touch the generated outputs.
---

# Building templates

The shipped plugin at `plugins/hoplite/` is the publishable artifact. Some of its files are **generated**: skill bodies and one hook are mail-merged at build time from `templates/`, so the shipped plugin carries no runtime cross-tree reads. Edit the source under `templates/`, then rebuild — never hand-edit a generated output, because the next build overwrites it.

## What is built

`templates/build/manifest.txt` is the source of truth: one `<src> -> <dst>` entry per line, paths relative to the repo root. The build reads each src, expands its markers, and writes the dst. Anything under `plugins/hoplite/` that is **not** a dst in the manifest is committed source, not generated — edit it directly.

- `templates/skills/<name>/SKILL.md` → `plugins/hoplite/skills/<name>/SKILL.md`
- `templates/hooks/check-frontmatter.py` → `plugins/hoplite/hooks/check-frontmatter.py`

To add a new generated file, add its `src -> dst` line to the manifest.

## Component injection

- Skill bodies and the templated hook inject shared content via `{{components/<area>/<file>.md}}` markers. The marker sits on its own line; the build replaces it with the literal file content from `templates/<rel-path>`. In the hook, the marker lives inside a Python string constant.
- **Composition is one level deep** — components must not themselves contain markers. The build errors if they do.
- Components live under `templates/components/{shape,prose,hoplite}/` and start at **H2**; the consuming skill owns the H1.
- Cross-reference a section in an injected component with a markdown anchor link to its H2, not a filename. The GitHub-style anchor is the heading lowercased, spaces hyphenated, punctuation dropped — `## Artifact structure` becomes `[Artifact structure](#artifact-structure)`. Skill and component bodies render into the same document after merge, so the anchor resolves.

## Build

Edit the source under `templates/`, then re-run the mail-merge from the repo root:

```
python templates/build/build.py
```

It expands every listed src and prints each `src -> dst` it wrote. Never edit the generated outputs directly.
