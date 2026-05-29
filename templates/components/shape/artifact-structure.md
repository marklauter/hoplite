## Artifact structure

An artifact covers exactly one topic. It is composed of YAML frontmatter and a markdown body.

See [Frontmatter](#frontmatter).

Template:

```markdown
---
title: <title>
summary: <one-line summary>
document:
  tags: [<tag>, ...]
  created: YYYY-MM-DD
---

# <one-line title>

<one-line summary>

## <a section title>
<content>

## <another section title>
<more content>
```
