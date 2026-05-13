#!/usr/bin/env bash
# Apply a single approved triage edit to an issue.
#
# Wraps `gh issue edit`. Prints the resolved invocation before calling gh,
# so the human sees the exact diff being applied. One issue per call —
# walking a triage document is the agent's job, not the script's, so the
# confirmation pause happens between entries.
#
# Output discipline:
#   - Success: the resolved invocation line, then the issue URL from gh.
#   - Failure: the resolved invocation line, then the full gh error,
#              and exit with gh's code.
#
# Usage:
#   edit.sh <number> [gh-issue-edit-flags...]
#
# Examples:
#   edit.sh 42 --add-label "priority: high" --add-label "tech-debt"
#   edit.sh 42 --remove-label "wontfix" --add-assignee "@me"
#   edit.sh 42 --title "New title" --milestone "v1.2"

set -eo pipefail

if [ $# -lt 2 ]; then
    echo "usage: edit.sh <number> <gh-issue-edit-flags...>" >&2
    exit 2
fi

NUMBER="$1"
shift

case "$NUMBER" in
    ''|*[!0-9]*)
        echo "edit.sh: issue number must be numeric, got '$NUMBER'" >&2
        exit 2
        ;;
esac

printf 'gh issue edit %s' "$NUMBER"
for a in "$@"; do
    printf ' %q' "$a"
done
printf '\n'

output=$(gh issue edit "$NUMBER" "$@" 2>&1) || { code=$?; echo "$output"; exit $code; }
echo "$output"
