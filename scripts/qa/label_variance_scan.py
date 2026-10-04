#!/usr/bin/env python3
"""Bold-label variance (LV-01..02, HARD) for Minder Academy.

Bold paragraph / list-item labels ("**X:**" at line start, list items
included) are a content family the platform renders as callout leads.
Two rules keep their forms uniform corpus-wide:

  LV-01  the eight canonized keys must use exactly their canonical
         surface form (corpus-vote winners, tick-484):

           Estimated Time / What You'll Learn / Best For /
           Troubleshooting / Requirements / Real-World Example /
           Verification / Note

         (all plain Title-case - the two emoji outliers lived in one
         file, LAB-000, and the tick-482 canon strips emoji from
         structure labels)
  LV-02  any OTHER label key (emoji/space/case-normalized) that has
         drifted into 2+ surface forms corpus-wide - new variance
         caught at birth, whatever the label

Quiz/worksheet content labels (answer, solution, ...) are unaffected:
they are single-form keys and LV-02 only fires when one key splits.
Frontmatter `Key:` lines are not bold and out of scope; `**X**:` with
the colon outside the bold is a different form, not captured (0
corpus-wide at birth, un-gated until a class appears).

Born tick-484, born-at-zero after the same-tick drain: census found
8 multi-surface keys (34 minority labels across 14 files - lowercase
`Estimated time` x5, `What you'll learn` x7, `Best for` x8, emoji
`(+)(!) Troubleshooting`/`Verification` x8 in LAB-000, `REQUIREMENTS`
x2, `Real-world example` x1, `NOTE` x3); all renamed to the vote
winners. Label capture is fence- and table-aware.

Run over the whole corpus:
    python scripts/qa/label_variance_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
LAB = re.compile(r"^((?:-\s+)?\*\*)([^*]+?)(:\*\*)")
TAB_SEP = re.compile(r"^\|[\s:|-]+\|?\s*$")
EMO = r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\s]+"

CANON_SURFACES = (
    "Estimated Time", "What You'll Learn", "Best For", "Troubleshooting",
    "Requirements", "Real-World Example", "Verification", "Note")
CANON = {re.sub(EMO, "", s).lower(): s for s in CANON_SURFACES}


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_labels = 0
    surfaces: dict[str, dict[str, int]] = {}
    where: dict[str, dict[str, str]] = {}
    for f in sorted((args.root / "docs").rglob("*.md")):
        rel = os.path.relpath(f, args.root).replace("\\", "/")
        lines = f.read_text(encoding="utf-8", errors="replace").split("\n")
        fence, f_char, f_len = False, "", 0
        in_tab = False
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
            if TAB_SEP.match(ln):
                continue
            if ln.startswith("|"):
                in_tab = True
                continue
            if ln.strip() and not ln.startswith("|"):
                in_tab = False
            if in_tab:
                continue
            m = LAB.match(ln)
            if not m:
                continue
            n_labels += 1
            surf = m.group(2)
            key = re.sub(EMO, "", surf).lower()
            if key in CANON:
                if surf != CANON[key]:
                    findings.append(
                        "LV-01 %s: label '**%s:**' - canonized key uses "
                        "the fixed form '**%s:**'" % (rel, surf,
                                                      CANON[key]))
            else:
                surfaces.setdefault(key, {}).setdefault(surf, 0)
                surfaces[key][surf] += 1
                where.setdefault(key, {}).setdefault(surf, rel)

    for key, forms in sorted(surfaces.items()):
        if len(forms) > 1:
            for surf in sorted(forms):
                findings.append(
                    "LV-02 %s: label key has drifted to %d surface "
                    "forms; '**%s:**' seen %d time(s) here - pick one "
                    "form corpus-wide" % (where[key][surf], len(forms),
                                          surf, forms[surf]))

    for f in findings:
        print("  " + esc(f))
    print("label_variance_scan: %d bold labels; %d findings - all hard "
          "(LV-01 canonized key off its fixed form / LV-02 label key "
          "drifted to 2+ surface forms; born tick-484 after the "
          "34-label drain across 14 files)" % (n_labels, len(findings)))
    return 1 if findings else 0


def rel_placeholder(key: str, surf: str) -> str:
    """LV-02 is a corpus-level rule; findings carry the label not a file."""
    return "<corpus> key='%s'" % key


if __name__ == "__main__":
    sys.exit(main())
