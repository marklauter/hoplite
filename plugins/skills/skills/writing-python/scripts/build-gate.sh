#!/usr/bin/env bash
# Validation loop for writing-python.
# format check -> lint -> type check -> tests, fail fast.
#
# Output discipline:
#   - format / lint / type: silent on success, captured output on failure.
#   - test: emits the pytest summary line(s) on success, full captured output on failure.
#
# Usage:
#   build-gate.sh                            project-wide: format, lint, type, test
#   build-gate.sh <pytest-target>            project-wide format / lint / type; test scoped
#
# pytest targets accept anything pytest accepts: a path, a node id, or a -k expression.

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

if [ ! -f "pyproject.toml" ]; then
    echo "build-gate: pyproject.toml missing in $PWD" >&2
    echo "  cd into the project root, then re-run." >&2
    exit 2
fi

ARG1="${1:-}"

run_step() {
    local label="$1"
    shift
    echo "==> $label"
    local output
    output=$("$@" 2>&1) || { local code=$?; echo "$output"; exit $code; }
}

test_step() {
    local label="$1"
    shift
    echo "==> $label"
    local output
    output=$("$@" 2>&1) || { local code=$?; echo "$output"; exit $code; }
    echo "$output" | grep -E "^=+.*(passed|failed|skipped|error)" | tail -5 || true
}

run_step "format (ruff)" ruff format --check
run_step "lint (ruff)"   ruff check
run_step "types (pyright)" pyright

if [ -z "$ARG1" ]; then
    test_step "test" pytest
else
    test_step "test $ARG1" pytest "$ARG1"
fi

echo "==> green"
