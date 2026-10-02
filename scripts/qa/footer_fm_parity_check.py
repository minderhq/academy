#!/usr/bin/env python3
"""footer_fm_parity_check - EOF metadata footers must not contradict the
front matter they visually mirror (FF-01..04).

The blind spot (tick-573): a THIRD metadata surface lives at the end of
some docs - bold-field rows after the final ``---`` separator (footer).
No gate read it, so five lab footers drifted against the FM the rest of
the fleet proves true (LI-06 anchors labs' FM Estimated Time to the
Exercise/Part sum): LAB-009/011/012/013/014 all promised a range like
"8-10 hours" against FM "12 hours", and three of them claimed a
"**** Expert" tier that does not exist anywhere in the corpus - the FM
Difficulty vocabulary is exactly three tiers (Advanced 220 /
Intermediate 117 / Beginner 71 across all docs), so Expert is illegal
vocabulary, not a stricter tier.

The census before the lock: 28 files carry footers (5 labs, 13
solutions, 12 templates, 2 tutorials) and 23 of them already mirror FM
exactly - the contract below is what the majority obeys, not a new
invention. TUT-006 is the clean mirror proof (footer Time Estimate
"60 minutes" == FM); the 13 solution and 12 template footers all match
their FM Difficulty word-for-word and star-for-star, proving the star
map is the tier index: Beginner=1, Intermediate=2, Advanced=3.

Rules (all conditional - footer presence is heterogeneous by design:
10 of 15 labs and 13 of 15 tutorials have no footer at all, and
SOLUTION-LAB-010/011 sit footerless beside 13 footer-carrying siblings,
so "every file must carry a footer" would be fiction):
- FF-01 a footer Difficulty value, stars stripped, must equal the FM
  Difficulty verbatim (a footer with no FM Difficulty also fires -
  a dangling claim).
- FF-02 the footer star count must equal TIER_STARS[FM Difficulty]
  (the tier-index map above); an FM tier outside the map fires.
- FF-03 a footer "Time Estimate"/"Duration" value must equal the FM
  Estimated Time verbatim, checked only when the FM actually carries
  Estimated Time - where FM has none (all 12 templates) the footer IS
  the only time claim and cannot contradict anything.
- FF-04 a footer Prerequisites value on an FM with an empty list must
  be exactly "None" (casefold) - no flourish punctuation ("None!"),
  and on a non-empty FM list every bracketed token in the footer must
  appear in the list.

Out of scope by design, documented here so the boundary is policy not
oversight: body-header summary blocks under the H1 (TUTORIAL-000's
"**Time:** 15-20 hours" elaboration layer - ranges and advice are
pedagogy, the footer is the budget) and blockquote callouts (the
"> Info **Time Estimate:**" prose note in the same file) are never
read; "**Lab:**"/"**Skills:**" id/keyword footer lines are not claim
fields; the footer region is fence-aware so a fenced example cannot
forge one, and a mid-body thematic break cannot swallow the region -
only the separator after the front-matter close starts it.

Born at 14 findings across 6 files (the drain followed in the same
tick): the five lab footers (three ranged against LI-06-proven hours,
three carrying the illegal Expert tier) plus TUTORIAL-000 (range-vs-
point Duration, starless tier, the "None!" punctuation).

Usage:
    python scripts/qa/footer_fm_parity_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FOOTER_FIELD = re.compile(
    r"^\*\*(Time Estimate|Duration|Difficulty|Prerequisites)"
    r"(?::\*\*|\*\*:|:)\s*(.+?)\s*$"
)
FM_DIFFICULTY = re.compile(r"^Difficulty:\s*(.+?)\s*$", re.M)
FM_EST_TIME = re.compile(r"^Estimated Time:\s*(.+?)\s*$", re.M)
FM_PREREQS = re.compile(r"^Prerequisites:\s*(.+?)\s*$", re.M)
SEP = re.compile(r"^---\s*$")
FENCE = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")
STARS = "\u2b50"
TIER_STARS = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}


def parse_fm(text: str) -> str:
    """The front-matter block text (between the opening --- and its
    close), or "" when the file has no front matter."""
    lines = text.split("\n")
    if not lines or not SEP.match(lines[0]):
        return ""
    for i in range(1, len(lines)):
        if SEP.match(lines[i]):
            return "\n".join(lines[1:i])
    return ""


def footer_fields(text: str) -> list[tuple[str, str]]:
    """(field, value) claim rows in the EOF footer region - the block
    after the LAST fence-aware thematic break beyond the FM close.
    Blockquote lines are skipped (callout prose is not metadata) and
    fence interiors are skipped (a fenced example cannot forge fields).
    """
    fm_close = 0
    lines = text.split("\n")
    if lines and SEP.match(lines[0]):
        for i in range(1, len(lines)):
            if SEP.match(lines[i]):
                fm_close = i
                break
        else:
            return []
    last_sep = -1
    in_fence = False
    for i, line in enumerate(lines):
        if i <= fm_close:
            continue
        f = FENCE.match(line)
        if f:
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if SEP.match(line):
            last_sep = i
    if last_sep < 0:
        return []
    fields: list[tuple[str, str]] = []
    in_fence = False
    for line in lines[last_sep + 1:]:
        f = FENCE.match(line)
        if f:
            in_fence = not in_fence
            continue
        if in_fence or line.lstrip().startswith(">"):
            continue
        m = FOOTER_FIELD.match(line)
        if m:
            fields.append((m.group(1), m.group(2)))
    return fields


def check(root: Path) -> list[str]:
    findings: list[str] = []
    lr = root / "docs" / "learning-resources"
    if not lr.exists():
        print("footer_fm_parity_check: docs/learning-resources missing")
        return findings
    for p in sorted(lr.rglob("*.md")):
        text = p.read_text(encoding="utf-8")
        fm = parse_fm(text)
        if not fm:
            continue
        fields = footer_fields(text)
        if not fields:
            continue
        rel = p.relative_to(root).as_posix()
        fm_diff_m = FM_DIFFICULTY.search(fm)
        fm_diff = fm_diff_m.group(1) if fm_diff_m else None
        fm_et_m = FM_EST_TIME.search(fm)
        fm_et = fm_et_m.group(1) if fm_et_m else None
        fm_pr_m = FM_PREREQS.search(fm)
        fm_prereqs: list[str] = []
        if fm_pr_m and fm_pr_m.group(1).strip() not in ("[]", ""):
            fm_prereqs = [
                t.strip().strip("'\"")
                for t in fm_pr_m.group(1).strip("[]").split(",")
                if t.strip()
            ]
        for field, value in fields:
            if field == "Difficulty":
                if fm_diff is None:
                    findings.append(
                        f"FF-01 {rel}: footer Difficulty \"{value}\" but "
                        "front matter has no Difficulty")
                    continue
                word = value.lstrip(STARS).strip()
                if word != fm_diff:
                    findings.append(
                        f"FF-01 {rel}: footer Difficulty \"{value}\" != "
                        f"front matter \"{fm_diff}\"")
                stars = value.count(STARS)
                want = TIER_STARS.get(fm_diff)
                if want is None:
                    findings.append(
                        f"FF-02 {rel}: front matter tier \"{fm_diff}\" is "
                        f"outside the corpus vocabulary "
                        f"{sorted(TIER_STARS)}")
                elif stars != want:
                    findings.append(
                        f"FF-02 {rel}: footer carries {stars} stars but "
                        f"tier \"{fm_diff}\" is {want} "
                        f"(star map = tier index)")
            elif field in ("Time Estimate", "Duration"):
                if fm_et is not None and value != fm_et:
                    findings.append(
                        f"FF-03 {rel}: footer {field} \"{value}\" != front "
                        f"matter Estimated Time \"{fm_et}\"")
            elif field == "Prerequisites":
                if not fm_prereqs:
                    if value.casefold() != "none":
                        findings.append(
                            f"FF-04 {rel}: footer Prerequisites \"{value}\" "
                            "but front matter list is empty (expect exactly "
                            "\"None\" - flourish belongs in prose)")
                else:
                    if re.findall(r"\[([^\]]+)\]", value):
                        findings.append(
                            f"FF-04 {rel}: footer Prerequisites \"{value}\" "
                            "claims none-of-the-brackets form; the Related "
                            "standard keeps tokens in the front matter")
                        continue
                    low = value.casefold()
                    if low.strip("!").strip() == "none":
                        findings.append(
                            f"FF-04 {rel}: footer Prerequisites "
                            f"\"{value}\" contradicts non-empty front "
                            f"matter list {fm_prereqs}")
                    elif not any(tok.lower() in low for tok in fm_prereqs):
                        findings.append(
                            f"FF-04 {rel}: footer Prerequisites \"{value}\" "
                            f"names none of the front-matter list "
                            f"{fm_prereqs}")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", help="repo root")
    args = ap.parse_args()
    findings = check(Path(args.root))
    if findings:
        for f in findings:
            print(f)
        print(f"footer_fm_parity_check: {len(findings)} findings "
              "(FF-01..04) - footers contradicting front matter")
        return 1
    print("footer_fm_parity_check: 0 findings (FF-01..04) - footers "
          "mirror front matter (where present)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
