---
title: Wiki skills with GitHub-hosted link rules
summary: writing-wiki and reviewing-wiki land as a pair; both locate the sibling source project before writing and converge on the same citation pattern; GitHub-hosted wiki link rules get encoded so the agent stops emitting Obsidian-style links into wikis that render through GitHub.
document:
  tags: [journal, skills, wiki, github, milestone]
  created: 2026-05-16
---

# Wiki skills with GitHub-hosted link rules

`writing-wiki` and `reviewing-wiki` land as a pair; both locate the sibling source project before writing and converge on the same citation pattern; GitHub-hosted wiki link rules get encoded so the agent stops emitting Obsidian-style links into wikis that render through GitHub.

## Intent

Add wiki-authoring and wiki-reviewing to the skill family. A wiki is structurally different from a code review or a journal entry: the source of truth lives in a sibling project, and the wiki is the published surface for explaining that project. The skills need to teach the agent to find the source before writing and to cite it explicitly while writing.

A second concern: link syntax. Obsidian wikis and GitHub-hosted wikis render `[[...]]` differently — GitHub doesn't support double-bracket wikilinks, so the agent has to use markdown links with the right URL shape for sibling-page navigation.

## What landed

- `writing-wiki` learns to locate the sibling source project before writing. The skill body teaches the location protocol: check for a sibling clone, fall back to a sibling under a configured project root, fail loud if neither is present.
- `reviewing-wiki` aligns with the same source-clone location and citation pattern, so the writer and reviewer point at the same external reference.
- GitHub-hosted wiki link rules: markdown links with sibling-relative URLs, never `[[double-bracket]]` inside a GitHub wiki. The skill bodies carry concrete examples of right and wrong shapes.

## Decisions captured

- Wiki skills point at external source projects, not at internal docs. The writer doesn't make claims it can't cite; the reviewer judges claims against the citable source. The location protocol makes this enforceable.
- Link syntax depends on the render target. Skills that produce content for a specific publishing platform have to know that platform's syntax. Carrying that knowledge inside the skill body is preferable to hoping the agent infers it from context.
- Writer/reviewer pairs share location and citation conventions. If the writer used a different source-clone path than the reviewer, evidence-based review would fall apart on the first citation.

## Next

The composition-skills tweaking later the same day starts pulling editorial discipline up into a shared spine. The wiki skills become candidates for the same downstream refactor when writing-prose lands.
