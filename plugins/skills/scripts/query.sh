#!/usr/bin/env bash
# Query findings by structured predicates over the head fields.
#
# Each flag is an optional predicate. Multiple flags AND together.
# No flags matches every finding.
#
# Predicates:
#   --title PAT       substring, case-insensitive, against the H1 title
#   --severity LEVEL  exact match: important | nit | pre-existing
#   --xseverity LEVEL exclude findings with this severity
#   --type KIND       exact match: code | documentation
#   --xtype KIND      exclude findings with this type
#   --lens NAME       exact match: Structure | Line | Copy | Accuracy | Coherence | References
#   --xlens NAME      exclude findings with this lens
#   --location PAT    substring, case-insensitive, against the Location field
#                     (raw Location value, including backticks)
#   --principle PAT   substring, case-insensitive, against the Principle field
#   --summary PAT     substring, case-insensitive, against the one-line summary
#
# Output: same block-per-match format as list-findings.sh.
# Exit code is 0 whether or not there are matches.
#
# Usage:
#   query.sh [--title PAT] [--severity LEVEL] [--xseverity LEVEL] \
#            [--type KIND] [--xtype KIND] [--lens NAME] [--xlens NAME] \
#            [--location PAT] [--principle PAT] [--summary PAT]
#
# Examples:
#   query.sh --severity important
#   query.sh --xseverity pre-existing               # everything actionable on this diff
#   query.sh --type documentation --lens Line
#   query.sh --type code --principle "Results, not exceptions"
#   query.sh --severity nit --location src/
#   query.sh --type documentation --xlens References

set -eo pipefail

TITLE=""
SEVERITY=""
XSEVERITY=""
TYPE=""
XTYPE=""
LENS=""
XLENS=""
LOCATION=""
PRINCIPLE=""
SUMMARY=""

while [ $# -gt 0 ]; do
    case "$1" in
        --title)
            [ $# -ge 2 ] || { echo "query.sh: --title requires a value" >&2; exit 2; }
            TITLE="$2"; shift 2 ;;
        --severity)
            [ $# -ge 2 ] || { echo "query.sh: --severity requires a value" >&2; exit 2; }
            SEVERITY="$2"
            case "$SEVERITY" in
                important|nit|pre-existing) ;;
                *)
                    echo "query.sh: invalid severity '$SEVERITY' (must be important, nit, or pre-existing)" >&2
                    exit 2 ;;
            esac
            shift 2 ;;
        --xseverity)
            [ $# -ge 2 ] || { echo "query.sh: --xseverity requires a value" >&2; exit 2; }
            XSEVERITY="$2"
            case "$XSEVERITY" in
                important|nit|pre-existing) ;;
                *)
                    echo "query.sh: invalid xseverity '$XSEVERITY' (must be important, nit, or pre-existing)" >&2
                    exit 2 ;;
            esac
            shift 2 ;;
        --type)
            [ $# -ge 2 ] || { echo "query.sh: --type requires a value" >&2; exit 2; }
            TYPE="$2"
            case "$TYPE" in
                code|documentation) ;;
                *)
                    echo "query.sh: invalid type '$TYPE' (must be code or documentation)" >&2
                    exit 2 ;;
            esac
            shift 2 ;;
        --xtype)
            [ $# -ge 2 ] || { echo "query.sh: --xtype requires a value" >&2; exit 2; }
            XTYPE="$2"
            case "$XTYPE" in
                code|documentation) ;;
                *)
                    echo "query.sh: invalid xtype '$XTYPE' (must be code or documentation)" >&2
                    exit 2 ;;
            esac
            shift 2 ;;
        --lens)
            [ $# -ge 2 ] || { echo "query.sh: --lens requires a value" >&2; exit 2; }
            LENS="$2"
            case "$LENS" in
                Structure|Line|Copy|Accuracy|Coherence|References) ;;
                *)
                    echo "query.sh: invalid lens '$LENS' (must be Structure, Line, Copy, Accuracy, Coherence, or References)" >&2
                    exit 2 ;;
            esac
            shift 2 ;;
        --xlens)
            [ $# -ge 2 ] || { echo "query.sh: --xlens requires a value" >&2; exit 2; }
            XLENS="$2"
            case "$XLENS" in
                Structure|Line|Copy|Accuracy|Coherence|References) ;;
                *)
                    echo "query.sh: invalid xlens '$XLENS' (must be Structure, Line, Copy, Accuracy, Coherence, or References)" >&2
                    exit 2 ;;
            esac
            shift 2 ;;
        --location)
            [ $# -ge 2 ] || { echo "query.sh: --location requires a value" >&2; exit 2; }
            LOCATION="$2"; shift 2 ;;
        --principle)
            [ $# -ge 2 ] || { echo "query.sh: --principle requires a value" >&2; exit 2; }
            PRINCIPLE="$2"; shift 2 ;;
        --summary)
            [ $# -ge 2 ] || { echo "query.sh: --summary requires a value" >&2; exit 2; }
            SUMMARY="$2"; shift 2 ;;
        *)
            echo "query.sh: unknown argument '$1'" >&2
            echo "usage: query.sh [--title PAT] [--severity LEVEL] [--xseverity LEVEL] [--type KIND] [--xtype KIND] [--lens NAME] [--xlens NAME] [--location PAT] [--principle PAT] [--summary PAT]" >&2
            exit 2 ;;
    esac
