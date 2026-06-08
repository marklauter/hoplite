## Artifact structure

An artifact covers exactly one topic. It is composed of YAML frontmatter and a markdown body.

See [Frontmatter](#frontmatter).

Template:

```markdown
---
title: <title>
summary: <one-line summary>
tags: [<tag>, ...]
created: YYYY-MM-DD
document: # optional — node properties, named value axes (status, severity, ...)
  status: <lifecycle state, e.g. open>
---

# <one-line title>

<one-line summary>

## <a section title>
<content>

## <another section title>
<more content>
```
