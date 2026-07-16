---
title: Data-model spec drafting and cold-review iteration
summary: Draft the MCP graph runtime data-model spec; three cold-review passes tighten the sidecar shape, the envelope semantics, and the apply_framing scope; spec restructures into docs/mcp/ with a contracts/implementation split.
tags: [journal, mcp, data-model, spec, cold-review, milestone]
created: 2026-05-23
---

# Data-model spec drafting and cold-review iteration

Draft the MCP graph runtime data-model spec; three cold-review passes tighten the sidecar shape, the envelope semantics, and the `apply_framing` scope; spec restructures into `docs/mcp/` with a contracts/implementation split.

## Intent

The runtime thesis from two days earlier ([[docs/journal/2026-05-21-0401-mcp-runtime-thesis-and-hello-world.md]]) declared a graph runtime; the data-model spec turns that thesis into something implementable. The spec needs concrete shapes for:

- Storage layout — where notes live, where the index lives, what the sidecar file looks like.
- Sidecar schema — fields, types, defaults.
- Label vocabulary — auto-derived labels, author-supplied labels, framing-axis labels.
- Edge vocabulary — the day-one minimum (`mentions`, `related`) plus deferred candidates.
- Tool API contracts — full request/response shapes for every public tool.
- Indexer operations — exactly what happens on `insert`, `update`, `delete`, on a per-step basis.

A spec this size has too many internal couplings to land in one pass. Plan was: draft, then cold-review, then iterate.

## What happened (chronological)

- 2026-05-23 00:40 — Draft data-model spec for mcp graph runtime; extend parent runtime note. First-draft commit. ~1500 lines of spec landed in one push.
- 2026-05-23 10:49 — Address cold-review findings on `mcp-graph-runtime-data-model`. First review pass surfaces a stack of structural issues.
- 2026-05-23 11:07 — Refresh refactor task list; demilitarize journaling description; prune superseded notes. Bookkeeping pass capturing what the review surfaced beyond the spec itself.
- 2026-05-23 11:08 — Address second-pass review of `mcp-graph-runtime-data-model`. Second cold-review iteration.
- 2026-05-23 12:13 — Address final-review findings; split sidecar and note formats. Third pass surfaces that mixing markdown frontmatter and YAML sidecars in the same file violates the one-format-one-role rule. Sidecars become pure YAML; notes become pure markdown with no frontmatter.
- 2026-05-23 12:35 — Close gaps from post-review pass: label sidecar creation, envelope bootstrap, `apply_framing` tool.
- 2026-05-23 12:37 — Scope `apply_framing` to label envelopes only.
- 2026-05-23 13:11 — Self-review pass: unify return type, structure the envelope, close small gaps. `FetchedNode` shape unifies across `invoke` and `read`; `Envelope` becomes a structured object with `framing` + `primes` fields.
- 2026-05-23 18:07 — Restructure mcp graph runtime spec into `docs/mcp/` with contracts/implementation split. The single spec file decomposes into a folder with contract docs (data-model, behavior, tool-api) and an implementation doc, plus a decision-log and a roadmap.

## The cold-review pattern

Three review passes in ~3 hours, each hand-off to a fresh agent reading the spec without context. Each pass surfaced different things:

- First pass — structural issues. Where the spec was internally inconsistent (sidecar shape disagreed with worked example, edge type list in one place didn't match the other).
- Second pass — semantic issues. Where the spec was internally consistent but the consequence was wrong (label uniqueness rules that would have prevented common cases).
- Final pass — format issues. Where the same file was carrying two file roles, where one tool's contract leaked through another's, where the envelope was a blob instead of a structure.

The pattern that emerged: read the spec the way the implementer would read it, identify the first thing they would have to ask, fix that, repeat. Each pass produced one clean commit; the spec converged.

## Decisions captured

- Pure-format files. Markdown files carry markdown; YAML files carry YAML. Mixed frontmatter-in-markdown was rejected for sidecars even though it works elsewhere — the role separation was load-bearing. Notes have no frontmatter; the body is the body.
- `FetchedNode` is one shape for both verbs. Both `invoke` and `read` return the same record; the verb chooses what fills the `envelope.framing` field and whether `envelope.primes` is populated. The agent (or its runtime) composes for display by concatenating `framing + primes + body` in that order.
- `apply_framing` is scoped narrow. Only label-envelope files. The read envelope at `docs/index/envelopes/read.md` is operational, edited by hand or via repair, not via the agent surface.
- Envelope ordering follows LLM attention. Framing at the strong start, body at the strong end, supplementary primes in the middle. This shape outlived the spec by several days — even after the retrieval tools died in the redesign, the framing-prefix-then-body ordering survived as a principle.
- Contracts split from implementation. The folder restructure on the evening of the 23rd was the recognition that "what the agent sees" and "how the indexer builds it" are different concerns that deserve different docs. The split foreshadows the docs/specs/ recompose two days later, which collapses the same docs back into a single architecture file when the contract/implementation distinction stops mattering after day-one ships.

## What this spec set up

- The data-model was the working blueprint for the next 36 hours. The next two days' code work — label-expression parser, candidate-filter, MinHash, wikilinks, ids module — built against this spec.
- The decision-log file got created during this session and became the running record of design supersession through the redesign.

## What this spec didn't survive

Most of it. The next session brought SQLite-hybrid as a peer implementation; within a day SQLite-hybrid won and the file-based design was dropped. Within two days the entire surrogate-key ULID identity model died and identity collapsed to path. Within three days the retrieval tools died and Hoplite became dataview over documents.

The spec was the scaffolding the design climbed up before being replaced. It captured a snapshot of an intermediate position. The cold-review iteration was right; the spec was right at the moment it was written; the design moved past it.

## Next

SQLite-hybrid lands as a peer implementation later that evening. See `[[journal/2026-05-24-0411-sqlite-hybrid-wins-file-based-dropped]]`.
