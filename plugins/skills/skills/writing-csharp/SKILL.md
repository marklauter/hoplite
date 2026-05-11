---
name: writing-csharp
description: Use when writing, refactoring, or reviewing C# or .NET code. Covers idioms, type-driven design, immutability, functional patterns, error handling with Result types, persistence ignorance, and modern language features.
---

# Writing C#

Philosophy, guidance, and validation for idiomatic C# and .NET code.

## Philosophy

These principles draw on several orienting threads. Evans for domain-driven design, boundaries between meaning and storage, ubiquitous language, and modeling the domain as types. Donald Norman for affordances, signifiers, and forcing functions — the world shapes behavior.

Minsky on making illegal states unrepresentable. Hickey on values, immutability, the distinction between simple and easy, and state representation as a series of events. Brooks on essential versus accidental complexity. Kernighan and Pike on the rule of clarity.

They describe what good code looks like. They apply to new code without exception; existing code is updated to match when it's touched.

### Make invalid states unrepresentable

The type system is the first line of defense, not a fallback. Construction is where invariants land — once a value exists, it is trustworthy, and downstream code does not re-verify what construction already guaranteed. Lean on the compiler to rule out the wrong thing entirely; runtime checking is for what types cannot express. Parse, don't validate. Make the incorrect inexpressible.

### Immutable by default

Default to immutable — Hickey's values-not-state stance. Mutation is a deliberate carve-out, justified by a measured hot path or a domain concept that genuinely models change in place.

### Pure functions over procedures

Push side effects to the boundary; keep the interior computational. Pure functions are testable by reading them. Impure functions require fixtures, fakes, and mocks — and that ceremony is a signal that the design wants to be purer.

### Results, not exceptions

If you can name the outcome — `NotFound`, `Conflict`, `InvalidInput` — it is not exceptional, it is a result variant. Exceptions are reserved for bugs and conditions no caller can sensibly handle. Use the real functional vocabulary: `Option`, `Either`, `bind`, `map`.

### Fail loud when prevention fails

The first defense is making bad states unreachable. When something slips past anyway, the system crashes immediately with a stack trace — Armstrong's let-it-crash, applied at function granularity. A loud failure beats silent data corruption.

### The domain doesn't know how it's stored

Domain types describe meaning. If a reader can reverse-engineer the database, ORM, or wire format from a domain type, that is a leak — Evans's persistence ignorance, taken seriously. Persistence concerns live in their own layer and do not colonize the model.

### Inference, not annotation

`var` is the default. Clarity comes from good names — for variables, methods, and types — not from re-stating types the compiler already knows. Annotations the reader could derive at a glance are noise.

### Modern idioms

New code uses the newest stable language features: records, pattern matching, primary constructors, collection expressions, file-scoped namespaces, expression-bodied members, required members, raw string literals.

### Performance where it matters

Hot paths get measured and optimized — allocations, branches, layout, all of it. Cold paths stay readable. The discipline (per Knuth) is knowing which is which and not pretending every method is in the inner loop.

### Build gates are signal

Warnings, analyzers, nullability, tests, type checks — these tighten the feedback loop and exist to help the agent. They are the ground truth between sessions, the most reliable signal that something is wrong before a human reviews. Disabling a gate erases that signal. Fix what triggered the gate; suppression is reserved for cases where the gate itself is wrong, with an explicit justification at the suppression site.

### The first slice sets the pattern

The first implementation of a pattern becomes the example the next ten will copy, whether or not that was intended. Invest disproportionate care in the first instance — it teaches by existing.

### One source of truth

Every fact has one authoritative representation. When the fact changes, one place changes. Duplicated knowledge — copy-pasted code, parallel hierarchies, values restated in both code and config — is a defect waiting to surface.

### The easy path is the correct path

The right thing is the path of least resistance; the dangerous thing takes real effort. Norman's affordances and forcing functions, in code form. Friction in front of a risky operation buys a beat of attention, and that pause is the whole point.

## Guidance

C#-specific patterns that operationalize the principles above. Each subsection mirrors a philosophy heading so the mapping is direct.

### Make invalid states unrepresentable

