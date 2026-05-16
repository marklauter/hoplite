#!/usr/bin/env bash
# Add a comment to a GitHub issue.
#
# The comment body is read from stdin so the agent does not have to
# escape quotes, backticks, dollar signs, or newlines when composing
# the comment.
#
# Output discipline:
#   - Success: the resolved invocation line, then the comment URL from gh.
#   - Failure: the resolved invocation line, then the full gh error,
#              and exit with gh's code.
#
# Usage:
#   echo "still reproducible on main@abc1234" | comment.sh 42
#   comment.sh 42 < comment-body.md
#
# Empty stdin is an error.

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

NUMBER="${1:-}"

if [ -z "$NUMBER" ]; then
    echo "usage: comment.sh <number>  (body on stdin)" >&2
    exit 2
fi

case "$NUMBER" in
    ''|*[!0-9]*)
        echo "comment.sh: issue number must be numeric, got '$NUMBER'" >&2
        exit 2
        ;;
esac

if [ -t 0 ]; then
    echo "comment.sh: body must be piped on stdin" >&2
    exit 2
fi

printf 'gh issue comment %s --body-file -\n' "$NUMBER"

output=$(gh issue comment "$NUMBER" --body-file - 2>&1) || { code=$?; echo "$output"; exit $code; }
echo "$output"
