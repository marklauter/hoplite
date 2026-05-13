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

set -e

get_field() {
    local file="$1"
    local field="$2"
    grep -m1 "^${field}: " "$file" | sed "s/^${field}: //" || true
}

get_summary() {
    # The summary is the line immediately after the Principle: line.
    local file="$1"
    local principle_line
    principle_line=$(grep -n -m1 '^Principle: ' "$file" | cut -d: -f1)
    [ -n "$principle_line" ] || return 0
    sed -n "$((principle_line + 1))p" "$file"
}

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
