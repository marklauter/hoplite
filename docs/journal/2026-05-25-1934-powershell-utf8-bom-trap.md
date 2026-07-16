---
title: PowerShell UTF-8 BOM trap
summary: Windows PowerShell 5.1's Out-File with -Encoding utf8 writes a byte-order mark; YAML parser sees the BOM as content and the frontmatter fails to parse. Sweep pass strips BOMs from notes rewritten through PowerShell.
tags: [journal, hoplite, windows, powershell, encoding, bug-fix]
created: 2026-05-25
---

# PowerShell UTF-8 BOM trap

Windows PowerShell 5.1's `Out-File` with `-Encoding utf8` writes a byte-order mark; YAML parser sees the BOM as content and the frontmatter fails to parse. Sweep pass strips BOMs from notes rewritten through PowerShell.

## What happened

The tag-discipline backfill ([[docs/journal/2026-05-25-1934-skill-md-to-component-and-the-repo-split.md]]) needed to walk every doc under `docs/notes/`, add the `note` tag if missing, and rewrite the file. The backfill ran from a PowerShell session — the natural Windows shell for this repo. PowerShell's idiomatic write-file shape is `Set-Content` or `Out-File`. Both produce a BOM by default on Windows PowerShell 5.1.

After the backfill, the indexer started failing on every touched note. The `---` opening fence had a `﻿` byte sitting in front of it, invisible in most editors but a real byte to the YAML parser. The parser saw the file as starting with `﻿---` and concluded the frontmatter fence was missing.

Every note PowerShell had rewritten became a ghost document — present on disk, absent from the graph.

## The fix

Two passes:

- Strip the BOM from every affected file. Open each `.md` under `docs/notes/`, check for the BOM bytes, remove if present, rewrite without BOM.
- Update the backfill script (and any future PowerShell-driven rewrite) to use a write path that doesn't BOM. Options:
  - `[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))` — explicit BOM-less UTF-8.
  - Pipe the content through `python -c "import sys; sys.stdout.buffer.write(sys.stdin.read().encode('utf-8'))"` from PowerShell. Awkward but explicit.
  - Use `Out-File -Encoding utf8NoBOM` (only available in PowerShell 7+; not in 5.1).

The fix used the first option — `WriteAllText` with explicit BOM-less encoding. Single line, no external dependency.

## Decisions captured

- Windows PowerShell 5.1 is BOM-hostile for cross-tool consumption. Any text file PowerShell writes will carry a BOM unless explicitly told otherwise. Tools that read those files (YAML parsers, JSON parsers, code editors that don't auto-strip) see the BOM as content.
- Treat PowerShell rewrites as a defect-prone path. The CLAUDE.md preference for Python-over-bash applies here too — Python writes UTF-8 without BOM by default; PowerShell takes a tax to do the same.
- BOM-strip sweeps are cheap; do them defensively. Any time a batch script touches `.md` files through PowerShell, follow up with a BOM-strip pass before reindex. The cost is one walk of the affected tree; the benefit is the frontmatter parses.

## What this is part of

The broader Windows-tooling caution: PowerShell's defaults reflect a different era and a different consumer model than the agentic-tool stack expects. UTF-16 LE for text files, CRLF for line endings, BOM for "explicit" UTF-8 — each is a default that survives because changing it would break Windows tooling that depends on it. The cost lands on cross-platform tooling reading the files PowerShell writes.

See also `[[journal/2026-05-25-0202-crlf-frontmatter-parse-bug]]` — the CRLF-frontmatter defect from earlier in the same day. Same defect family: a Windows-default that breaks a parser expecting Unix shape.

## Cross-references

- `[[journal/2026-05-25-1934-skill-md-to-component-and-the-repo-split]]` — the backfill that triggered the BOM problem.
- `[[journal/2026-05-25-0202-crlf-frontmatter-parse-bug]]` — the parallel CRLF defect.
