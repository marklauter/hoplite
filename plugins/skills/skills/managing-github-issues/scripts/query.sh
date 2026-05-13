#!/usr/bin/env bash
# Dedup search across open and closed issues.
# Runs the same keyword search against both states and prints any matches.
#
# Output discipline:
#   - Success with matches: one line per issue, format `#<n> [<state>] <title>  <url>`.
#   - Success with no matches: `no matches`.
#   - Failure: full captured gh output, exit with gh's code.
# Exit code is 0 in both match and no-match cases — a clean dedup result is success.
#
# Usage:
#   query.sh <keywords...>
#
# Examples:
#   query.sh "nested map serialization"
#   query.sh tech-debt transactions

set -eo pipefail

if [ $# -eq 0 ]; then
    echo "usage: query.sh <keywords...>" >&2
    exit 2
fi

SEARCH="$*"

TEMPLATE='{{range .}}#{{.number}} [{{.state}}] {{.title}}  {{.url}}
{{end}}'

output=$(gh issue list --state all --search "$SEARCH" --json number,state,title,url --limit 50 --template "$TEMPLATE" 2>&1) || {
    code=$?; echo "$output"; exit $code;
}

if [ -z "$output" ]; then
    echo "no matches"
else
    echo "$output"
fi
