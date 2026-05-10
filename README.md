# marklauter — personal Claude Code marketplace

A single git repo to centrally maintain my Claude Code skills, replacing copies spread across many project repos.

## Structure

```
.claude-plugin/marketplace.json           # marketplace manifest
plugins/skills/                           # the "skills" plugin
  .claude-plugin/plugin.json
  skills/<skill-name>/SKILL.md            # one file per skill
```

## Install locally

From any directory inside Claude Code:

```
/plugin marketplace add D:/claude
/plugin install skills@marklauter
```

After editing a skill, run `/reload-plugins` to apply.

## Info-dump skill template

Every skill is a single `SKILL.md` with this shape:

```markdown
---
name: <skill-name>
description: When this skill should activate. Be specific about trigger phrases and topics.
---

# <Skill Title>

Brief prose describing what this skill covers and when it loads.

## Philosophy

The principles behind the domain. Why this works the way it does.

## Guidance

Concrete patterns, idioms, and rules. The dense reference material.

## Validation

How to verify the work meets the philosophy and guidance.
```

- **Skill name:** gerund form per Anthropic best practices (`writing-X`, `reviewing-X`, `interviewing-X`).
- **Description:** the trigger. Claude reads this to decide whether to load the skill — invest in it.
- **Body:** the domain knowledge that gets injected when the skill activates.

## Adding a skill

1. Create `plugins/skills/skills/<skill-name>/SKILL.md` following the template above.
2. `/reload-plugins` in Claude Code to test.
3. Commit and push.

## Publishing to GitHub later

Push this repo to GitHub, then update the marketplace source in consumers:

```
/plugin marketplace remove marklauter
/plugin marketplace add marklauter/<repo-name>
```

No restructuring needed.
