---
name: writing-wiki
description: Use when writing, refactoring, or reviewing pages in a software-project wiki — GitHub wiki, docs site, or any partitioned set of pages organized by a sidebar. Treats sections as the unit that owns audience, tone, and register; pages inherit from their section. Loads alongside writing-documentation, which owns the universal prose spine.
---

# Writing wiki pages

A software-project wiki is a partitioned document — sections like "Getting Started," "Reference," and "Recipes" each own their own audience, tone, and register. Pages inherit from the section they live in. The sidebar declares the partition. Source code is the sole accuracy authority.

## Philosophy

These principles describe what makes a wiki coherent across many pages, many sections, and many readers. The universal prose principles — voice, density, sentence-case headings, em dashes, no bold, no tables, link mechanics — live in `writing-documentation` and apply unchanged. The principles below are the wiki-shaped concerns layered on top.

### Sections own the triple

Audience, tone, and register are three independent dimensions, and they belong to the section, not the wiki. A "Getting Started" section can serve beginners in a friendly tone in tutorial register. A "Reference" section can serve active builders in a dry tone in reference register. A "Recipes" section can serve experienced users with a specific scenario in a pragmatic tone in a hybrid register. The same wiki holds all three without contradiction. A page inherits its triple from the section it lives in — not from a wiki-wide setting.

### The sidebar is the partition map

`_Sidebar.md` is the contract that declares which sections exist and which pages belong to each. A page's location in the sidebar tells the reader, and the next author, which triple to honor. A page that drifts into another register has a sidebar problem — either it lives in the wrong section, or the section needs to split.

### Source code is the accuracy authority

Every factual claim in a wiki page is grounded in source code, or in an external specification the page cites. Not training data, not inference, not "this is probably how it works." When prose and source disagree, fix the prose. The bar is stricter for wikis than for general documentation because wiki readers depend on the project — a wrong claim costs them debugging time.

### Document only what exists

Pages exist for capabilities present in source. No speculative pages, no pages for hypothetical features, no stubs marking "to be written." A wiki for what might exist is indistinguishable from a wiki for what does exist — until the reader runs the example and it fails.

### Sibling pages teach the register

The most reliable signal for how a page should sound is the other pages in its section. They define the depth of explanation, where examples enter, the surface tells of the register. Siblings teach more reliably than any prose description of "tutorial register" or "reference register" ever could.

### Cross-section links don't bleed register

A recipe page links into reference pages; a tutorial links into concepts. The link is good; the borrowing of voice is not. Each page is read in its own section's voice, even when pointing into a different section's territory.

### Pages within a section reinforce rather than overlap

When two pages in the same section cover the same ground, they teach the reader twice and confuse them once. Pages in the same section take deliberately different angles, examples, or scopes — reading both compounds rather than repeats. Two tutorials work when they walk through different example shapes; they fail when one is a longer version of the other.

### Home is the front door, not a duplicate index

`Home.md` answers "what is this project and where do I go next." It is not a flat list of every page — `_Sidebar.md` is the index. Home directs the reader to the right section for their goal; the sidebar lets them browse from there.

### Usage before internals

Across a wiki, pages that describe how to use the project come before pages that describe how the project works internally. Within a page, the same rule applies — what the reader does precedes what the system does behind the scenes. Architecture pages exist for contributors and curious users; they do not gate access to usage.

## Guidance

Concrete rules for applying the principles. Each subsection mirrors a Philosophy heading.

### Sections own the triple

- When proposing or revising a wiki structure, name each section's triple explicitly: who the section serves (audience), how it sounds (tone), and what shape its pages take (register). Record the triples in a wiki-level hint file, in `Home.md`'s lede, or in the project's `CLAUDE.md`.
- Standard registers wiki sections take:
  - Tutorial — walks the reader through one task in sequence, builds understanding step by step, second person, present tense, imperative.
  - Reference — dense and lookup-oriented, declarative, exhaustive on the surface area, third person where appropriate.
  - Recipe / how-to — a hybrid with task framing and reference-level density on the meat. Names the scenario the recipe applies to, then shows the construction.
  - Concepts / vision — authoritative-declarative-terse. States the model the rest of the wiki assumes.
- A page that genuinely needs a different triple from its section's is a page that belongs in a different section. Move it before writing.
- Audience and tone are usually wiki-wide enough to record once per section. Register varies more — a Reference section might hold reference-register pages and one or two tutorials that teach the surface area before listing it. Name the exception in the page's lede when it deviates from the section's default.

### The sidebar is the partition map

- Update `_Sidebar.md` in the same change set that adds, removes, or moves a page. A page on disk that is not in the sidebar is orphaned; a sidebar entry that points at no page is a broken link.
- Sidebar group headings name the section. The group name declares the section to the reader — "Getting Started," "Reference," "Recipes," not "Misc" or "Other."
- When a section grows past roughly seven pages, reconsider whether it is actually two sections. The sidebar is also a cognitive map; a flat list of fifteen entries under one heading defeats the partition.
- Order pages within a section by how the reader would encounter them. Getting Started reads top-to-bottom; Reference reads alphabetical or by surface-area grouping; Recipes reads by scenario, with the most common first.

### Source code is the accuracy authority

- The wiki's source project is a sibling directory by GitHub convention: a wiki checked out at `<path>/<repo>.wiki` has its code at `<path>/<repo>`. When invoked inside a `*.wiki` directory, locate the sibling before writing and treat it as the authority for every page. If the sibling is absent, stop and ask — do not write from memory.
- Read the relevant source files before writing about them. Documenting from memory is the most common way pages drift from reality.
- Cite source files with `path:line` notation when claiming a specific behavior or signature. The citation is what makes the claim verifiable on the next sync.
- Code samples in wiki pages compile against the current source. When a type, method, or signature changes, every page that mentions it goes stale; update them in the same change set.
- External references the wiki depends on (RFCs, vendor docs, spec URLs) are also accuracy authorities. When they change, the page that depends on them is stale.
- When a claim cannot be verified against any authority, flag it in the page or remove it. Unverified claims accumulate into wikis the reader cannot trust.

