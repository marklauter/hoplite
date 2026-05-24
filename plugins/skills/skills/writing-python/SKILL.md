---
name: writing-python
description: Use when writing, refactoring, or reviewing Python. Covers pragmatic-functional idioms, frozen dataclasses, pattern matching, comprehensions, type hints with Protocol, error handling, src/tests layout, and modern tooling (ruff, pyright, pytest, uv).
---

# Writing Python

Pragmatic-functional Python: frozen dataclasses for records, pattern matching for sum-type dispatch, comprehensions and `itertools` for transforms, small pure functions at the core, I/O at the boundary, ruff and pyright and pytest as the gate.

!`cat ${CLAUDE_PLUGIN_ROOT}/components/writing-code/writing-code.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`

The sections below render those principles in Python's vocabulary.

## Pragmatic-functional over pure-functional

Python rewards a hybrid style. The runtime treats purity as discipline rather than constraint. Recursion runs on a fixed-depth stack. Lambdas accept a single expression. The type system covers first-order generics. Porting F# or Haskell idioms into Python yields code that reads as foreign to other Python developers and fights the language at every turn.

The pragmatic stance:

- Frozen dataclasses for records.
- Pattern matching (`match` / `case`) for sum-type dispatch.
- Small pure functions at the core; I/O at the boundary.
- Comprehensions and `itertools` for transforms.
- `Result` and `Option` containers from `expression` or `returns` where Result discipline earns its keep — parser error chains, multi-step pipelines with cascading failure. Elsewhere, raise a specific exception (for bugs) or return `T | None` (for absence).

This style captures most of the correctness benefit of pure FP while staying inside the language the rest of the team reads fluently.

## Records and types

- `@dataclass(frozen=True, slots=True)` for immutable records. `frozen=True` blocks reassignment; `slots=True` cuts memory and rejects ad-hoc attributes.
- `NamedTuple` for tuple-shaped records where positional access matters.
- `Enum` for closed sets of constants. `StrEnum` (3.11+) when the values round-trip as strings.
- Tagged unions as sibling frozen dataclasses; the union type is `Foo | Bar | Baz`; dispatch with `match`.
- `Protocol` for structural typing — any type with the matching shape satisfies it.
- `NewType` for thin wrappers around primitives: `UserId = NewType("UserId", int)`.
- `Literal` for narrow string or int constants.
- `Final` for module-level constants.
- `TypeAlias` (3.10+) or the `type` statement (3.12+) for named complex types.
- Type hints on every function signature. `T | None` over `Optional[T]` post-3.10.
- Run `pyright` in strict mode so the hints stay honest under the gate.

## Functions and control flow

- Comprehensions for the common transform: `[f(x) for x in xs if pred(x)]`.
- Generator expressions for lazy streams: `sum(x * x for x in xs)` allocates no intermediate list.
- `itertools` for streaming pipelines — `chain`, `groupby`, `takewhile`, `accumulate`.
- `functools.reduce` for folds, `functools.partial` for partial application, `functools.cache` and `functools.lru_cache` for memoization.
- The `operator` module supplies function forms of operators (`operator.add`, `operator.itemgetter`).
- Pattern matching over `isinstance` chains — structural destructure, attribute matching, list patterns, guards.
- Keyword-only arguments for boolean and configuration flags: `def fetch(*, force: bool = False):` — the call site reads `fetch(force=True)`.
- Resolve mutable defaults inside the body: `def f(items: list[str] | None = None): items = items or []`.
- Context managers (`with`) for resources that open and close. Author your own with `contextlib.contextmanager`.
- For loops iterate the collection directly: `for item in items:`, or `for i, item in enumerate(items):` when the index matters.
- Replace deep recursion with `while` or `functools.reduce`. Python evaluates calls without TCO.

## Project layout

