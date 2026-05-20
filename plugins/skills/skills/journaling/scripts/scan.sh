#!/usr/bin/env bash
# Scan journal entries by structured predicates over the head fields.
#
# Each flag is an optional predicate. Multiple flags AND together.
# No flags lists every entry, chronologically.
#
# Predicates:
#   --title PAT          substring, case-insensitive, against the H1 title
#   --tag TAG            exact match against an entry in the comma-separated Tags
#   --xtag TAG           exclude entries where this tag is present in the Tags line
#   --summary PAT        substring, case-insensitive, against the one-line summary
#   --since YYYY-MM-DD   entries with filename date prefix on or after this date
#   --until YYYY-MM-DD   entries with filename date prefix on or before this date
#
# Output: one block per match — title, date, tags, summary, filename — in
# chronological order, blank line between blocks.
# Empty result prints `no entries matching <predicates>` (or `no entries` if
# docs/journal is missing/empty).
# Exit code is 0 whether or not there are matches — a clean empty result is success.
#
# Usage:
#   scan.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT] [--since DATE] [--until DATE]
#
# Examples:
#   scan.sh
#   scan.sh --since 2026-05-01
#   scan.sh --tag auth-investigation --since 2026-05-01 --until 2026-05-12
#   scan.sh --title cache --summary ttl
#   scan.sh --xtag retrospective --since 2026-05-01

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

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
            [ $# -ge 2 ] || { echo "scan.sh: --title requires a value" >&2; exit 2; }
            TITLE="$2"; shift 2 ;;
        --tag)
            [ $# -ge 2 ] || { echo "scan.sh: --tag requires a value" >&2; exit 2; }
            TAG="$2"; shift 2 ;;
        --xtag)
            [ $# -ge 2 ] || { echo "scan.sh: --xtag requires a value" >&2; exit 2; }
            XTAG="$2"; shift 2 ;;
        --summary)
            [ $# -ge 2 ] || { echo "scan.sh: --summary requires a value" >&2; exit 2; }
            SUMMARY="$2"; shift 2 ;;
        --since)
            [ $# -ge 2 ] || { echo "scan.sh: --since requires a value" >&2; exit 2; }
            SINCE="$2"
            printf '%s' "$SINCE" | grep -Eq "$date_re" || { echo "scan.sh: --since must be YYYY-MM-DD" >&2; exit 2; }
            shift 2 ;;
        --until)
            [ $# -ge 2 ] || { echo "scan.sh: --until requires a value" >&2; exit 2; }
            UNTIL="$2"
            printf '%s' "$UNTIL" | grep -Eq "$date_re" || { echo "scan.sh: --until must be YYYY-MM-DD" >&2; exit 2; }
            shift 2 ;;
        *)
            echo "scan.sh: unknown argument '$1'" >&2
            echo "usage: scan.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT] [--since DATE] [--until DATE]" >&2
            exit 2 ;;
    esac
done

# Portable case-insensitive substring match — bash 3.2 compatible.
to_lower() {
    printf '%s' "$1" | LC_ALL=C tr '[:upper:]' '[:lower:]'
}

TITLE_LC=$(to_lower "$TITLE")
SUMMARY_LC=$(to_lower "$SUMMARY")

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
    date=$(sed -n '3s/^date: //p' "$f")
    tags=$(sed -n '4s/^tags: //p' "$f")
    summary=$(sed -n '5p' "$f")

    if [ -n "$TITLE_LC" ]; then
        case "$(to_lower "$title")" in
            *"$TITLE_LC"*) ;;
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

    if [ -n "$SUMMARY_LC" ]; then
        case "$(to_lower "$summary")" in
            *"$SUMMARY_LC"*) ;;
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
    preds=""
    [ -n "$TITLE" ]   && preds="$preds --title '$TITLE'"
    [ -n "$TAG" ]     && preds="$preds --tag '$TAG'"
    [ -n "$XTAG" ]    && preds="$preds --xtag '$XTAG'"
    [ -n "$SUMMARY" ] && preds="$preds --summary '$SUMMARY'"
    [ -n "$SINCE" ]   && preds="$preds --since '$SINCE'"
    [ -n "$UNTIL" ]   && preds="$preds --until '$UNTIL'"
    echo "no entries matching${preds}"
fi
