---
title: mcp-reference undersells the graph against grep
summary: High-priority TODO. The component at plugins/hoplite/components/hoplite/mcp-reference.md reads like an API spec rather than a recommendation, so agents default to Grep/Glob when they should be calling where and relatives. Seven specific gaps and a one-paragraph fix to add at the top.
tags: [note, todo, hoplite, mcp, design]
created: 2026-05-26
priority: low
effort: low
status: open
---

# mcp-reference undersells the graph against grep

High-priority TODO. The component at `plugins/hoplite/components/hoplite/mcp-reference.md` reads like an API spec rather than a recommendation, so agents default to Grep/Glob when they should be calling `where` and `relatives`. Seven specific gaps and a one-paragraph fix to add at the top.

## Why agents grep

[Inference] An agent (Claude inside a Claude Code session) won't reach for hoplite over grep unless the documentation makes the case. Today's component doesn't. Seven specific gaps:

1. **Grep is the default verb for "find."** Every agent has it in muscle memory; hoplite tools are plugin-specific and require remembering they exist and trusting they work. The reference doesn't push back on that default.

2. **The reference reads like an API spec, not a recommendation.** It says *"`where(predicate, k=5)` — search. Returns up to `k` `Hit` records..."* — what the tool does, not when to reach for it or why it beats grep. Without that framing, the agent treats hoplite as one option among many.

3. **Nothing tells the agent that BM25 ≠ substring match.** An agent that needs "docs about caching" doesn't realize grep finds the literal token `cache` in lines, while `where({"text": "caching"})` ranks documents by topical relevance over body and summary. The reference says "BM25-scored" but the agent reads that as a technical detail, not a capability differentiator.

4. **The related-edges feature is undersold.** The doc says `related` edges come from MinHash similarity above threshold and carry a `confidence` property — mechanism, not value. What it actually gives — topical-neighborhood discovery that grep can't do at all — never gets stated. Traversing via `related` edges surfaces conceptually-adjacent documents the author never literally cross-referenced.

5. **Ghost documents are invisible to grep.** The doc mentions them but doesn't frame the payoff. The graph exposes documents the corpus has mentioned but not yet written — your "open loops" backlog. Grep finds nothing for an unwritten file; `relatives` surfaces ghost nodes as first-class results.

6. **There's no "which tool first" guidance.** Four tools, no decision tree. An agent reaching for the graph has to figure out the workflow alone — `where` to discover candidates, `relatives` to walk neighborhoods, `refresh` after writes, `export` for debug only.

7. **Wikilinks aren't framed as a navigation primitive.** Agents think in files. `[[other-doc]]` and the `mentions` edges it produces give the agent authored, explicit relationships — stronger than any grep heuristic. The doc says `mentions` edges come from wikilinks but doesn't say "follow these to navigate intentional connections."

## Recommended fix

[Guess] Add a short framing block to the top of `mcp-reference.md`. Two parts.

Part one — the default-tool stance, one or two sentences:

> **Reach for hoplite first when navigating the corpus.** Grep and Glob are for literal-token matching and filename patterns; the hoplite tools surface documents by topic, by tag, and by authored or inferred relationship.

Part two — a "when to use what" paragraph contrasting grep and hoplite head-to-head:

> Grep finds substrings; `where` finds topically-relevant documents by BM25 over body and summary. Glob lists files by name pattern; `relatives` walks the graph of authored relationships (wikilinks → `mentions` edges) and inferred relationships (MinHash similarity → `related` edges). Reach for grep when the literal token matters (debugging, exact-string search); reach for hoplite when the topic, concept, or relationship matters.

Part three — a one-line decision aid for the four tools, so the agent picks the right one without re-reading the full spec:

- `where` — discover candidates by text or tag.
- `relatives` — explore the neighborhood of a known starting document.
- `refresh` — after writing or editing markdown under `docs/`.
- `export` — debug only.

The existing API descriptions stay below this framing — they're the spec, and the spec belongs in the doc. The framing tells the agent *when* to use the spec.

## Refinement (2026-05-27)

Reviewed and revised. Diagnosis stands; the recommended fix drifts toward imperative framing ("reach for hoplite first"), which conflicts with the component family's declarative-not-runbook style ([[ghost/skill-shape]]). Four declarative edits applied to `plugins/hoplite/components/hoplite/mcp-reference.md` — landing in the component, not the skill, because `research/SKILL.md` is a thin `cat` wrapper and the same component is injected by `taking-notes` and `journaling`. One edit propagates everywhere.

1. **Extend the positioning paragraph, don't add a section.** The existing line already names hoplite's relationship to the content surface (`Read`/`Write`/`Edit`/`rm`). Parallel sentence added for the discovery surface: `Grep`/`Glob` are the literal surface (substrings, filename patterns); hoplite is the semantic surface (BM25 topical ranking, boolean tag expressions, `mentions` and `related` edges). Declarative contrast — the agent infers the recommendation.
2. **Lead each tool bullet with intent.** `where` now opens with "rank documents by topical relevance" and explicitly contrasts BM25-over-FTS with literal-token matching (the gap the note flags at point 3). Mechanism follows intent.
3. **Frame `related` edges as a discovery primitive in `relatives`.** The bullet now names both relationship kinds — authored (`mentions` from wikilinks) and inferred (`related` from MinHash) — and states the payoff: topical adjacency without an explicit wikilink. Addresses note points 4 and 7 together.
4. **Refresh the ghost-document vocab entry.** Adds "first-class node in `relatives` results, so the corpus's unwritten cross-references stay visible." Capability, not just mechanism. Addresses note point 5.

Deliberately omitted: the note's "one-line decision aid for the four tools" list. Once tool bullets lead with intent (#2 above), a separate decision list duplicates without adding signal.

## See also

- `plugins/hoplite/components/hoplite/mcp-reference.md` — the file this note targets.
- `plugins/hoplite/skills/taking-notes/SKILL.md` and `plugins/hoplite/skills/journaling/SKILL.md` — both inject mcp-reference.md, so the fix lands once and propagates everywhere agents see the tool surface.
- `plugins/hoplite/skills/using-graph/SKILL.md` — the thin skill that loads only mcp-reference.md; the most-direct beneficiary of clearer "use this first" framing.

## Resolution

All four refinement edits are live in `plugins/hoplite/components/hoplite/mcp-reference.md`. The positioning paragraph contrasts the literal surface (`Grep`, `Glob`) with the semantic surface (BM25, tag expressions, edges). The `where` bullet leads with "rank documents by topical relevance" and explicitly opposes BM25-over-FTS to literal-token matching. The `relatives` bullet names both authored (`mentions` from wikilinks) and inferred (`related` from MinHash) relationships and states the payoff. The ghost-document vocabulary entry adds "first-class node in `relatives` results." The deliberately-omitted decision-aid list stays omitted.