- `internal sealed` by default for records and concrete classes. `internal sealed record Range { ... }`. Promote to `public` only when the type is part of the library's exported contract.
- Public interfaces, internal implementations. Library exports a `public interface IFormatter`; the implementation is `internal sealed class MarkdownFormatter(FormatterOptions options) : IFormatter`. Consumers depend on the interface; the implementation is registered in the DI container. The public contract is mockable for tests because callers see only the interface.
- `required` for construction-time invariants. `public required int Start { get; init; }`. Every construction site is forced to set the property.
- `init` accessors only. Properties expose `init`, never `set`. Once constructed, the value is the value.
- Smart constructors via static factory methods. Keep the constructor private or internal; expose `public static Result<Range> Create(int start, int end)` that runs validation (e.g., `start <= end`). Once a `Range` exists, its invariants hold.
- `readonly record struct` for value-type wrappers. Wrap `string` → `FilePath`, `TimeSpan` → `Duration`, `decimal` → `Percent`. `public readonly record struct FilePath(string Value) : IValue<FilePath, string>`. Value semantics, no heap allocation, equality and `ToString` for free.
- `IValue<TSelf, TValue>` interface (CRTP). `public interface IValue<TSelf, TValue> where TSelf : IValue<TSelf, TValue>` — the wrapper carries both its self-type and the underlying primitive as generic parameters. Enables `static abstract Create` on the interface, generic constraints across all value objects, and shared helpers without runtime reflection.
- Discriminated unions for state machines. Model state as an abstract base record with sealed records per state (e.g., a `Connection` as `Disconnected`, `Connecting`, `Connected`, `Faulted`). Each state carries only the data valid in that state. Pattern match to handle.
- Nullable reference types enabled. `<Nullable>enable</Nullable>` in `Directory.Build.props`. `string` means non-null; `string?` is the explicit opt-in for absence.
- `NotNullWhen` / `MemberNotNull` attributes to carry nullability through helper methods and `Try*` patterns.

### Immutable by default

- `IReadOnlyList<T>` / `IReadOnlyDictionary<TK, TV>` as return types and field types for collections that should not be mutated by the consumer.
- `ImmutableArray<T>` / `ImmutableDictionary<TK, TV>` for shared snapshots and lookup tables.
- `with` expressions for non-destructive update of records: `range with { End = newEnd }`.
- `readonly` modifier on fields and on struct types. `readonly record struct` for value types that should be immutable end-to-end.
- `Unit` type (a `readonly record struct`) for fire-and-forget pipeline returns where no value is meaningful.

### Pure functions over procedures

- Static factory methods for composition. Pure factories take parameters, return a configured object, perform no I/O. Composition is a value, not an event.
- Imperative shell at the entry point. I/O (Console, file system, network, database) lives in `Program.cs`, the controller, the host. The core layer takes data in and returns data out.
- `TimeProvider` injected instead of direct `DateTime.UtcNow` or `Stopwatch.GetTimestamp` calls. Time becomes testable and controllable.
- Static helpers for pure transformations (tokenize, normalize, parse, format). No state, no I/O, no logging — just data → data.
- Logging is opt-in via constructor injection. A pure transformation does not log; a middleware that needs to log declares `ILogger<T>` in its primary constructor and does so explicitly.

### Results, not exceptions

- ErrorOr for domain logic. Domain operations return `ErrorOr<T>`. Callers pattern match on success or error.
- Domain error enum (or sealed hierarchy) in the domain layer only. The named failure shapes the domain knows how to act on: `Gone`, `NotFound`, `Conflict`, `Validation`. Each carries the context needed to handle it.
- Adapters and ports throw. Database errors, network failures, file-system errors, deserialization failures, and any other infrastructure-layer failure throw. The domain layer does not see these directly.
- Infrastructure-only codebases lean on exceptions. A framework, library, or adapter codebase with no domain to model (e.g., a request-pipeline library) uses exceptions throughout — there is no domain layer for Results to inhabit. Apply Results where there is a domain to name failures in.
- Translation at the boundary. Adapters convert infrastructure exceptions into domain errors when the failure is something the domain can act on (e.g., row-not-found → `Gone`); they let true infrastructure failures propagate as exceptions to the host.
- Pattern match the result, do not unwrap blindly. `result.Match(value => ..., errors => ...)` over `result.Value` access. The compiler keeps both paths visible.

### Fail loud when prevention fails

- `ArgumentNullException.ThrowIfNull(param)` at every public API boundary. The failure names the parameter and stops the call dead.
- Distinguish exception types. `TimeoutException` for elapsed-time failures, `OperationCanceledException` for caller-initiated cancellation, `InvalidOperationException` for misuse of the API, `ArgumentException` / `ArgumentNullException` for bad inputs. Do not conflate them.
- Throw with named context. The exception message names what failed (which factory, which type, which step) so the stack trace explains itself without source diving.
- No catch-all handlers. Catch specific exception types you can act on; let everything else propagate.

### The domain doesn't know how it's stored

- No persistence or serialization attributes on domain types. No `[Table]`, `[Column]`, `[Key]`, `[ForeignKey]`, `[JsonPropertyName]`, `[DataMember]`, `[XmlElement]`. Mapping happens at the adapter boundary.