done

# shellcheck disable=SC1091
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

to_lower() {
    printf '%s' "$1" | LC_ALL=C tr '[:upper:]' '[:lower:]'
}

TITLE_LC=$(to_lower "$TITLE")
LOCATION_LC=$(to_lower "$LOCATION")
PRINCIPLE_LC=$(to_lower "$PRINCIPLE")
SUMMARY_LC=$(to_lower "$SUMMARY")

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
matched=0
for f in "${files[@]}"; do
    title=$(sed -n '1s/^# //p' "$f")
    f_severity=$(get_field "$f" "Severity")
    f_type=$(get_field "$f" "Type")
    f_lens=$(get_field "$f" "Lens")
    f_location=$(get_field "$f" "Location")
    f_principle=$(get_field "$f" "Principle")
    summary=$(get_summary "$f")
    name=$(basename "$f")

    if [ -n "$TITLE_LC" ]; then
        case "$(to_lower "$title")" in
            *"$TITLE_LC"*) ;;
            *) continue ;;
        esac
    fi

    if [ -n "$SEVERITY" ] && [ "$f_severity" != "$SEVERITY" ]; then
        continue
    fi

    if [ -n "$XSEVERITY" ] && [ "$f_severity" = "$XSEVERITY" ]; then
        continue
    fi

    # Backward-compat: absent Type: is treated as code, matching summarize.sh.
    effective_type="${f_type:-code}"

    if [ -n "$TYPE" ] && [ "$effective_type" != "$TYPE" ]; then
        continue
    fi

    if [ -n "$XTYPE" ] && [ "$effective_type" = "$XTYPE" ]; then
        continue
    fi

    if [ -n "$LENS" ] && [ "$f_lens" != "$LENS" ]; then
        continue
    fi

    if [ -n "$XLENS" ] && [ "$f_lens" = "$XLENS" ]; then
        continue
    fi

    if [ -n "$LOCATION_LC" ]; then
        case "$(to_lower "$f_location")" in
            *"$LOCATION_LC"*) ;;
            *) continue ;;
        esac
    fi

    if [ -n "$PRINCIPLE_LC" ]; then
        case "$(to_lower "$f_principle")" in
            *"$PRINCIPLE_LC"*) ;;
            *) continue ;;
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
    echo "  severity: $f_severity"
    [ -n "$f_type" ] && echo "  type: $f_type"
    [ -n "$f_lens" ] && echo "  lens: $f_lens"
    echo "  location: $f_location"
    echo "  principle: $f_principle"
    echo "  $summary"
    echo "  → $name"
done

if [ "$matched" = "0" ]; then
    echo "no matches"
fi
