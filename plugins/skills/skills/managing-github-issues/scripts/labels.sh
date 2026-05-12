#!/usr/bin/env bash
# List labels defined in the current repository.
#
# Output discipline:
#   - Success: one line per label, format `<name>  <description>`.
#               Empty result prints `no labels`.
#   - Failure: full captured gh output, exit with gh's code.
#
# Usage:
#   labels.sh                use this before composing a filing or a
#                            triage entry so label names match the
#                            project's existing vocabulary exactly.

set -e

TEMPLATE='{{if .}}{{range .}}{{.name}}  {{.description}}
{{end}}{{else}}no labels
{{end}}'

output=$(gh label list --limit 200 --json name,description --template "$TEMPLATE" 2>&1) || { code=$?; echo "$output"; exit $code; }
echo "$output"
