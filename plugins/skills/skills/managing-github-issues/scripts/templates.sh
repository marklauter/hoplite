#!/usr/bin/env bash
# List issue templates defined in the current repository.
#
# Output discipline:
#   - Success: one line per template as `<name>  [<labels>]  <description>`.
#               Empty result prints `no templates`.
#   - Failure: standard shell errors propagate; exit non-zero.
#
# Template lookup order:
#   1. ./.github/ISSUE_TEMPLATE
#   2. <git-root>/.github/ISSUE_TEMPLATE
#   3. <git-root>/*/.github/ISSUE_TEMPLATE   (nested project)
#
# Usage:
#   templates.sh                run before composing a filing so the
#                               template name and label set are visible
#                               at the call site for create.sh.

set -e

DIR=""
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
for candidate in \
    "./.github/ISSUE_TEMPLATE" \
    "${GIT_ROOT}/.github/ISSUE_TEMPLATE"; do
    if [ -n "$candidate" ] && [ -d "$candidate" ]; then
        DIR="$candidate"
        break
    fi
done

if [ -z "$DIR" ] && [ -n "$GIT_ROOT" ]; then
    DIR=$(find "$GIT_ROOT" -type d -name "ISSUE_TEMPLATE" -print -quit 2>/dev/null || true)
fi

if [ -z "$DIR" ] || [ ! -d "$DIR" ]; then
    echo "no templates"
    exit 0
fi

shopt -s nullglob 2>/dev/null || true
found=0
for f in "$DIR"/*.yml "$DIR"/*.yaml; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    [ "$name" = "config.yml" ] || [ "$name" = "config.yaml" ] && continue
    labels=$(awk -F'"' '/^labels:/{for(i=2;i<=NF;i+=2) printf "%s%s", (printed?",":""), $i; printed=1}' "$f")
    description=$(awk '/^description:/ {sub(/^description:[ ]*/, "", $0); print $0; exit}' "$f")
    echo "$name  [$labels]  $description"
    found=1
done

if [ "$found" -eq 0 ]; then
    echo "no templates"
fi