### Document only what exists

- Before adding a page, confirm the capability it documents is present in source. A page for a planned feature is a maintenance burden the wiki cannot honor.
- When source removes a capability, remove the page that documents it in the same change set. A page documenting a deleted feature is worse than no page.
- Stubs have no place. Either write the page or do not list it.

### Sibling pages teach the register

- Before writing a new page in an existing section, read at least two sibling pages end to end. Note the lede shape, the depth of background given, where examples enter, and how the page closes.
- When a section has only one existing page, that page is the template. Decide consciously whether the new page extends the template or revises it; do not drift.
- When the section is empty, name the triple explicitly with the user before writing the first page. The first page becomes the template the next ten copy — invest disproportionate care in it.

### Cross-section links don't bleed register

- Use `[text](Target-Page)` to link into another section. The link text describes what the target is; the linking page does not adopt the target's voice to introduce it.
- A recipe page may briefly summarize a concept it depends on, then link to the concept page for depth. The summary lives in the recipe's register; the depth lives in the concept page's register.
- Do not paste a reference table into a tutorial. Link to the reference page instead. The tutorial's job is to walk the reader through; the reference's job is to be looked up.

### Pages within a section reinforce rather than overlap

- When introducing a second page that shares ground with an existing one, name in the new page how the two relate — what the new page covers that the existing one does not, and vice versa.
- Different example shapes are the most reliable way for two tutorials to reinforce each other: a CLI walkthrough next to a service walkthrough, a synchronous example next to an async one.
- When two pages in the same section have grown to cover the same ground, merge them or split the section. Two pages teaching the same thing twice is the failure mode.

### Home is the front door, not a duplicate index

- `Home.md` opens with a one-paragraph statement of what the project is and what the reader gets from it. Then it points the reader at the right section for their goal — "new here? start with Getting Started; integrating? jump to Recipes; looking up an API? Reference."
- The router shape holds at every wiki size — five pages or fifty. The sidebar carries page enumeration; Home routes by reader goal. Even when a small wiki's page list would fit on Home, directing to sections serves the reader better.
- Update Home when sections are added or renamed. A Home page that points at a section that no longer exists is a broken contract.

### Usage before internals

- Within the wiki taxonomy, Getting Started and Reference (the public surface) come before Architecture and Internals (the contributor surface).
- Within a page, what the reader does — the call, the configuration, the example — precedes what happens inside. The reader who stops at "how do I use it" leaves with a working answer; the reader who continues learns the model.
- Architecture and internals pages name their audience explicitly in the lede. The lede signals "this page is for contributors" so a user who landed by mistake knows to leave.

### Terminology hygiene across pages

- A domain term used meaningfully in multiple pages has one canonical definition. The Concepts page (or its section equivalent) owns the definition; other pages link.
- The same concept is named the same way across the entire wiki. Pick one of "request handler" or "pipeline handler" and use it everywhere.
- When a term's meaning differs by context, name the context: "the handler (the user code)" vs "the handler (the framework's `RequestHandler`)."

## Validation

Validation for wiki pages is the loop the author runs before commit. The reviewer runs the same loop across the whole wiki.

### The four lenses (self-review)

Apply each lens to the page before commit. A page passing all four is ready for formal review.

- Structure — Does the page belong to the right section? Does it lead with what the reader of that section needs? Are there gaps the reader will notice, or content that belongs on a different page? Are the headings and subsection ordering coherent for the page's register?
- Line — Does each sentence carry its weight? Are transitions doing work or announcing? Are there hedges, fillers, or restated sentences to cut?
- Copy — Are terminology choices consistent with the rest of the wiki? Is the heading case sentence-case? Are code identifiers in backticks? Are links pointing at pages that exist?
- Accuracy — Is every factual claim grounded in source code or a cited external authority? Do code samples compile against the current source? Are signatures and identifiers current?

Findings carry a severity:

- must-fix — readers will be confused or misled.
- suggestion — works but could be better.

Address every must-fix before commit; prioritize suggestions by impact.

### The writing loop

1. Read the section's siblings before composing. Confirm the triple before judging your own prose.
2. Read the relevant source files. Documenting from memory is the most common way pages drift.
3. Compose the page. Lede first; usage before internals; cite sources with `path:line`.
4. Reread the changed prose against the four lenses. The check is mechanical.
5. Run `reviewing-documentation` for the formal pass. Address findings before commit.

### Per-page checks

- Open `_Sidebar.md` after every change. The page exists in the sidebar, in the right section, with sensible link text.
- Open `Home.md` after a section change. Home still points at the right entry points.
- Search the wiki for any identifier the page introduces or renames. Other pages mentioning the old identifier are stale.
- Read the page's first paragraph alone. Does it serve the section's audience in the section's tone, in the section's register? If not, the page is in the wrong section or the lede is wrong.

### When to defer to other skills

- Universal prose concerns — voice, density, sentence-case, em dashes, link mechanics, prose-level terminology hygiene — are owned by `writing-documentation`. Load it alongside this skill.
- Formal editorial review across an existing wiki is owned by `reviewing-documentation`. Use it after the writing loop, not as a substitute for it.
- Decisions about whether a wiki should exist for a project, or what its top-level sections should be, belong in a planning artifact (a note or journal entry), not the wiki itself.
