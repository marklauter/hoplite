#!/usr/bin/env bash
# Close a GitHub issue with a mandatory comment.
#
# The comment is read from stdin so the agent does not have to escape
# quotes, backticks, dollar signs, or newlines when composing the close
# reason.
#
# Output discipline:
#   - Success: the resolved invocation line, then gh's confirmation output.
#   - Failure: the resolved invocation line, then the full gh error,
#              and exit with gh's code.
#
# Usage:
#   echo "fixed in commit abc1234"        | close.sh 42
#   echo "duplicate of #17"               | close.sh 42
#   close.sh 42 < close-reason.md
#
# Empty stdin is an error — every closure carries a comment that names
# the reason, and the script enforces that gate.

set -eo pipefail

NUMBER="${1:-}"

if [ -z "$NUMBER" ]; then
    echo "usage: close.sh <number>  (comment on stdin)" >&2
    exit 2
fi

case "$NUMBER" in
    ''|*[!0-9]*)
        echo "close.sh: issue number must be numeric, got '$NUMBER'" >&2
        exit 2
        ;;
esac

if [ -t 0 ]; then
    echo "close.sh: comment must be piped on stdin" >&2
    exit 2
fi

COMMENT=$(cat)

if [ -z "$COMMENT" ]; then
    echo "close.sh: comment is empty" >&2
    exit 2
fi

printf 'gh issue close %s --comment %q\n' "$NUMBER" "$COMMENT"

output=$(gh issue close "$NUMBER" --comment "$COMMENT" 2>&1) || { code=$?; echo "$output"; exit $code; }
echo "$output"
