---
title: CRLF frontmatter parse bug
summary: Windows-style line endings on a markdown file's opening `---` fence threw off the YAML frontmatter parser; documents with CRLF terminators silently fell out of the graph; normalize on read.
tags: [journal, hoplite, frontmatter, windows, bug-fix]
created: 2026-05-25
---

# CRLF frontmatter parse bug

Windows-style line endings on a markdown file's opening `---` fence threw off the YAML frontmatter parser; documents with CRLF terminators silently fell out of the graph; normalize on read.

## The symptom

A reindex pass on a corpus that included files authored on Windows produced fewer documents than expected. Specific docs were missing from query results. Looking at the dump, the affected docs had `documents` rows but no `node_properties` rows — the indexer had loaded the body but not the frontmatter.

The walker's frontmatter parser detected the opening `---` fence, ran the YAML parser on the lines that followed, and rolled forward to the closing `---`. With CRLF terminators, the line containing `---` came back to the parser as `---\r`, which didn't match the expected `---` exactly. The frontmatter block was treated as missing; the YAML body got skipped; the document entered the graph with no tags, no title, no summary.

## The fix

Strip `\r` from line terminators at read time. The body content kept its original terminators (Hoplite doesn't rewrite content), but the parser's view of each line was the normalized form. The fix lived in the walker's file-load function — one strip pass before frontmatter detection.

## Decisions captured

- Normalize line endings at the parser boundary. The walker is the right place — it sits between the disk and every other consumer. Doing the normalize once means downstream code (frontmatter parser, body indexer, wikilink extractor) doesn't have to worry about terminator shape.
- Don't rewrite files. The fix normalizes the parser's view, not the file on disk. Authors keep whatever terminators their editor produces; Hoplite reads through the difference.
- Silent skips are a defect. The parser had been skipping frontmatter without warning when the fence didn't match. After the fix the walker emits a warning if it sees a leading `---` but fails to find a closing `---` — so the next time this happens for a different reason, the failure is visible.

## What this exposed

The walker had no test fixture for CRLF input. The development corpus was authored on Unix-line-ending tools (the editor, the git autocrlf setting, the bash tooling). The corpus that revealed the bug came from a Windows-authoring session where PowerShell's default file-write encoding produced CRLF.

A fixture for CRLF input would have caught this in CI. After the fix, the test suite gained a CRLF-frontmatter test case.

## Cross-references

- `[[journal/2026-05-25-0202-dead-then-redesign-in-memory-graph-and-four-tools]]` — the bug landed in the bug-sweep commit that closed the redesign night.
- `[[journal/2026-05-25-1934-skill-md-to-component-and-the-repo-split]]` — the PowerShell BOM trap that's a sibling Windows-tooling defect.
