#!/usr/bin/env bash
# Validation loop for writing-csharp.
# format (solution-wide) -> build -> tests, fail fast, output only on failure.
#
# Each step's stdout+stderr is captured. On success the script emits only the
# step label. On failure it emits the captured output and exits with the
# command's exit code.
#
# Usage:
#   build.sh                                  whole solution: format, build, test
#   build.sh <test-target>                    solution-wide format; test scoped
#                                             (dotnet test builds the test target's
#                                             dependencies implicitly, so no explicit build)
#   build.sh <build-target> <test-target>     solution-wide format; build scoped; test scoped
#                                             (use for non-paired test targets)
#
# Targets accept anything `dotnet` accepts: a project name, a .csproj path, or a .sln path.

set -e

ARG1="${1:-}"
ARG2="${2:-}"

run_step() {
    local label="$1"
    shift
    echo "==> $label"
    local output
    output=$("$@" 2>&1) || { local code=$?; echo "$output"; exit $code; }
}

run_step "format (solution-wide)" dotnet format --verify-no-changes --severity info --verbosity quiet

if [ -z "$ARG1" ]; then
    run_step "build (solution-wide)" dotnet build --nologo --verbosity quiet
    run_step "test (solution-wide)" dotnet test --nologo --verbosity quiet --logger "console;verbosity=minimal"
elif [ -z "$ARG2" ]; then
    run_step "test $ARG1" dotnet test "$ARG1" --nologo --verbosity quiet --logger "console;verbosity=minimal"
else
    run_step "build $ARG1" dotnet build "$ARG1" --nologo --verbosity quiet
    run_step "test $ARG2" dotnet test "$ARG2" --nologo --verbosity quiet --logger "console;verbosity=minimal"
fi

echo "==> green"
