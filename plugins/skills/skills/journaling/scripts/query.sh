#!/usr/bin/env bash
# Query journal entries by structured predicates over the head fields.
#
# Each flag is an optional predicate. Multiple flags AND together.
# No flags matches every entry.
#
# Predicates:
#   --title PAT          substring, case-insensitive, against the H1 title
#   --tag TAG            exact match against an entry in the comma-separated Tags
#   --xtag TAG           exclude entries where this tag is present in the Tags line
#   --summary PAT        substring, case-insensitive, against the one-line summary
#   --since YYYY-MM-DD   entries with filename date prefix on or after this date
#   --until YYYY-MM-DD   entries with filename date prefix on or before this date
#
# Output: same block-per-match format as list-journal.sh, chronological order.
# Exit code is 0 whether or not there are matches.
#
# Usage:
#   query.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT] [--since DATE] [--until DATE]
#
# Examples:
#   query.sh --since 2026-05-01
#   query.sh --tag auth-investigation --since 2026-05-01 --until 2026-05-12
#   query.sh --title cache --summary ttl
#   query.sh --xtag retrospective --since 2026-05-01

set -e

TITLE=""
TAG=""
XTAG=""
SUMMARY=""
SINCE=""
UNTIL=""

date_re='^[0-9]{4}-[0-9]{2}-[0-9]{2}$'

while [ $# -gt 0 ]; do
    case "$1" in
        --title)
            [ $# -ge 2 ] || { echo "query.sh: --title requires a value" >&2; exit 2; }
            TITLE="$2"; shift 2 ;;
        --tag)
            [ $# -ge 2 ] || { echo "query.sh: --tag requires a value" >&2; exit 2; }
            TAG="$2"; shift 2 ;;
        --xtag)
            [ $# -ge 2 ] || { echo "query.sh: --xtag requires a value" >&2; exit 2; }
            XTAG="$2"; shift 2 ;;
        --summary)
            [ $# -ge 2 ] || { echo "query.sh: --summary requires a value" >&2; exit 2; }
            SUMMARY="$2"; shift 2 ;;
        --since)
            [ $# -ge 2 ] || { echo "query.sh: --since requires a value" >&2; exit 2; }
            SINCE="$2"
            printf '%s' "$SINCE" | grep -Eq "$date_re" || { echo "query.sh: --since must be YYYY-MM-DD" >&2; exit 2; }
            shift 2 ;;
        --until)
            [ $# -ge 2 ] || { echo "query.sh: --until requires a value" >&2; exit 2; }
            UNTIL="$2"
            printf '%s' "$UNTIL" | grep -Eq "$date_re" || { echo "query.sh: --until must be YYYY-MM-DD" >&2; exit 2; }
            shift 2 ;;
        *)
            echo "query.sh: unknown argument '$1'" >&2
            echo "usage: query.sh [--title PAT] [--tag TAG] [--summary PAT] [--since DATE] [--until DATE]" >&2
            exit 2 ;;
    esac
done

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
    entry_date=$(printf '%s' "$name" | sed -E 's/^([0-9]{4}-[0-9]{2}-[0-9]{2}).*/\1/')

    if [ -n "$SINCE" ] && [ "$entry_date" \< "$SINCE" ]; then
        continue
    fi
    if [ -n "$UNTIL" ] && [ "$entry_date" \> "$UNTIL" ]; then
        continue
    fi

    title=$(sed -n '1s/^# //p' "$f")
    date=$(sed -n '3s/^Date: //p' "$f")
    tags=$(sed -n '4s/^Tags: //p' "$f")
    summary=$(sed -n '5p' "$f")

    if [ -n "$TITLE" ]; then
        case "${title,,}" in
            *"${TITLE,,}"*) ;;
            *) continue ;;
        esac
    fi

    if [ -n "$TAG" ]; then
        case ",${tags// /}," in
            *",${TAG},"*) ;;
            *) continue ;;
        esac
    fi

    if [ -n "$XTAG" ]; then
        case ",${tags// /}," in
            *",${XTAG},"*) continue ;;
        esac
    fi

    if [ -n "$SUMMARY" ]; then
        case "${summary,,}" in
            *"${SUMMARY,,}"*) ;;
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
    echo "no matches"
fi
