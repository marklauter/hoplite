# Write the writing-architecture skill

Tags: todo,skills,csharp,architecture
Architectural concerns scoped out of writing-csharp deserve their own skill — persistence ignorance, layer boundaries, bounded contexts, adapter patterns.

## Observation

Pre-draft rules captured in memory (originally at `project_writing_architecture_rules.md`, now consolidated here):

- **Persistence ignorance** is in `writing-csharp` Philosophy ("the domain doesn't know how it's stored") because philosophy is language-agnostic and applies everywhere. The deeper architectural treatment belongs in `writing-architecture`: bounded contexts, layer boundaries, mapper/DTO conventions, where adapters live, repository patterns. In `writing-csharp` Guidance, only the C#-specific surface rule was included: no persistence or serialization attributes on domain types.

- Mark's framing: the architect (and possibly the agent) devises the plan; the developer follows it. Architecture-scale decisions are a separate skill from idiomatic language use.

## Interpretation

Likely scope for `writing-architecture`:

- Persistence ignorance fully elaborated — adapter/port boundaries, mapper/DTO conventions, repository placement.
- Dependency direction — clean / hexagonal / onion patterns.
- Bounded contexts and anti-corruption layers.
- Integration patterns (sync vs async, choreography vs orchestration).
- Deployment topology where it shapes the code (service boundaries, shared databases).

Cross-references:

- `writing-csharp` for C#-specific manifestations (no `[Table]` on domain types, etc.) so the two skills compose without duplication.
- `reviewing-csharp` and a future `reviewing-architecture` skill would judge against this rubric.

## Next

- Draft the skill following the canonical four-section structure (intro → Philosophy → Guidance → Validation).
- Decide whether a `reviewing-architecture` skill ships at the same time (architecture findings would slot into the existing `.findings/` shape with a new `--type architecture` and possibly a lens vocabulary).
- After it ships, the memory `project_writing_architecture_rules.md` can be deleted — its content lives here now and the skill itself becomes the authoritative source.
