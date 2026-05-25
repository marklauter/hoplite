---
name: writing-wiki
description: Use when writing, refactoring, or composing pages in a software-project wiki — GitHub wiki, docs site, or any partitioned set of pages organized by a sidebar. Sections own the rhetorical context; each section declares `_conventions.md` with its slot values for pages in that section. Loads alongside writing-prose, which owns the universal prose spine.
---

# Writing wiki pages

A software-project wiki is a partitioned document — sections like Getting Started, Reference, and Recipes each own their own rhetorical context. Pages inherit from the section they live in. The sidebar declares the partition. Source code is the sole accuracy authority. Universal prose discipline — voice, density, sentence-case headings, em-dash usage, link mechanics — lives in `writing-prose` and applies unchanged.

Composing a wiki page has six steps: identify the section, load the section's conventions, read the source the page documents, search siblings for the section's pattern, compose the page, save and sweep cross-references.

## Identify the section — locate the partition the page belongs to

Every wiki page belongs to a section, and the section determines the page's rhetorical context. Open `_Sidebar.md` (or the docs engine's equivalent) to read the current partition; place the new page under the section whose audience, voice, and register it matches.

- Sidebar group headings name the section. The group name declares the section to the reader — "Getting Started," "Reference," "Recipes," not "Misc" or "Other."
- A page that fits no existing section either belongs in a new section (update the sidebar in the same change set) or is the wrong page (drop it).
- A page that drifts into another register has a sidebar problem — either it lives in the wrong section, or the section needs to split.
- When a section grows past roughly seven pages, reconsider whether it is two sections. The sidebar is also a cognitive map.

## Load the section's conventions — read the section's `_conventions.md`

Each section declares its rhetorical-context overrides in a `_conventions.md` file. The file declares values for the section-owned slots: Voice, Audience, Subject, Genre, Tone, Register, Intent. Read it before composing.

```markdown
## Rhetorical context

- Voice: declarative, dense, lookup-oriented
- Audience: builders integrating the project, looking up an exact answer
- Subject: a single capability of the project
- Genre: reference page
- Tone: dry, professional
- Register: third-person where appropriate, exhaustive on the surface area, no narrative voice
- Intent: be precise so a reader can find the answer fast
```

File location follows the engine:

- Engines with section folders (mkdocs, docusaurus): `<section>/_conventions.md`.
- Flat-layout wikis (GitHub): `<Section-Name>-_conventions.md` next to the section's pages, or a single `_Conventions.md` with one H2 per section.

The globals (Writer, Ethos, Stance) come from this skill's `## Rhetorical context` block at the bottom of this file and are not restated in section conventions.

When the section has no `_conventions.md` yet, stop and propose one to the user before composing the page. The first page sets the pattern; investing in the conventions first prevents the next ten pages from copying a drift.

## Read the source — verify against the accuracy authority

Every factual claim in a wiki page is grounded in source code, or in an external specification the page cites. Read the relevant source files before writing about them — documenting from memory drifts.

- Locate the source clone. The standard layout is sibling clones — when CWD is `{project}.wiki/`, source is the sibling `{project}/` (strip the `.wiki` suffix). When the wiki lives inside the source repo (a `docs/` subdirectory or a self-hosted engine), source paths resolve normally. If neither layout applies and no source location is configured, ask the user before writing.
- Cite source by symbol — file plus a stable identifier (class, type, method, exported function) — never by line number. Symbols survive refactors that move code within a file; line numbers do not. Form: `(source: ../{project}/src/Pipeline/Builder.cs Build method)` for sibling-clone wikis, or the in-repo equivalent when wiki and source share a tree.
- Code samples compile against the current source. When a type, method, or signature changes, every page that mentions it goes stale; update them in the same change set.
- External references (RFCs, vendor docs, spec URLs) are also accuracy authorities. When they change, the page that depends on them is stale.
- Flag unverified claims in the page or remove them. Unverified claims accumulate into wikis the reader cannot trust.

## Search siblings — learn the section's pattern

The most reliable signal for how a page should sound is the other pages in its section. Read at least two siblings end to end before composing.

