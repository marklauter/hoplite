#!/usr/bin/env bash
# Enumerate journal entries by reading the first five lines of each docs/journal/*.md.
#
# Output: one block per entry, in chronological order, blank line between blocks.
#   <title>
#     date: <date>
#     tags: <tags>
#     <summary>
#     -> <filename>
#
# Optional argument filters output:
#   - YYYY-MM-DD: lists entries on or after that date.
#   - <tag>: lists entries whose Tags: line contains the tag.
#
# Empty or missing docs/journal/ prints `no entries`.
#
# Usage:
#   list-journal.sh [<since-date> | <tag>]
#
# Examples:
#   list-journal.sh
#   list-journal.sh 2026-05-01
#   list-journal.sh auth-investigation

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

FILTER="${1:-}"
DATE_MODE=0

if [ -n "$FILTER" ]; then
    if printf '%s' "$FILTER" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
        DATE_MODE=1
    fi
fi

if [ ! -d docs/journal ]; then
    echo "no entries"
    exit 0
fi

shopt -s nullglob
files=(docs/journal/*.md)

if [ ${#files[@]} -eq 0 ]; then
    echo "no entries"
    exit 0
fi

first=1
matched=0
for f in "${files[@]}"; do
    name=$(basename "$f")

    if [ "$DATE_MODE" = "1" ]; then
        entry_date=$(printf '%s' "$name" | sed -E 's/^([0-9]{4}-[0-9]{2}-[0-9]{2}).*/\1/')
        if [ "$entry_date" \< "$FILTER" ]; then
            continue
        fi
    fi

    title=$(sed -n '1s/^# //p' "$f")
    date=$(sed -n '3s/^Date: //p' "$f")
    tags=$(sed -n '4s/^Tags: //p' "$f")
    summary=$(sed -n '5p' "$f")

    if [ -n "$FILTER" ] && [ "$DATE_MODE" = "0" ]; then
        case ",${tags// /}," in
            *",${FILTER},"*) ;;
            *) continue ;;
        esac
    fi

    [ "$first" = "1" ] || echo
    first=0
    matched=1

    echo "$title"
    echo "  date: $date"
    echo "  tags: $tags"
    echo "  $summary"
    echo "  -> $name"
done

if [ "$matched" = "0" ]; then
    if [ "$DATE_MODE" = "1" ]; then
        echo "no entries on or after '$FILTER'"
    elif [ -n "$FILTER" ]; then
        echo "no entries tagged '$FILTER'"
    else
        echo "no entries"
    fi
fi
