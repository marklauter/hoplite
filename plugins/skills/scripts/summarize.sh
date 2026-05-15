#!/usr/bin/env bash
# Summarize the .findings/ directory.
#
# Output (per type present, then a combined verdict):
#   code: <i> important, <n> nit, <p> pre-existing
#   documentation: <i> important, <n> nit, <p> pre-existing
#     by lens: <count> Structure, <count> Line, ...     (only when documentation findings exist)
#   <verdict line>
#   <non-canonical principle line(s) if any>
#
# Verdict logic (aggregate across all types):
#   - any important > 0          → "diff is blocked on important findings"
#   - important == 0, nit > 0    → "diff is shippable; nits optional"
#   - important == 0, nit == 0   → "diff is shippable"
#   - any pre-existing           → appended "; pre-existing triage pending"
#
# Non-canonical principles are reported per type. Type code is checked against
# writing-csharp Philosophy headings; type documentation against writing-documentation.
#
# Empty or missing .findings/ prints `no findings` and exits 0.
#
# Usage:
#   summarize.sh

set -eo pipefail

# shellcheck disable=SC1091
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

dir=$(findings_dir)

if [ ! -d "$dir" ]; then
    echo "no findings"
    exit 0
fi

shopt -s nullglob
files=("$dir"/*.md)

if [ ${#files[@]} -eq 0 ]; then
    echo "no findings"
    exit 0
fi

code_important=0
code_nit=0
code_preexisting=0
documentation_important=0
documentation_nit=0
documentation_preexisting=0

lens_Structure=0
lens_Line=0
lens_Copy=0
lens_Accuracy=0
lens_Coherence=0
lens_References=0
declare -a code_noncanonical
declare -a documentation_noncanonical

plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
code_skill="${plugin_root}/skills/writing-csharp/SKILL.md"
documentation_skill="${plugin_root}/skills/writing-documentation/SKILL.md"

read_canonical() {
    local skill="$1"
    [ -f "$skill" ] || return 0
    # Strip trailing ` (Source)` citation suffixes so principle matching ignores them.
    awk '/^## Philosophy/{flag=1; next} /^## /{flag=0} flag && /^### /{sub(/^### /, ""); sub(/ \([^)]+\)$/, ""); print}' "$skill"
}

strip_citation() {
    printf '%s' "$1" | sed -E 's/ \([^)]+\)$//'
}

if [ -z "$plugin_root" ]; then
    code_canonical=""
    documentation_canonical=""
    code_canonical_unreadable=1
    documentation_canonical_unreadable=1
else
    code_canonical=$(read_canonical "$code_skill")
    documentation_canonical=$(read_canonical "$documentation_skill")
    [ -f "$code_skill" ] && code_canonical_unreadable=0 || code_canonical_unreadable=1
    [ -f "$documentation_skill" ] && documentation_canonical_unreadable=0 || documentation_canonical_unreadable=1
fi

# Sanity check: if the SKILL.md was readable but no canonical principles were
# extracted, the Philosophy heading structure has likely drifted from the
# `### <heading>` shape this script depends on. Warn so the contract failure
# is visible rather than silent.
if [ "$code_canonical_unreadable" = "0" ] && [ -z "$code_canonical" ]; then
    echo "summarize.sh: warning: $code_skill was readable but yielded no canonical principles; verify the Philosophy heading shape" >&2
fi
if [ "$documentation_canonical_unreadable" = "0" ] && [ -z "$documentation_canonical" ]; then
    echo "summarize.sh: warning: $documentation_skill was readable but yielded no canonical principles; verify the Philosophy heading shape" >&2
fi

is_canonical() {
    local p; p=$(strip_citation "$1")
    local list="$2"
    while IFS= read -r line; do
        [ "$line" = "$p" ] && return 0
    done <<< "$list"
    return 1
}

for f in "${files[@]}"; do
    severity=$(get_field "$f" "Severity")
    type=$(get_field "$f" "Type")
    lens=$(get_field "$f" "Lens")
    principle=$(get_field "$f" "Principle")
    name=$(basename "$f")

    # Treat absent Type as code for backward compatibility.
    [ -z "$type" ] && type="code"

    case "$type" in
        code)
            case "$severity" in
                important) code_important=$((code_important + 1)) ;;
                nit) code_nit=$((code_nit + 1)) ;;
                pre-existing) code_preexisting=$((code_preexisting + 1)) ;;
            esac
            if [ -n "$principle" ] && [ "$code_canonical_unreadable" = "0" ] && ! is_canonical "$principle" "$code_canonical"; then
                code_noncanonical+=("$name: $principle")
            fi
            ;;
        documentation)
            case "$severity" in
                important) documentation_important=$((documentation_important + 1)) ;;
                nit) documentation_nit=$((documentation_nit + 1)) ;;
                pre-existing) documentation_preexisting=$((documentation_preexisting + 1)) ;;
            esac
            case "$lens" in
                Structure)  lens_Structure=$((lens_Structure + 1)) ;;
                Line)       lens_Line=$((lens_Line + 1)) ;;
                Copy)       lens_Copy=$((lens_Copy + 1)) ;;
                Accuracy)   lens_Accuracy=$((lens_Accuracy + 1)) ;;
                Coherence)  lens_Coherence=$((lens_Coherence + 1)) ;;
                References) lens_References=$((lens_References + 1)) ;;
            esac
            if [ -n "$principle" ] && [ "$documentation_canonical_unreadable" = "0" ] && ! is_canonical "$principle" "$documentation_canonical"; then
                documentation_noncanonical+=("$name: $principle")
            fi
            ;;
    esac
done

code_total=$((code_important + code_nit + code_preexisting))
documentation_total=$((documentation_important + documentation_nit + documentation_preexisting))

if [ "$code_total" -gt 0 ]; then
    echo "code: $code_important important, $code_nit nit, $code_preexisting pre-existing"
fi

if [ "$documentation_total" -gt 0 ]; then
    echo "documentation: $documentation_important important, $documentation_nit nit, $documentation_preexisting pre-existing"
    parts=""
    for lens in Structure Line Copy Accuracy Coherence References; do
        var="lens_${lens}"
        count="${!var}"
        if [ "$count" -gt 0 ]; then
            [ -z "$parts" ] || parts="${parts}, "
            parts="${parts}${count} ${lens}"
        fi
    done
    [ -n "$parts" ] && echo "  by lens: $parts"
fi

total_important=$((code_important + documentation_important))
total_nit=$((code_nit + documentation_nit))
total_preexisting=$((code_preexisting + documentation_preexisting))

if [ "$total_important" -gt 0 ]; then
    verdict="diff is blocked on important findings"
elif [ "$total_nit" -gt 0 ]; then
    verdict="diff is shippable; nits optional"
else
    verdict="diff is shippable"
fi

if [ "$total_preexisting" -gt 0 ]; then
    verdict="${verdict}; pre-existing triage pending"
fi

echo "$verdict"

if [ "$code_total" -gt 0 ] && [ "$code_canonical_unreadable" = "1" ]; then
    if [ -z "$plugin_root" ]; then
        echo "warning: CLAUDE_PLUGIN_ROOT is unset; non-canonical principle check skipped for code findings" >&2
    else
        echo "warning: $code_skill not found; non-canonical principle check skipped for code findings" >&2
    fi
fi

if [ ${#code_noncanonical[@]} -gt 0 ]; then
    echo "${#code_noncanonical[@]} code finding(s) cite a non-canonical principle — candidate(s) for writing-csharp:"
    for entry in "${code_noncanonical[@]}"; do
        echo "  $entry"
    done
fi

if [ "$documentation_total" -gt 0 ] && [ "$documentation_canonical_unreadable" = "1" ]; then
    if [ -z "$plugin_root" ]; then
        echo "warning: CLAUDE_PLUGIN_ROOT is unset; non-canonical principle check skipped for documentation findings" >&2
    else
        echo "warning: $documentation_skill not found; non-canonical principle check skipped for documentation findings" >&2
    fi
fi

if [ ${#documentation_noncanonical[@]} -gt 0 ]; then
    echo "${#documentation_noncanonical[@]} documentation finding(s) cite a non-canonical principle — candidate(s) for writing-documentation:"
    for entry in "${documentation_noncanonical[@]}"; do
        echo "  $entry"
    done
fi
