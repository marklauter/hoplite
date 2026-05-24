# MCP server design evaluation

Review of the `docs/mcp/` spec against `docs/mcp-skill/reference/mcp_best_practices.md` and `docs/mcp-skill/reference/python_mcp_servers.md`.

## Substantive gaps

### 1. Tool names lack a service prefix

The ten tools — `match`, `traverse`, `invoke`, `read`, `insert`, `update`, `index`, `delete`, `apply_framing`, `slugify` — are all generic verbs with no namespace. Best practices are explicit: "Use `slack_send_message` instead of just `send_message`." Three of these will collide hard:

- `read` is the name of Claude Code's built-in file-read tool.
- `index` is heavily overloaded across MCP servers.
- `delete` / `update` / `insert` are generic enough to clash with any DB-flavored server.

Recommend a prefix like `graph_` or `kg_` across the board (`graph_match`, `graph_invoke`, `graph_read`, etc.). This is the single biggest interop risk in the spec.

### 2. Response format option missing

The reference says every list/data tool should support `response_format: "json" | "markdown"`. The contracts define structured types (`Landing`, `TraversalHit`, `FetchedNode`) but say nothing about MCP wire format. For `invoke` / `read` specifically, the envelope composition is text-shaped and probably wants markdown by default; `match` / `traverse` results probably want JSON by default. Worth stating explicitly per tool.

### 3. Error-model boundary isn't mapped to MCP

`behavior.md` distinguishes invariants (throw) from constraints (ErrorOr result). At the MCP boundary, both need to become `isError: true` content responses — raising exceptions surfaces as JSON-RPC protocol errors, which best practices say to avoid ("Report tool errors within result objects"). Add a sentence: the MCP adapter catches thrown invariants and converts them, alongside ErrorOr results, into structured error content.

### 4. Server name not declared

Python convention is `{service}_mcp`. The spec calls this "the MCP graph runtime" but never picks a module name. Pick one (`graph_mcp`, `kg_mcp`) and put it in the implementation doc.

## Smaller items

- **Path-traversal safety** is structurally enforced by the segment regex (`[a-z0-9-]` excludes `.`, so `..` segments can't form), but worth one explicit sentence in `behavior.md` claiming this property — easier for a reviewer to verify than to derive.
- **`slugify` as a tool** is pure and trivial; the agent can do it inline. The argument for keeping it is "canonical implementation == server validator." Fine to keep, but worth a one-line justification.
- **Transport** isn't specified. Day-one is local single-user single-corpus — stdio is the obvious fit. State it.
- **Lifespan / connection management.** The PRAGMA-on-open requirement plus FTS5 implies a persistent connection. The Python guide's `lifespan=app_lifespan` pattern is the right shape; worth a sentence in the implementation doc.
- **Progress reporting on `index`.** A bulk soft-reindex (the documented "walk docs/ and call `index` per file" workflow) is the one place where `ctx.report_progress` would matter. Optional but cheap.

## What's well-shaped

- Strategic tool design (verbs for complete workflows, not endpoint wrappers) is exactly what the best practices push for.
- The invoke/read split as an intent declaration is a clean abstraction that maps well to LLM behavior.
- ACID write semantics + temp-and-rename for cross-boundary atomicity is the right call.
- The contract/implementation split keeps the spec robust to substrate changes.
