#!/usr/bin/env bash
# Produce the canonical diff for a review pass.
#
# Output sections:
#   ==> files       changed file paths with status markers (M/A/D/R)
#   ==> diff        full unified diff (no color)
#   ==> untracked   new files not yet under git (no-arg case only)
#
# Output discipline:
#   - Success: the sections above.
#   - Failure: full captured git output, exit with git's code.
#
# Usage:
#   changes.sh                     pre-commit: uncommitted changes vs HEAD
#                                  (staged + unstaged + untracked file list)
#   changes.sh <ref>               diff against <ref> (e.g. main, origin/main, HEAD~3)
#   changes.sh <ref1> <ref2>       three-dot diff: what is on <ref2> since
#                                  it diverged from <ref1>

set -e

ARG1="${1:-}"
ARG2="${2:-}"

if [ -z "$ARG1" ]; then
    RANGE="HEAD"
    SHOW_UNTRACKED=1
elif [ -z "$ARG2" ]; then
    RANGE="$ARG1"
    SHOW_UNTRACKED=0
else
    RANGE="${ARG1}...${ARG2}"
    SHOW_UNTRACKED=0
fi

run_git() {
    local output
    output=$(git "$@" 2>&1) || { local code=$?; echo "$output"; exit $code; }
    echo "$output"
}

echo "==> files"
files=$(run_git diff --name-status "$RANGE")
if [ -z "$files" ]; then
    echo "(no changes)"
else
    echo "$files"
fi

echo
echo "==> diff"
diff=$(run_git diff --no-color "$RANGE")
if [ -z "$diff" ]; then
    echo "(no diff)"
else
    echo "$diff"
fi

if [ "$SHOW_UNTRACKED" = "1" ]; then
    echo
    echo "==> untracked"
    untracked=$(run_git ls-files --others --exclude-standard)
    if [ -z "$untracked" ]; then
        echo "(none)"
    else
        echo "$untracked"
    fi
fi
