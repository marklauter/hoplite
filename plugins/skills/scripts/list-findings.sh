#!/usr/bin/env bash
# Enumerate findings by reading the head fields of each .findings/*.md by name.
#
# Output: one block per finding, blank line between blocks.
#   <title>
#     severity: <severity>
#     type: <type>
#     lens: <lens>            (only when present)
#     location: <location>
#     principle: <principle>
#     <summary>
#     → <slug>.md
#
# Empty or missing .findings/ prints `no findings`.
#
# Usage:
#   list-findings.sh

set -eo pipefail

# shellcheck disable=SC1091
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

if [ ! -d .findings ]; then
    echo "no findings"
    exit 0
fi

shopt -s nullglob
files=(.findings/*.md)

if [ ${#files[@]} -eq 0 ]; then
    echo "no findings"
    exit 0
fi

first=1
for f in "${files[@]}"; do
    [ "$first" = "1" ] || echo
    first=0

    title=$(sed -n '1s/^# //p' "$f")
    severity=$(get_field "$f" "Severity")
    type=$(get_field "$f" "Type")
    lens=$(get_field "$f" "Lens")
    location=$(get_field "$f" "Location")
    principle=$(get_field "$f" "Principle")
    summary=$(get_summary "$f")
    slug=$(basename "$f")

    echo "$title"
    echo "  severity: $severity"
    [ -n "$type" ] && echo "  type: $type"
    [ -n "$lens" ] && echo "  lens: $lens"
    echo "  location: $location"
    echo "  principle: $principle"
    echo "  $summary"
    echo "  → $slug"
done
