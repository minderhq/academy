#!/usr/bin/env python3
"""Pitfalls item-shape standardization (PS-01..04, HARD) for Minder Academy.

Every non-checkpoint doc with a pitfalls section (the "## ...Pitfall..."
review block in phase READMEs, module-group READMEs, module files,
industry and volume pages) must carry at least 3 structured pitfall
items in one of the corpus shapes:

  - numbered one-liners   "N. **Name:** advice"   (checkpoint standard)
  - numbered subsections  "### Pitfall N: Name"   (the rich wrong/right
                                                  example blocks)
  - pitfall table         "| Pitfall | ... |"     (numbered-outline genre)

and every "### " subsection inside a pitfalls section must be in the
canonical "### Pitfall N: Name" form - sequential numbering, no emoji
prefix. Inside a pitfalls section, bold paragraph labels ("**X:**" at
line start) must be the canonical pair **Pitfall:** / **Solution:**
(PS-03) - the corpus had **Problem:** x22 and **Fix:** x3 alongside
them, canonized same tick. PS-04 (tick-634) owns the written
numbering of the numbered one-liner items: PS-01 reads only the
item COUNT via ITEM (the number values are dropped at match time),
so a gap, duplicate or restart inside a run served the learner a
broken numbered review list while every check stayed clean - the
tick-631 partition shape, the 3-item floor stays PS-01's, the
numbering inside the count is PS-04's. Checkpoints are excluded
(CK-09/CK-10 in checkpoint_coverage_scan govern their "N. **Name:**"
lists).

Born tick-482, born-at-zero after the same-tick drain: census found
subsection headers in 4 shapes (plain "### Name", "### (warning-emoji)
Name", "(x-emoji) ### Pitfall N: Name", canonical) across 18 rich
files, and 17 module-group READMEs carrying thin unnumbered
"- **Name**: advice" bullets (83 bullets) - all canonized same tick.
PS-03 born tick-483, born-at-zero after the 25-label drain across 6
files (19 **Problem:** + 3 **Fix:** + 3 more **Problem:**). Section
scanning is fence-aware: bash comment lines inside code fences are
not headers or labels (the tick-482 census's own first draft broke
on "# Wrong:" fence comments).

Run over the whole corpus:
    python scripts/qa/pitfall_shape_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
SUB = re.compile(r"^Pitfall\s+(\d+):\s*(\S.*)$")
ITEM = re.compile(r"^\s*\d+\.\s+\*\*[^*]+:\*\*")
TAB_HEAD = re.compile(r"^\|\s*Pitfall\b", re.IGNORECASE)
TAB_SEP = re.compile(r"^\|[\s:|-]+\|?\s*$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


LABELS = ("Pitfall", "Solution")


def analyze(
        text: str) -> tuple[int, list[str], list[str], list[str]]:
    """One section -> (item count, bad subsections, bad one-liner
    numbering, non-canonical labels)."""
    lines = text.split("\n")
    items = 0
    bad = []
    bad_lab = []
    bad_num = []
    n_sub = 0
    in_tab = False
    fence, f_char, f_len = False, "", 0
    run: list[int] = []

    def end_run() -> None:
        if run and run != list(range(1, len(run) + 1)):
            bad_num.append("items are numbered %s, expected 1..%d" % (
                ", ".join(str(n) for n in run), len(run)))
        run.clear()

    for ln in lines:
        m = FENCE.match(ln.strip())
        if m:
            ch, n = m.group(1)[0], len(m.group(1))
            if fence:
                if ch == f_char and n >= f_len:
                    fence = False
            else:
                fence = True
                f_char, f_len = ch, n
            continue
        if fence:
            continue
        if re.match(r"^###\s", ln):
            end_run()
            m = SUB.match(ln.lstrip("#").strip())
            if m:
                n_sub += 1
                if int(m.group(1)) != n_sub:
                    bad.append(ln.lstrip("#").strip()
                               + " (out of sequence)")
            else:
                bad.append(ln.lstrip("#").strip())
            items += 1
        elif ITEM.match(ln):
            run.append(int(re.match(r"^\s*(\d+)\.", ln).group(1)))
            items += 1
        elif TAB_HEAD.match(ln):
            end_run()
            in_tab = True
            items += 1
        elif in_tab and ln.startswith("|") and not TAB_SEP.match(ln):
            items += 1
        elif ln.strip() and not ln.startswith("|"):
            end_run()
            in_tab = False
            lm = re.match(r"^\*\*([A-Za-z][A-Za-z ]*):\*\*", ln)
            if lm and lm.group(1) not in LABELS:
                bad_lab.append("**%s:**" % lm.group(1))
    end_run()
    return items, bad, bad_num, bad_lab


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_secs = 0
    for f in sorted((args.root / "docs").rglob("*.md")):
        rel = os.path.relpath(f, args.root).replace("\\", "/")
        if re.match(r"docs/phases/phase[^/]+/CHECKPOINT\.md$", rel):
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.split("\n")
        for i, ln in enumerate(lines):
            m = re.match(r"^(#{2,3})\s+(.*pitfall.*)$", ln, re.IGNORECASE)
            if not m or re.search(r"pitfall\s*\d+", m.group(2).lower()):
                continue
            n_secs += 1
            lvl = len(m.group(1))
            body: list[str] = []
            fence, f_char, f_len = False, "", 0
            for l2 in lines[i + 1:]:
                m = FENCE.match(l2.strip())
                if m:
                    ch, n = m.group(1)[0], len(m.group(1))
                    if fence:
                        if ch == f_char and n >= f_len:
                            fence = False
                    else:
                        fence = True
                        f_char, f_len = ch, n
                    continue
                if fence:
                    continue
                h = re.match(r"^(#{1,4})\s", l2)
                if h and len(h.group(1)) <= lvl:
                    break
                body.append(l2)
            items, bad, bad_num, bad_lab = analyze("\n".join(body))
            if items < 3:
                findings.append(
                    "PS-01 %s: pitfalls section '%s' carries %d structured "
                    "items - below the 3-item floor" % (rel, m.group(2).strip(),
                                                        items))
            for b in bad:
                findings.append(
                    "PS-02 %s: pitfalls subsection not in canonical "
                    "'### Pitfall N: Name' shape: %s" % (rel, b))
            for lab in sorted(set(bad_lab)):
                findings.append(
                    "PS-03 %s: pitfalls label '%s' not in the canonical "
                    "set (**Pitfall:** / **Solution:**)" % (rel, lab))
            for bn in bad_num:
                findings.append(
                    "PS-04 %s: pitfalls section '%s' one-liner %s"
                    % (rel, m.group(2).strip(), bn))

    for f in findings:
        print("  " + esc(f))
    print("pitfall_shape_scan: %d pitfalls sections (non-checkpoint); "
          "%d findings - all hard (PS-01 below the 3-structured-item "
          "floor / PS-02 subsection not in canonical '### Pitfall N: "
          "Name' shape / PS-03 inner label outside **Pitfall:** / "
          "**Solution:** / PS-04 one-liner items numbered out of 1..K "
          "order; born tick-482 after the 85-header + 83-bullet "
          "shape drain, PS-03 tick-483 after the 25-label canonization "
          "drain, PS-04 tick-634 after the 17-run all-1..K census)"
          % (n_secs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
