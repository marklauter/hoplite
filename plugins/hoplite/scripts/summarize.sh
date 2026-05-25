#!/usr/bin/env bash
# Summarize the .findings/ directory.
#
# Output (per type present, then a combined verdict):
#   code: <i> important, <n> nit, <p> pre-existing
#   documentation: <i> important, <n> nit, <p> pre-existing
#     by lens: <count> Structure, <count> Line, ...     (only when documentation findings exist)
#   wiki: <i> important, <n> nit, <p> pre-existing
#     by lens: <count> Structure, <count> Line, ...     (only when wiki findings exist)
#   <verdict line>
#   <non-canonical principle line(s) if any>
#
# Verdict logic (aggregate across all types). Mode-agnostic: the same
# vocabulary covers diff mode (pre-commit gate) and audit mode (whole-corpus
# pass). In audit mode `pre-existing` does not arise — the reviewer produces
# only important and nit findings.
#   - any important > 0          → "review blocked on important findings"
#   - important == 0, nit > 0    → "review passes; nits optional"
#   - important == 0, nit == 0   → "review passes"
#   - any pre-existing           → appended "; pre-existing triage pending"
#
# Non-canonical principles are reported per type. Type code is checked against
# writing-csharp Philosophy headings; type documentation against writing-prose
# principle bullets; type wiki against the union of writing-wiki Philosophy
# headings and writing-prose principle bullets (wiki findings may cite either
# rubric).
#
# Empty or missing .findings/ prints `no findings` and exits 0.
#
# Usage:
#   summarize.sh

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

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
wiki_important=0
wiki_nit=0
wiki_preexisting=0

lens_Structure=0
lens_Line=0
lens_Copy=0
lens_Accuracy=0
lens_Coherence=0
lens_References=0
wiki_lens_Structure=0
wiki_lens_Line=0
wiki_lens_Copy=0
wiki_lens_Accuracy=0
wiki_lens_Coherence=0
wiki_lens_References=0
declare -a code_noncanonical
declare -a documentation_noncanonical
declare -a wiki_noncanonical

plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
code_skill="${plugin_root}/skills/writing-csharp/SKILL.md"
documentation_skill="${plugin_root}/skills/writing-prose/SKILL.md"
wiki_skill="${plugin_root}/skills/writing-wiki/SKILL.md"

read_canonical() {
    local skill="$1"
    [ -f "$skill" ] || return 0
    # Strip trailing ` (Source)` citation suffixes so principle matching ignores them.
    awk '/^## Philosophy/{flag=1; next} /^## /{flag=0} flag && /^### /{sub(/^### /, ""); sub(/ \([^)]+\)$/, ""); print}' "$skill"
}

# writing-prose holds principles as bulleted list items in three places:
# the Composition section, the Grammar/structure/referential-integrity section,
# and the judgement subsection of Validation — rather than as `### ` anchors.
# The canonical name is the text between the leading `- ` and the first
# ` — ` (space-em-dash-space). Citation suffixes are stripped so authors may
# cite either form.
read_canonical_prose() {
    local skill="$1"
    [ -f "$skill" ] || return 0
    awk '
        /^## Composition/ { flag=1; next }
        /^## Grammar, structure, and referential integrity/ { flag=1; next }
        /^### Self-review — apply judgement/ { flag=1; next }
        /^## / { flag=0 }
        /^### / && !/^### Self-review — apply judgement/ { if (flag) flag=0 }
        flag && /^- / {
            line = substr($0, 3)
            idx = index(line, " — ")
            if (idx > 0) {
                name = substr(line, 1, idx - 1)
                sub(/ \([^)]+\)$/, "", name)
                print name
            }
        }
    ' "$skill"
}

strip_citation() {
    printf '%s' "$1" | sed -E 's/ \([^)]+\)$//'
}

if [ -z "$plugin_root" ]; then
    code_canonical=""
    documentation_canonical=""
    wiki_canonical_own=""
    code_canonical_unreadable=1
    documentation_canonical_unreadable=1
    wiki_canonical_unreadable=1
else
    code_canonical=$(read_canonical "$code_skill")
    documentation_canonical=$(read_canonical_prose "$documentation_skill")
    wiki_canonical_own=$(read_canonical "$wiki_skill")
    [ -f "$code_skill" ] && code_canonical_unreadable=0 || code_canonical_unreadable=1
    [ -f "$documentation_skill" ] && documentation_canonical_unreadable=0 || documentation_canonical_unreadable=1
    [ -f "$wiki_skill" ] && wiki_canonical_unreadable=0 || wiki_canonical_unreadable=1
fi