_Architectural treatment (bounded contexts, layer boundaries, mapper/DTO conventions) lives in the separate `writing-architecture` skill._

### Inference, not annotation

- `var` for locals when the right-hand side names the type. `var range = Range.Create(0, 10);`.
- Target-typed `new(...)` in initializers and assignments where the target type is declared: `Range range = new(0, 10);` or `List<Range> ranges = [new(0, 10), new(1, 20)];`.
- Collection expressions `[]` in place of `new List<T>()`, `Array.Empty<T>()`, and similar. `List<int> xs = [];`, `Data ??= [];`.
- Method return types are explicit. API boundary; the type is part of the contract.

### Modern idioms

- Primary constructors on services and middleware. `internal sealed class MarkdownFormatter(FormatterOptions options) : IFormatter`. Captures immutable dependencies; no boilerplate constructor body.
- Records for data carriers. `internal sealed record FormatterOptions(...)` with primary constructor and static defaults.
- Collection expressions throughout. `[]`, `??= []`, `new(...)` in initializers, list patterns in `switch`.
- `with` expressions for non-destructive update of records.
- File-scoped namespaces. `namespace Foo.Bar;` at the top of every file.
- Raw string literals (`"""..."""`) for multi-line text, JSON fixtures, and SQL.
- Pattern matching with property patterns, list patterns, and relational patterns. `switch` expressions for branching on shape.
- Required members. `public required int Start { get; init; }` in place of constructor-validated invariants where the property genuinely must be set.
- `LangVersion` set centrally in `Directory.Build.props` so every project has the same toolbox.

### Performance where it matters

- `readonly record struct` for small value types. Value semantics without heap allocation.
- `TimeProvider` for monotonic, testable time over `DateTime.UtcNow` or `Stopwatch.GetTimestamp` direct calls. Avoids both correctness drift and test flakiness.
- Hot-path techniques available when measurement justifies them: `Span<T>` / `ReadOnlySpan<T>` for slicing without allocation, `ArrayPool<T>` for buffer reuse, `[SkipLocalsInit]` for stack-allocated locals, `ref struct` for stack-only types, struct layout attributes for tight memory packing. Reach for them when a benchmark says to.
- `ValueTask<T>` for hot async paths where the awaited work often completes synchronously.
- Benchmark with BenchmarkDotNet before optimizing. Cold paths stay readable.

### Build gates are signal

- `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>` in `Directory.Build.props`. A warning that survives is a failure that gets investigated immediately.
- `<Nullable>enable</Nullable>` in `Directory.Build.props` so every project inherits it.
- `<AnalysisMode>All</AnalysisMode>` and `<AnalysisLevel>latest-all</AnalysisLevel>` in `Directory.Build.props`. The strictest analyzer set against the latest language version.
- Analyzer packs via `GlobalPackageReference` in `Directory.Packages.props` so every project picks them up automatically. No per-project drift.
- ArchUnitNET tests as structural gates. Architectural invariants — sealed concrete classes, no public instance fields, namespace shape, layer dependencies, constructor visibility — encoded as xUnit tests. Drift trips the build.
- Coverage threshold ratchet in `Directory.Build.props`. Line, branch, and method coverage minimums as MSBuild properties. Start at zero, measure the current value, lock the threshold in at that value, and ratchet up as coverage grows. The gate moves forward only.

### The first slice sets the pattern

- ArchUnitNET tests encode the canonical pattern. When a new architectural rule is established (sealed concrete classes, namespace shape, forbidden references, immutability requirements), an ArchUnit test enforces it. Every subsequent slice is checked against the rule on every build.
- The first instance of a new domain concept gets extra review. Naming, layout, dependencies, lifetime. The shape it takes becomes the shape ten copies will take.
- Folder and file conventions are followed without negotiation. The first slice establishes them; following slices match.

### One source of truth

- Central Package Management (CPM). `<ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>`. Every package version declared once in `Directory.Packages.props`; project `.csproj` files reference packages by name only, no inline `Version=`.
- `<CentralPackageTransitivePinningEnabled>true</CentralPackageTransitivePinningEnabled>` so transitive dependencies cannot float and surprise the build.
- `GlobalPackageReference` in `Directory.Packages.props` for solution-wide analyzer and source-generator packs.
- `Directory.Build.props` for solution-wide MSBuild properties. Compiler flags (`LangVersion`, `Nullable`, `TreatWarningsAsErrors`, `AnalysisMode`), target framework, common properties. One declaration; every project inherits.
- `Directory.Build.targets` for solution-wide build targets. Shared build steps and conditional logic.
- Strongly-typed configuration via `IOptions<T>` or direct immutable record injection. Each configuration concept is one typed declaration; consumers receive the typed instance.
- Constants declared in one place per concept. Magic numbers and strings live in a named type, referenced everywhere they apply.