- Note the lede shape, the depth of background given, where examples enter, and how the page closes.
- When the section holds only one existing page, that page is the template. Decide consciously whether the new page extends the template or revises it; do not drift.
- When the section is empty, the conventions file is the only signal — invest in it before writing the first page. The first page becomes the template the next ten copy.

## Compose the page — lede first, usage before internals

Compose the page in the section's voice, audience, and register. Lead with what a reader of that section needs. Cite source by symbol where claims have a specific behavior or signature.

- Lede first. The first paragraph names what the page is for and who it serves. A reader who stops there leaves with the right impression.
- Usage before internals. What the reader does — the call, the configuration, the example — precedes what happens inside. Architecture and internals pages name their audience explicitly in the lede so a user who landed by mistake knows to leave.
- Cross-section links do not bleed register. A recipe page may briefly summarize a concept then link to the concept page for depth; the summary stays in the recipe's register.
- Pages within a section reinforce rather than overlap. When introducing a second page that shares ground with an existing one, name the relation — what the new page covers that the existing one does not, and vice versa. Different example shapes are the most reliable way for two tutorials to reinforce each other.
- A domain term used in multiple pages has one canonical definition. The Concepts page (or its section equivalent) owns the definition; other pages link.

!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/template.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/title.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/summary.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/body.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/editorial-principles.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`

### Link mechanics on GitHub-hosted wikis

When the wiki is a GitHub repository wiki (the `{project}.wiki` repo paired with `{project}`), link form follows GitHub's wiki renderer, not general markdown. A link that works locally but breaks at github.com helps no one.

- Detect the host. A CWD ending in `.wiki` is a GitHub wiki repo by convention; assume GitHub link rules unless existing pages contradict. Other engines (Docusaurus, MkDocs, self-hosted) resolve links differently — read existing pages to confirm before writing new links.
- Wiki-to-wiki page links omit the `.md` extension: `[text](Page-Name)`, not `[text](Page-Name.md)`. GitHub resolves the bare slug.
- Page filenames use `Title-Case-With-Hyphens.md`. The link target is the basename without extension. A page renamed on disk needs the same rename in every link.
- In-page and cross-page anchors use GitHub's heading-slug transform: lowercase, spaces and punctuation to hyphens, leading hyphens stripped. `## Picking a Strategy` becomes `#picking-a-strategy`. Cross-page form: `[text](Page-Name#picking-a-strategy)`.
- Links into the companion source repository use absolute GitHub URLs: `https://github.com/<owner>/<repo>/blob/<ref>/<path>`. Prefer a tagged release or commit SHA for `<ref>` when stability matters; `main` is acceptable for living references. Relative `../` paths from the wiki repo do not resolve at render time.
- `_Sidebar.md` and `Home.md` follow the same rules — entries are `[Page Name](Page-Name)` with no `.md`.

## Save and sweep — update the sidebar and cross-references

Saving a wiki page is more than a Write call. The partition map and any pages mentioning the new page's content land in the same change set.

- Update `_Sidebar.md` in the same change set that adds, removes, or moves a page. A page on disk not in the sidebar is orphaned; a sidebar entry pointing at no page is a broken link.
- Order pages within a section by how the reader encounters them. Getting Started reads top-to-bottom; Reference reads alphabetical or by surface-area grouping; Recipes reads by scenario, with the most common first.
- Update `Home.md` after a section is added or renamed. `Home.md` opens with one paragraph naming what the project is and what the reader gets, then routes the reader to the right section for their goal — "new here? start with Getting Started; integrating? jump to Recipes; looking up an API? Reference." The sidebar carries page enumeration; Home routes by reader goal.
- Search the wiki for any identifier the page introduces or renames. Other pages mentioning the old identifier are stale; update them in the same change set.
- When source removes a capability, remove the page that documents it in the same change set. A page documenting a deleted feature is worse than no page.
- After saving, confirm with a minimal acknowledgment — for example, `page saved: <Page-Name>, sidebar updated`. No recital or recap.

## Rhetorical context

- Writer: contributor
- Ethos: expert
- Stance: neutral

Voice, Audience, Subject, Genre, Tone, Register, and Intent are section-owned. Each section declares them in `_conventions.md`. Load that file before composing — a page with no section conventions has no rhetorical context.
