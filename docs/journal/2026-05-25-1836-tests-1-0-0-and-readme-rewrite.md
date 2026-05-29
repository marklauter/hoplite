---
title: Traverse tests, version bump to 1.0.0, README rewrite
summary: Focused unit tests for tools.traverse_nodes land; self-loop and mid-graph cycle coverage close gaps in the BFS path; armory and hoplite both bump 0.1.0 → 1.0.0; README rewrites around hoplite as agentic note-taking and knowledge graph.
document:
  tags: [journal, hoplite, tests, release, readme, milestone]
  created: 2026-05-25
---

# Traverse tests, version bump to 1.0.0, README rewrite

Focused unit tests for `tools.traverse_nodes` land; self-loop and mid-graph cycle coverage close gaps in the BFS path; armory and hoplite both bump 0.1.0 → 1.0.0; README rewrites around hoplite as agentic note-taking and knowledge graph.

## Intent

The runtime worked. The tests covered the leaf modules (parser, filter, MinHash, wikilinks, ids) but the tool surface — `match_nodes`, `traverse_nodes` — was tested only through smoke-style end-to-end calls. `traverse_nodes` in particular has graph-algorithm subtleties: cycles, self-loops, multi-edge paths, direction filtering. Each subtlety needed focused coverage.

Version bump to 1.0.0 follows. The 0.1.0 → 1.0.0 jump skips the usual prerelease ladder because the implementation isn't an experimental sketch — it is a working shape that has survived three major design pivots, is feature-complete for day-one, and has tests covering the critical paths.

README rewrite: the existing README still framed the package as a skills plugin for authoring. The thing that actually ships is a knowledge graph over markdown — that needs to be what the README says.

## What landed (chronological)

- 2026-05-25 18:11 — Hoplite: focused unit tests for `tools.traverse_nodes`. The BFS implementation gets its own test module separate from the smoke tests.
- 2026-05-25 18:16 — Traverse tests: add self-loop and mid-graph cycle coverage. The visited-set defense against cycles needs explicit coverage for the two interesting cycle shapes: a node with an edge to itself, and a cycle that the BFS reaches mid-walk.
- 2026-05-25 18:17 — Armory + hoplite: 0.1.0 → 1.0.0. Both `pyproject.toml` and the marketplace manifest bump. Same version on both because the marketplace ships them together.
- 2026-05-25 18:36 — README: rewrite around hoplite as agentic note-taking + knowledge graph. The README opens with what Hoplite is; the install steps stay near the top; the skill list comes after.
- 2026-05-25 18:44 — Three small commits in a minute: "tests", "idea", "rename". Final polish.

## Decisions captured

- 1.0.0 means feature-complete for day-one, not bug-free. The day-one feature set is settled: 4 MCP tools, in-memory graph, frontmatter contract, wikilinks, MinHash relatedness, FTS5 BM25, tag predicates. Bugs will come up; they get fixed in 1.x. The version isn't a maturity claim, it's a stability-of-shape claim.
- Self-loops and mid-graph cycles each get explicit tests. The BFS visited-set handles both, but a test that exercises only one of them leaves the other to a manual review pass that may not run.
- The README is the front door. A user landing on the GitHub page sees the README before anything else. That artifact needs to lead with what Hoplite does, not with how to install the plugin or which skills it ships.
- Same version across plugin and package. The plugin pins the package; bumping the package without bumping the plugin breaks the dependency. Lockstep versioning keeps the two in sync mechanically.

## Cross-references

- `[[journal/2026-05-25-1137-eav-property-graph-refactor]]` — the EAV shape these tests cover.
- `[[journal/2026-05-25-1724-fts5-rowid-bug-and-timestamped-dumps]]` — the bug fix that preceded this.

## Next

The hoplite SKILL.md extracts to a component injected into the authoring skills; armory renames to hoplite as the project starts to spin out of the Claude repo into its own home. See `[[journal/2026-05-25-1934-skill-md-to-component-and-the-repo-split]]`.