### The easy path is the correct path

- Primary constructors for DI. The easy thing — declare a parameter — is the correct thing — capture an immutable dependency. No boilerplate constructor body.
- Fluent builders with `WithX()` extension methods. `WithServices(...)`, `WithConfiguration(...)`, `WithInMemorySettings(...)`, and similar. The right configuration path is a chain of `WithX` calls; deviation requires writing a custom builder.
- DI ownership tracked alongside construction. When a factory creates a resource it owns, an internal flag tracks ownership so disposal lives in the same place as construction. `using var x = Factory.Create(...);` disposes correctly without the caller thinking about it.
- ArchUnitNET tests as forcing functions. When a structural rule is encoded as a test, deviation is harder than compliance — the build fails the moment someone tries.
- Static factory methods over public constructors for types with validation invariants. The factory runs validation and returns the result; the public constructor is unavailable.

## Validation

"Testing shows the presence of bugs, not their absence" (Dijkstra). Validation is layered: types prevent what types can prevent, tests catch what slips through, and the build gates keep both honest. Each layer carries the load it can carry.

The golden rule: test what you own. The framework, the ORM, and the third-party libraries beneath this code have their own test suites. This codebase's tests cover this codebase's logic.

### The validation loop

Run the build script to validate format, build, and test. One command, one three signals.

1. Format (always solution-wide). `dotnet format --verify-no-changes --severity info --verbosity quiet`. Style drift anywhere is a defect; the agent never merges unscoped drift even when iterating on one layer.
2. Build. `dotnet build --nologo --verbosity quiet`. Scope depends on args.
3. Tests. `dotnet test --nologo --verbosity quiet --logger "console;verbosity=minimal"`. Pass/fail counts and failed-test names. Scope depends on args. `dotnet test` builds dependencies implicitly, so when only a test target is given the explicit build step is skipped — `dotnet test` covers it.

Each step runs only when the prior is green. The script's exit code is the gate.

Output discipline: each step captures stdout and stderr. On success only the `==> step-name` label prints. On failure the captured output prints and the script exits with the command's code. Anything beyond the `==>` labels and a final `==> green` is failure output.

The canonical script ships at `${CLAUDE_PLUGIN_ROOT}/skills/writing-csharp/scripts/build.sh`. Portable POSIX bash; runs on Linux, macOS, and Windows (Git Bash, WSL). Claude Code sets `${CLAUDE_PLUGIN_ROOT}` to the plugin's install path; the agent invokes the script from the consuming project's root, and the shell's working directory determines which solution gets operated on. The script lives outside any consuming repo, so an in-repo edit cannot silently neuter the gate.

Arguments scope build and test:

- `build.sh` — solution-wide: format, build, and test.
- `build.sh <test-target>` — solution-wide format, then test scoped. The explicit build step is skipped; `dotnet test` builds dependencies (transitively including the project under test).
- `build.sh <build-target> <test-target>` — solution-wide format, then build and test each scoped. Use when the test target is not the conventional `<X>.Tests` paired with `<X>`.

Each target accepts anything `dotnet` accepts: a project name, a `.csproj` path, or a `.sln` path.

### Gate policies

When a gate fires, the rule is: fix the underlying cause. Suppression and exclusion are policy-controlled.

- Suppression scope hierarchy. Order of preference: `#pragma warning disable` around the offending lines → `[SuppressMessage(..., Justification = "...")]` attribute on a member → `<NoWarn>` in the project `.csproj` → `<NoWarn>` in `Directory.Build.props`. Push suppressions as close to the offending code as possible.
- `[SuppressMessage]` always carries a `Justification`. An unjustified suppression is a defect.
- Solution-wide `<NoWarn>` in `Directory.Build.props` uses `<NoWarn>$(NoWarn);1234;5678</NoWarn>` and must be preceded by one comment per warning:

  ```xml
  <!-- 1234 warn-description : justification -->
  <!-- 5678 warn-description : justification -->
  <NoWarn>$(NoWarn);1234;5678</NoWarn>
  ```

  One comment block per line. A suppression without its accompanying comment block is a defect.