- `src/<package>/` for library code, `tests/` peer to `src/`, `pyproject.toml` at the root.
- `pyproject.toml` carries `[build-system]`, `[project]`, `[project.optional-dependencies]`, `[tool.pytest.ini_options]`, `[tool.ruff]`, and `[tool.pyright]` in one file.
- Dev dependencies live in an `optional-dependencies` extra (`dev = [...]`), installed via `pip install -e .[dev]` or `uv pip install -e .[dev]`.
- `__init__.py` in every package directory makes the package unambiguous.
- One module per cohesive responsibility. Split when the module passes ~400 lines or carries unrelated concepts.
- `if __name__ == "__main__":` guard at the bottom of scripts so imports stay side-effect-free.

## Errors

- Exceptions carry bugs and infrastructure failures. Domain operations that fail meaningfully return values.
- Use the specific built-in: `ValueError`, `TypeError`, `KeyError`, `RuntimeError`. Custom exceptions inherit from the closest built-in — `class ParseError(ValueError): ...`.
- Return `T | None` for simple absence; a `Result[T, E]` container (`returns`, `expression`) for richer error vocabulary.
- Catch the specific exception type: `except FileNotFoundError:`. Catch-all handlers belong at the outermost host boundary only.
- Try the operation, catch the failure — Easier to Ask Forgiveness than Permission. `try: x.foo()` beats `if hasattr(x, "foo"): x.foo()`.
- Every `raise` inside `except` carries `from`: `raise ParseError("bad input") from exc`. The chain stays intact.

## Naming and style

- `snake_case` for functions, variables, and modules. `PascalCase` for classes. `UPPER_SNAKE` for module-level constants. `_leading_underscore` marks internal names.
- Imports group as stdlib, third-party, local; blank line between groups; sorted within each. `ruff` enforces.
- Single-character names appear inside comprehensions and lambdas only, where one line of context fixes the meaning (`i`, `x`, `k`, `v`).

## Testing

- `pytest` as the test runner. Plain `assert` with rewriting gives rich diffs.
- Tests live under `tests/` and mirror the package layout: `src/hoplite/parser.py` pairs with `tests/test_parser.py`.
- Fixtures via `@pytest.fixture`, requested by parameter name. Scope chosen by lifetime — function, module, session.
- `@pytest.mark.parametrize` for table-driven tests.
- `pytest-asyncio` for async tests with `asyncio_mode = "auto"` in `[tool.pytest.ini_options]`, so `async def test_*` runs without per-test decoration.
- `hypothesis` for property-based tests on parsers, serializers, and round-trip code.
- `syrupy` for snapshot tests when the output shape is the contract.
- Test the units you own. Frameworks, ORMs, and third-party libraries carry their own suites.

## Tooling

- `ruff` for lint and format — one tool replaces `black`, `flake8`, `isort`, and `pyupgrade`. Single config block in `pyproject.toml`.
- `pyright` for type checking in strict mode. `mypy` is the alternative; pick one and gate on it.
- `pytest` for tests; `pytest-asyncio`, `pytest-cov`, `hypothesis`, and `syrupy` as plugins.
- `uv` for dependency management — fast resolver, lockfile, replaces `pip`, `pip-tools`, and `virtualenv`.
- `pyproject.toml` as the single source of project config.

## Validation

The loop: format check → lint → type check → tests. Each step gates on the prior staying green.

1. `ruff format --check` — style drift surfaces as a defect.
2. `ruff check` — idiom violations and dead code.
3. `pyright` — type errors gate the build.
4. `pytest` — pass / fail counts and failed-test names.

The canonical script ships at `${CLAUDE_PLUGIN_ROOT}/skills/writing-python/scripts/build-gate.sh`. Bash, POSIX-portable, runs on Linux, macOS, and Windows (Git Bash, WSL).

### Gate policies

- Fix the underlying cause when a gate fires. Suppressions (`# noqa: E501`, `# type: ignore[arg-type]`) carry the rule code and a reason on the same line.
- Project-wide suppressions live in `pyproject.toml` (`[tool.ruff.lint] ignore = [...]`, `[tool.pyright] reportFoo = "none"`) with one comment per rule explaining the reason.
- Pin every `# noqa` to a specific rule code. Bare `# noqa` suppresses every check at the site.
- Tests stay green at merge.
