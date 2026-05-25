Template:

```
# <one-line title>

<one-line summary>

## <a section title>
<content>

## <another section title>
<more content>
```

Body shape (H2 sections, titles and content) is yours. The fixed line-position contract: line 1 is the H1 title, line 2 is blank, line 3 is the one-line summary, line 4 is blank, line 5 onward is the body. This positional convention is the scanner contract — `Read limit=3` pulls the headline; `Grep -A 2 '^# '` over the artifact directory pulls every title-and-summary pair without parsing.

Defects:

- No one-line summary under the H1. Every artifact opens with title then summary.
- Body restates the summary verbatim. The summary is the lede; the body is the evidence.
- Title and slug disagree. Title and filename are one fact in two places; they agree.
- Covers two distinct subjects. Split it — one artifact per subject.