- `#pragma warning disable` always carries a comment explaining what and why, paired with an explicit `#pragma warning restore` at the end of the affected scope.
- Hints and warnings may be suppressed when the rule legitimately does not apply to the local context or fires a false positive, with `Justification`.
- Errors are suppressed only with an explicit ticket and team acknowledgment in addition to the `Justification`.
- Coverage exclusion via `[ExcludeFromCodeCoverage]` requires a comment naming the reason. Acceptable: generated code (source generators, OpenAPI clients, EF migrations), trivial constant types, platform-specific code unreachable in CI. Hand-written logic is tested, not excluded.

### Tooling

- xUnit v3 as the test runner. `[Fact]` and `[Theory]` attributes; async tests named `*Async`.
- `TestContext.Current.CancellationToken` propagated into every async test so cancellation works correctly under the test runner's lifecycle.
- ArchUnitNET tests run as xUnit tests. The test runner is the gate that fires on architectural drift.
- One test project per implementation project, namespaces mirrored along the DDD onion. `Domain` → `Domain.Tests`; `Domain.PortX` → `Domain.PortX.Tests`; `Domain.PortX.AdapterY` → `Domain.PortX.AdapterY.Tests`.
- Coverage scoped per test project via `<Include>` in the test project's settings. `Domain.PortX.Tests` produces coverage for `Domain.PortX` only. Per-layer coverage numbers stay meaningful, and the ratchet applies layer by layer.

### Make invalid states unrepresentable

- Smart-constructor tests: each validation branch yields the correct error variant; `Create` returns success only for valid input.
- ArchUnitNET: validated types expose no public parameterless constructor.

### Immutable by default

- ArchUnitNET: no public instance fields; concrete domain types are sealed records or `readonly record struct`.
- A `set;` in domain code is a smell. Analyzer or grep flags it.
- Tests verify `with` expressions return new instances; the original is unchanged.

### Pure functions over procedures

- A test that needs fixtures, mocks, or async setup signals the function is not pure.
- ArchUnitNET: domain-layer assemblies do not reference `System.IO`, `System.Net.*`, `Microsoft.EntityFrameworkCore`, or `Microsoft.Extensions.Logging` directly.

### Results, not exceptions

- A domain signature returning `T` that throws for domain failures is a defect.
- Domain-layer tests pattern match the result; absence of `try`/`catch` is the sign.
- ArchUnitNET: throwing methods exist only at adapter boundaries.

### Fail loud when prevention fails

- Boundary tests verify `ArgumentNullException.ThrowIfNull(...)` fires for each public parameter.
- ArchUnitNET: `catch (Exception)` without re-throw is forbidden outside the host's outermost handler.
- Tests assert exception message content includes the named context (which factory, which type, which step).

### The domain doesn't know how it's stored

- ArchUnitNET: domain assembly references zero of `Microsoft.EntityFrameworkCore.*`, `Dapper`, `Marten`, `Microsoft.Azure.Cosmos`, `System.Text.Json.Serialization.*Attribute`, `System.Runtime.Serialization`.
- The domain test project references no serializer; round-trip tests live in the adapter project.

### Inference, not annotation

- Analyzer IDE0007 (use `var`) at `warning` or `error` in `.editorconfig`.
- `.editorconfig` rules: `csharp_style_var_for_built_in_types`, `csharp_style_var_when_type_is_apparent`, `csharp_style_var_elsewhere` set to `true:warning`.

### Modern idioms

- Analyzers enabled at `warning` or `error`: IDE0028 (collection initializer), IDE0090 (`new()`), IDE0300–IDE0305 (collection expression), IDE0161 (file-scoped namespace), and the rest of the IDE0* modernization family.

### Performance where it matters

- BenchmarkDotNet project with regression thresholds. CI flags a benchmark whose mean or allocation crosses the configured budget.
- CA18xx performance analyzers enabled: CA1827 (use `Any` over `Count() > 0`), CA1829 (use `Length`/`Count` property), CA1845 (span-based concat), and others.

### Build gates are signal

- The validation-loop script is the agent's primary signal source — one tool call, one exit code.
- Gates exist to provide feedback to the agent. Disabling one is tantamount to self-harm — the protection vanishes along with the noise. Use them wisely.

### The first slice sets the pattern

- ArchUnitNET rule ships in the same change set as the first instance of the pattern.
- Code review on the first slice is deeper than on subsequent slices.

### One source of truth

- CPM with `<CentralPackageTransitivePinningEnabled>true</CentralPackageTransitivePinningEnabled>` — the build fails if a project declares its own package version.
- Duplicated literal values across files are flagged at review.

### The easy path is the correct path

- ArchUnitNET: services in DI-managed assemblies declare dependencies via primary constructor.
- Fluent builders are tested for chain validity — a builder test fails when the canonical `WithX` chain breaks.
