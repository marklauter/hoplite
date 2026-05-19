#!/usr/bin/env bash
# Query notes by structured predicates over the head fields.
#
# Each flag is an optional predicate. Multiple flags AND together.
# No flags matches every note.
#
# Predicates:
#   --title PAT     substring, case-insensitive, against the H1 title
#   --tag TAG       exact match against an entry in the comma-separated Tags
#   --xtag TAG      exclude notes where this tag is present in the Tags line
#   --summary PAT   substring, case-insensitive, against the one-line summary
#
# Output: one block per match — title, tags, summary, filename.
# Empty result prints `no notes matching <predicates>` (or `no notes` if docs/notes is missing/empty).
# Exit code is 0 whether or not there are matches — a clean empty result is success.
#
# Usage:
#   scan.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT]
#
# Examples:
#   scan.sh --tag auth-investigation
#   scan.sh --title cache --summary ttl
#   scan.sh --tag cache --xtag draft
#   scan.sh --xtag stale

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
        *)
            echo "scan.sh: unknown argument '$1'" >&2
            echo "usage: scan.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT]" >&2
            exit 2 ;;
    esac
done

# Portable case-insensitive substring match — bash 3.2 compatible.
to_lower() {
    printf '%s' "$1" | LC_ALL=C tr '[:upper:]' '[:lower:]'
}

TITLE_LC=$(to_lower "$TITLE")
SUMMARY_LC=$(to_lower "$SUMMARY")

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
    echo "no notes matching${preds}"
fi
