#!/usr/bin/env bash
# List GitHub issues with optional filters.
#
# Output discipline:
#   - Success: one line per issue, format `#<n> [<state>] [<labels>] <title>  <url>`.
#               Empty result prints `no issues`.
#   - Failure: full captured gh output, exit with gh's code.
#
# Usage:
#   list.sh                              open issues, no filters
#   list.sh open                         open issues
#   list.sh closed                       closed issues
#   list.sh all                          open and closed
#   list.sh <state> <label>              filter by label
#   list.sh <state> <label> <search>     filter by label and keyword search
#   list.sh <state> "" <search>          filter by keyword only (empty label)

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

STATE="${1:-open}"
LABEL="${2:-}"
SEARCH="${3:-}"

TEMPLATE='{{if .}}{{range .}}#{{.number}} [{{.state}}] {{if .labels}}[{{range $i, $l := .labels}}{{if $i}},{{end}}{{$l.name}}{{end}}] {{end}}{{.title}}  {{.url}}
{{end}}{{else}}no issues
{{end}}'

args=(issue list --state "$STATE" --json number,state,labels,title,url --limit 100 --template "$TEMPLATE")
[ -n "$LABEL" ] && args+=(--label "$LABEL")
[ -n "$SEARCH" ] && args+=(--search "$SEARCH")

output=$(gh "${args[@]}" 2>&1) || { code=$?; echo "$output"; exit $code; }
echo "$output"
