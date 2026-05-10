---
name: writing-csharp
description: Use when writing, refactoring, or reviewing C# or .NET code. Covers idioms, type-driven design, immutability, functional patterns, error handling with Result types, persistence ignorance, and modern language features.
---

# Writing C#

Philosophy, guidance, and validation for idiomatic C# and .NET code.

## Philosophy

These principles draw on several orienting threads. Evans for domain-driven design, boundaries between meaning and storage, ubiquitous language, and modeling the domain as types. Donald Norman for affordances, signifiers, and forcing functions — the world shapes behavior.

Minsky on making illegal states unrepresentable. Hickey on values, immutability, the distinction between simple and easy, and state representation as a series of events. Brooks on essential versus accidental complexity. Kernighan and Pike on the rule of clarity.

They describe what good code looks like. They apply to new code without exception; existing code is updated to match when it's touched, not chased preemptively.

### Make invalid states unrepresentable

The type system is the first line of defense, not a fallback. Construction is where invariants land — once a value exists, it is trustworthy, and downstream code does not re-verify what construction already guaranteed. Lean on the compiler to rule out the wrong thing entirely; runtime checking is for what types cannot express. Parse, don't validate. Make the incorrect inexpressible.

### Immutable by default

Default to immutable — Hickey's values-not-state stance. Mutation is a deliberate carve-out, justified by a measured hot path or a domain concept that genuinely models change in place. It is never the path of least resistance.

### Pure functions over procedures

Push side effects to the boundary; keep the interior computational. Pure functions are testable by reading them. Impure functions require fixtures, fakes, and mocks — and that ceremony is a signal that the design wants to be purer than it currently is.

### Results, not exceptions

If you can name the outcome — `NotFound`, `Conflict`, `InvalidInput` — it is not exceptional, it is a result variant. Exceptions are reserved for bugs and conditions no caller can sensibly handle. Use the real functional vocabulary: `Option`, `Either`, `bind`, `map`.

### Fail loud when prevention fails

The first defense is making bad states unreachable. When something slips past anyway, the system crashes immediately with a stack trace — Armstrong's let-it-crash, applied at function granularity. A loud failure beats silent data corruption every time, and quietly swallowing an unexpected condition is worse than either.

### The domain doesn't know how it's stored

Domain types describe meaning. If a reader can reverse-engineer the database, ORM, or wire format from a domain type, that is a leak — Evans's persistence ignorance, taken seriously. Persistence concerns live in their own layer and do not colonize the model.

### Inference, not annotation

`var` is the default. Clarity comes from good names — for variables, methods, and types — not from re-stating types the compiler already knows. Annotations the reader could derive at a glance are noise.

### Modern idioms

New code uses the newest stable language features: records, pattern matching, primary constructors, collection expressions, file-scoped namespaces, expression-bodied members, required members, raw string literals. Older syntax exists for backward compatibility with existing code, not as a stylistic option for new code.

### Performance where it matters

Hot paths get measured and optimized — allocations, branches, layout, all of it. Cold paths stay readable. The discipline (per Knuth) is knowing which is which and not pretending every method is in the inner loop.

### Build gates are signal

Warnings, analyzers, nullability, tests, type checks — these tighten the feedback loop. Suppressing a gate to ship is self-harm dressed up as productivity. Fix what triggered the gate; suppression is a last resort that requires explicit acknowledgment.

### The first slice sets the pattern

The first implementation of a pattern becomes the example the next ten will copy, whether or not that was intended. Invest disproportionate care in the first instance — it teaches by existing.

### One source of truth

Every fact has exactly one authoritative representation. When the fact changes, one place changes. Duplicated knowledge — copy-pasted code, parallel hierarchies, values restated in both code and config — is a defect waiting to surface.

### The easy path is the correct path

The right thing is the path of least resistance; the dangerous thing takes real effort. Norman's affordances and forcing functions, in code form. Friction in front of a risky operation buys a beat of attention, and that pause is the whole point.

## Guidance

_Concrete patterns, idioms, and rules go here. Drafted next._

## Validation

"Testing shows the presence of bugs, not their absence" (Dijkstra). Validation in this codebase is layered: types prevent what types can prevent, tests catch what slips through, and the build gates keep both honest. The discipline is using each layer for what it does well, and not asking any one of them to carry the others.

_Concrete validation steps and checks go here. Drafted last._
