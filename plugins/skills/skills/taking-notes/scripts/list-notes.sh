#!/usr/bin/env bash
# Enumerate notes by reading the first four lines of each docs/notes/*.md.
#
# Output: one block per note, blank line between blocks.
#   <title>
#     tags: <tags>
#     <summary>
#     -> <filename>
#
# Optional tag filter limits output to notes whose Tags: line contains the tag.
# Empty or missing docs/notes/ prints `no notes`.
#
# Usage:
#   list-notes.sh [<tag>]
#
# Examples:
#   list-notes.sh
#   list-notes.sh auth-investigation

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

FILTER="${1:-}"

if [ ! -d docs/notes ]; then
    echo "no notes"
    exit 0
fi

shopt -s nullglob
files=(docs/notes/*.md)

if [ ${#files[@]} -eq 0 ]; then
    echo "no notes"
    exit 0
fi

first=1
matched=0
for f in "${files[@]}"; do
    title=$(sed -n '1s/^# //p' "$f")
    tags=$(sed -n '3s/^Tags: //p' "$f")
    summary=$(sed -n '4p' "$f")
    name=$(basename "$f")

    if [ -n "$FILTER" ]; then
        case ",${tags// /}," in
            *",${FILTER},"*) ;;
            *) continue ;;
        esac
    fi

    [ "$first" = "1" ] || echo
    first=0
    matched=1

    echo "$title"
    echo "  tags: $tags"
    echo "  $summary"
    echo "  -> $name"
done

if [ "$matched" = "0" ]; then
    if [ -n "$FILTER" ]; then
        echo "no notes tagged '$FILTER'"
    else
        echo "no notes"
    fi
fi
