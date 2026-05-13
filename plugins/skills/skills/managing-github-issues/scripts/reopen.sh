#!/usr/bin/env bash
# Reopen a closed GitHub issue with a mandatory comment.
#
# The comment is read from stdin so the agent does not have to escape
# quotes, backticks, dollar signs, or newlines when composing the
# reopen reason.
#
# Output discipline:
#   - Success: the resolved invocation line, then gh's confirmation output.
#   - Failure: the resolved invocation line, then the full gh error,
#              and exit with gh's code.
#
# Usage:
#   echo "problem resurfaced after #17 landed" | reopen.sh 42
#   reopen.sh 42 < reopen-reason.md
#
# Empty stdin is an error — every reopen carries a comment that names
# what changed since closure.

set -eo pipefail

NUMBER="${1:-}"

if [ -z "$NUMBER" ]; then
    echo "usage: reopen.sh <number>  (comment on stdin)" >&2
    exit 2
fi

case "$NUMBER" in
    ''|*[!0-9]*)
        echo "reopen.sh: issue number must be numeric, got '$NUMBER'" >&2
        exit 2
        ;;
esac

if [ -t 0 ]; then
    echo "reopen.sh: comment must be piped on stdin" >&2
    exit 2
fi

COMMENT=$(cat)

if [ -z "$COMMENT" ]; then
    echo "reopen.sh: comment is empty" >&2
    exit 2
fi

printf 'gh issue reopen %s --comment %q\n' "$NUMBER" "$COMMENT"

output=$(gh issue reopen "$NUMBER" --comment "$COMMENT" 2>&1) || { code=$?; echo "$output"; exit $code; }
echo "$output"
