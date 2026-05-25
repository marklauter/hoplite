#!/usr/bin/env bash
# Minimal bash test runner for the skills plugin.
#
# Usage:
#   run-tests.sh                     # discover and run every *_test.sh under the plugin
#   run-tests.sh <path>...           # run tests in the given files or directories
#   NO_COLOR=1 run-tests.sh          # disable ANSI colors
#
# Test file convention:
#   - File names end in _test.sh.
#   - Each test is a function named test_<something>.
#   - Optional setup() runs before each test; teardown() runs after.
#   - Each test runs in a subshell with cwd set to a fresh tmpdir and
#     $PLUGIN_ROOT exported for absolute references to scripts under test.
#   - A test fails if any command exits non-zero (the test runs with `set -e`).
#
# Assertions (all return non-zero on failure, which aborts the test under set -e):
#   assert_equal         <expected> <actual> [<msg>]
#   assert_contains      <haystack> <needle> [<msg>]
#   assert_not_contains  <haystack> <needle> [<msg>]
#   assert_match         <string>   <regex>  [<msg>]
#   assert_exit_code     <expected> <actual> [<msg>]
#   assert_file_exists   <path>              [<msg>]
#   assert_file_not_exists <path>            [<msg>]

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export PLUGIN_ROOT

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
    C_RED=$'\033[31m'
    C_GREEN=$'\033[32m'
    C_GRAY=$'\033[90m'
    C_RESET=$'\033[0m'
else
    C_RED=""; C_GREEN=""; C_GRAY=""; C_RESET=""
fi

PASS_COUNT=0
FAIL_COUNT=0
FAIL_LIST=()

# ---- assertions ----

assert_equal() {
    local expected="$1" actual="$2" msg="${3:-}"
    if [ "$expected" != "$actual" ]; then
        printf '  %sFAIL%s: expected %q, got %q' "$C_RED" "$C_RESET" "$expected" "$actual" >&2
        [ -n "$msg" ] && printf ' — %s' "$msg" >&2
        printf '\n' >&2
        return 1
    fi
}

assert_contains() {
    local haystack="$1" needle="$2" msg="${3:-}"
    case "$haystack" in
        *"$needle"*) return 0 ;;
    esac
    printf '  %sFAIL%s: expected output to contain %q\n  ----\n%s\n  ----' "$C_RED" "$C_RESET" "$needle" "$haystack" >&2
    [ -n "$msg" ] && printf ' — %s' "$msg" >&2
    printf '\n' >&2
    return 1
}

assert_not_contains() {
    local haystack="$1" needle="$2" msg="${3:-}"
    case "$haystack" in
        *"$needle"*)
            printf '  %sFAIL%s: expected output to NOT contain %q\n  ----\n%s\n  ----' "$C_RED" "$C_RESET" "$needle" "$haystack" >&2
            [ -n "$msg" ] && printf ' — %s' "$msg" >&2
            printf '\n' >&2
            return 1 ;;
    esac
}

assert_match() {
    local string="$1" regex="$2" msg="${3:-}"
    if ! [[ "$string" =~ $regex ]]; then
        printf '  %sFAIL%s: expected %q to match /%s/' "$C_RED" "$C_RESET" "$string" "$regex" >&2
        [ -n "$msg" ] && printf ' — %s' "$msg" >&2
        printf '\n' >&2
        return 1
    fi
}

assert_exit_code() {
    local expected="$1" actual="$2" msg="${3:-}"
    if [ "$expected" != "$actual" ]; then
        printf '  %sFAIL%s: expected exit code %s, got %s' "$C_RED" "$C_RESET" "$expected" "$actual" >&2
        [ -n "$msg" ] && printf ' — %s' "$msg" >&2
        printf '\n' >&2
        return 1
    fi
}

assert_file_exists() {
    local path="$1" msg="${2:-}"
    if [ ! -e "$path" ]; then
        printf '  %sFAIL%s: expected file %q to exist' "$C_RED" "$C_RESET" "$path" >&2
        [ -n "$msg" ] && printf ' — %s' "$msg" >&2
        printf '\n' >&2
        return 1
    fi
}

assert_file_not_exists() {
    local path="$1" msg="${2:-}"
    if [ -e "$path" ]; then
        printf '  %sFAIL%s: expected file %q to NOT exist' "$C_RED" "$C_RESET" "$path" >&2
        [ -n "$msg" ] && printf ' — %s' "$msg" >&2
        printf '\n' >&2
        return 1
    fi
}

# ---- discovery ----

discover() {
    if [ $# -eq 0 ]; then
        find "$PLUGIN_ROOT" -name '*_test.sh' -type f 2>/dev/null | sort
        return
    fi
    local arg
    for arg in "$@"; do
        if [ -d "$arg" ]; then
            find "$arg" -name '*_test.sh' -type f 2>/dev/null | sort
        elif [ -f "$arg" ]; then
            printf '%s\n' "$arg"
        else
            printf 'run-tests.sh: not found: %s\n' "$arg" >&2
            return 2
        fi
    done
}

# ---- runner ----

reset_test_functions() {
    # Unset all test_*, setup, teardown from the current shell so each
    # sourced file starts clean. Required because the runner sources tests
    # into its own shell rather than per-file subshells (so it can read the
    # function list back).
    local fn
    while IFS= read -r fn; do
        unset -f "$fn" 2>/dev/null || true
    done < <(declare -F | awk '/^declare -f (test_|setup$|teardown$)/ {print $3}')
}

run_test_file() {
    local file="$1"
    printf '%s%s%s\n' "$C_GRAY" "$file" "$C_RESET"
    reset_test_functions
    # shellcheck disable=SC1090
    source "$file"

    local fn rc tmp
    while IFS= read -r fn; do
        tmp="$(mktemp -d)"
        (
            set -e
            cd "$tmp"
            if declare -F setup >/dev/null; then setup; fi
            "$fn"
            if declare -F teardown >/dev/null; then teardown; fi
        )
        rc=$?
        rm -rf "$tmp"
        if [ "$rc" = "0" ]; then
            printf '  %s✓%s %s\n' "$C_GREEN" "$C_RESET" "$fn"
            PASS_COUNT=$((PASS_COUNT + 1))
        else
            printf '  %s✗%s %s\n' "$C_RED" "$C_RESET" "$fn"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            FAIL_LIST+=("$file::$fn")
        fi
    done < <(declare -F | awk '/^declare -f test_/ {print $3}')
}

main() {
    local files=()
    while IFS= read -r f; do
        files+=("$f")
    done < <(discover "$@")

    if [ ${#files[@]} -eq 0 ]; then
        echo "no tests found"
        exit 0
    fi

    local file
    for file in "${files[@]}"; do
        run_test_file "$file"
    done

    printf '\n----\n'
    if [ "$FAIL_COUNT" = "0" ]; then
        printf '%sall passed%s: %d test(s)\n' "$C_GREEN" "$C_RESET" "$PASS_COUNT"
        exit 0
    fi
    printf '%sFAILED%s: %d failed, %d passed\n' "$C_RED" "$C_RESET" "$FAIL_COUNT" "$PASS_COUNT"
    local f
    for f in "${FAIL_LIST[@]}"; do
        printf '  - %s\n' "$f"
    done
    exit 1
}

main "$@"
