## Code composition — principles that cross all languages

Apply to new code. Existing code updates to match when touched.

- Make invalid states unrepresentable — the type system is the first line of defense. Construction is where invariants land; downstream code trusts the value.
- Immutable by default — values, not state. Mutation is a deliberate carve-out, justified by a measured hot path or a domain concept that models change in place.
- Pure functions at the core, I/O at the boundary — push side effects to the entry point. Pure functions test by reading; impure functions need fixtures and fakes, and the ceremony signals the design wants to be purer.
- Domain failures as values; bugs as exceptions — named outcomes (`NotFound`, `Conflict`, `InvalidInput`) ride in a Result-shaped carrier appropriate to the language. Exceptions carry bugs and infrastructure failures the caller has no path to act on.
- Fail loud when prevention fails — when a bad state slips past, crash immediately. A loud failure beats silent corruption.
- Persistence ignorance — domain types describe meaning. Storage, serialization, and wire formats live behind adapter layers; they stay out of domain shapes.
- Performance where it matters — measure hot paths and optimize them. Cold paths stay readable. The discipline is knowing which is which.
- Build gates are signal — warnings, type errors, and failing tests are ground truth. Fix what triggered the gate; suppression carries explicit justification at the site.
- The first slice sets the pattern — the first instance teaches the next ten. Invest disproportionate care in the canonical example.
- One source of truth — every fact has one authoritative home. Duplicated knowledge is a defect waiting to surface.
- The easy path is the correct path — make the right thing the path of least resistance. Friction in front of a risky operation buys a beat of attention.