# Wiki findings may cite anchors from either writing-wiki or writing-prose.
# The union of both rubrics is the canonical set for wiki type. The unreadable
# flag fires only when both rubrics are missing — one is enough to check against.
if [ "$wiki_canonical_unreadable" = "0" ] || [ "$documentation_canonical_unreadable" = "0" ]; then
    wiki_canonical=$(printf '%s\n%s\n' "$wiki_canonical_own" "$documentation_canonical")
    wiki_check_unreadable=0
else
    wiki_canonical=""
    wiki_check_unreadable=1
fi

# Sanity check: if the SKILL.md was readable but no canonical principles were
# extracted, the section structure has likely drifted from the shape this
# script depends on. Warn so the contract failure is visible rather than silent.
if [ "$code_canonical_unreadable" = "0" ] && [ -z "$code_canonical" ]; then
    echo "summarize.sh: warning: $code_skill was readable but yielded no canonical principles; verify the Philosophy heading shape" >&2
fi
if [ "$documentation_canonical_unreadable" = "0" ] && [ -z "$documentation_canonical" ]; then
    echo "summarize.sh: warning: $documentation_skill was readable but yielded no canonical principles; verify the principle-bullet shape under Composition, Grammar/structure/referential integrity, and Validation" >&2
fi
if [ "$wiki_canonical_unreadable" = "0" ] && [ -z "$wiki_canonical_own" ]; then
    echo "summarize.sh: warning: $wiki_skill was readable but yielded no canonical principles; verify the Philosophy heading shape" >&2
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
        wiki)
            case "$severity" in
                important) wiki_important=$((wiki_important + 1)) ;;
                nit) wiki_nit=$((wiki_nit + 1)) ;;
                pre-existing) wiki_preexisting=$((wiki_preexisting + 1)) ;;
            esac
            case "$lens" in
                Structure)  wiki_lens_Structure=$((wiki_lens_Structure + 1)) ;;
                Line)       wiki_lens_Line=$((wiki_lens_Line + 1)) ;;
                Copy)       wiki_lens_Copy=$((wiki_lens_Copy + 1)) ;;
                Accuracy)   wiki_lens_Accuracy=$((wiki_lens_Accuracy + 1)) ;;
                Coherence)  wiki_lens_Coherence=$((wiki_lens_Coherence + 1)) ;;
                References) wiki_lens_References=$((wiki_lens_References + 1)) ;;
            esac
            if [ -n "$principle" ] && [ "$wiki_check_unreadable" = "0" ] && ! is_canonical "$principle" "$wiki_canonical"; then
                wiki_noncanonical+=("$name: $principle")
            fi
            ;;
    esac
done

code_total=$((code_important + code_nit + code_preexisting))
documentation_total=$((documentation_important + documentation_nit + documentation_preexisting))
wiki_total=$((wiki_important + wiki_nit + wiki_preexisting))

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

if [ "$wiki_total" -gt 0 ]; then
    echo "wiki: $wiki_important important, $wiki_nit nit, $wiki_preexisting pre-existing"
    parts=""
    for lens in Structure Line Copy Accuracy Coherence References; do
        var="wiki_lens_${lens}"
        count="${!var}"
        if [ "$count" -gt 0 ]; then
            [ -z "$parts" ] || parts="${parts}, "
            parts="${parts}${count} ${lens}"
        fi
    done
    [ -n "$parts" ] && echo "  by lens: $parts"
fi

total_important=$((code_important + documentation_important + wiki_important))
total_nit=$((code_nit + documentation_nit + wiki_nit))
total_preexisting=$((code_preexisting + documentation_preexisting + wiki_preexisting))

if [ "$total_important" -gt 0 ]; then
    verdict="review blocked on important findings"
elif [ "$total_nit" -gt 0 ]; then
    verdict="review passes; nits optional"
else
    verdict="review passes"
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
    echo "${#documentation_noncanonical[@]} documentation finding(s) cite a non-canonical principle — candidate(s) for writing-prose:"
    for entry in "${documentation_noncanonical[@]}"; do
        echo "  $entry"
    done
fi

if [ "$wiki_total" -gt 0 ] && [ "$wiki_check_unreadable" = "1" ]; then
    if [ -z "$plugin_root" ]; then
        echo "warning: CLAUDE_PLUGIN_ROOT is unset; non-canonical principle check skipped for wiki findings" >&2
    else
        echo "warning: neither $wiki_skill nor $documentation_skill is readable; non-canonical principle check skipped for wiki findings" >&2
    fi
fi

if [ ${#wiki_noncanonical[@]} -gt 0 ]; then
    echo "${#wiki_noncanonical[@]} wiki finding(s) cite a non-canonical principle — candidate(s) for writing-wiki or writing-prose:"
    for entry in "${wiki_noncanonical[@]}"; do
        echo "  $entry"
    done
fi
