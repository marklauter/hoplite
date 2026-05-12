#!/usr/bin/env bash
# Enumerate findings by reading the first six lines of each .findings/*.md.
#
# Output: one block per finding, blank line between blocks.
#   <title>
#     severity: <severity>
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
    severity=$(sed -n '3s/^Severity: //p' "$f")
    location=$(sed -n '4s/^Location: //p' "$f")
    principle=$(sed -n '5s/^Principle: //p' "$f")
    summary=$(sed -n '6p' "$f")
    slug=$(basename "$f")

    echo "$title"
    echo "  severity: $severity"
    echo "  location: $location"
    echo "  principle: $principle"
    echo "  $summary"
    echo "  → $slug"
done
