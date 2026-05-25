#!/usr/bin/env bash
# Create a GitHub issue from a template and a stdin body.
#
# gh rejects `--template` together with `--body-file`, so the script
# reads the template YAML to extract the labels it would have applied,
# combines them with the LABELS env var, and passes the result through
# `--label`. The template name is still required — it names the schema
# the agent composed against, and locating the YAML enforces that the
# template actually exists.
#
# Template lookup order:
#   1. ./.github/ISSUE_TEMPLATE/<template>
#   2. <git-root>/.github/ISSUE_TEMPLATE/<template>
#   3. <git-root>/*/.github/ISSUE_TEMPLATE/<template>   (nested project)
#
# Output discipline:
#   - Success: the created issue's URL (gh's own output).
#   - Failure: full captured gh output, exit with gh's code.
#
# Usage:
#   create.sh <template-name> <title>
#   LABELS="<csv-labels>" create.sh <template-name> <title>
#
# The body is read from stdin. Labels declared in the template's YAML
# are extracted automatically and combined with any LABELS env var.
#
# Examples:
#   cat body.md | create.sh tech-debt.yml "Refactor serialization layer"
#   LABELS="priority:high" create.sh bug-report.yml "Nested map keys mis-serialized" < body.md

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

TEMPLATE="${1:-}"
TITLE="${2:-}"

if [ -z "$TEMPLATE" ] || [ -z "$TITLE" ]; then
    echo "usage: create.sh <template-name> <title>  (body on stdin)" >&2
    exit 2
fi

if [ -t 0 ]; then
    echo "create.sh: body must be piped on stdin" >&2
    exit 2
fi

TEMPLATE_PATH=""
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
for candidate in \
    "./.github/ISSUE_TEMPLATE/$TEMPLATE" \
    "${GIT_ROOT}/.github/ISSUE_TEMPLATE/$TEMPLATE"; do
    if [ -n "$candidate" ] && [ -f "$candidate" ]; then
        TEMPLATE_PATH="$candidate"
        break
    fi
done

if [ -z "$TEMPLATE_PATH" ] && [ -n "$GIT_ROOT" ]; then
    TEMPLATE_PATH=$(find "$GIT_ROOT" -path '*/.github/ISSUE_TEMPLATE/'"$TEMPLATE" -print -quit 2>/dev/null || true)
fi

if [ -z "$TEMPLATE_PATH" ] || [ ! -f "$TEMPLATE_PATH" ]; then
    echo "create.sh: template not found: $TEMPLATE" >&2
    exit 2
fi

# Label extraction assumes the GitHub issue template style of double-quoted strings,
# e.g. `labels: ["bug", "priority:high"]`. Single-quoted, unquoted, or YAML
# flow-style alternatives silently yield empty labels — the sanity check below
# warns when a `labels:` line is present but extraction produced nothing.
TEMPLATE_LABELS=$(awk -F'"' '/^labels:/{for(i=2;i<=NF;i+=2) print $i}' "$TEMPLATE_PATH" | paste -sd, -)

if [ -z "$TEMPLATE_LABELS" ] && grep -q '^labels:' "$TEMPLATE_PATH"; then
    echo "create.sh: warning: template has a labels: line but no double-quoted labels were extracted; check the template's YAML quoting style" >&2
fi

if [ -n "${LABELS:-}" ] && [ -n "$TEMPLATE_LABELS" ]; then
    ALL_LABELS="${TEMPLATE_LABELS},${LABELS}"
elif [ -n "$TEMPLATE_LABELS" ]; then
    ALL_LABELS="$TEMPLATE_LABELS"
else
    ALL_LABELS="${LABELS:-}"
fi

args=(issue create --title "$TITLE" --body-file -)
[ -n "$ALL_LABELS" ] && args+=(--label "$ALL_LABELS")

output=$(gh "${args[@]}" 2>&1) || { code=$?; echo "$output"; exit $code; }
echo "$output"
