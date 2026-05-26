## Artifact structure

An artifact covers exactly one topic. It is composed of YAML frontmatter and a markdown body.

See [Frontmatter — the YAML envelope at the top of every document](#frontmatter--the-yaml-envelope-at-the-top-of-every-document).

Template:

```markdown
---
title: <title>
summary: <one-line summary>
tags: [<tag>, ...]
created: YYYY-MM-DD
aliases: []
---

# <one-line title>

<one-line summary>

## <a section title>
<content>

## <another section title>
<more content>
```
