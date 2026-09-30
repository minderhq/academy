#!/usr/bin/env python3
"""Pitfalls item-shape standardization (PS-01..02, HARD) for PROJECT-OMEGA.

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
prefix. Checkpoints are excluded (CK-09 in checkpoint_coverage_scan
governs their "N. **Name:**" lists).

Born tick-482, born-at-zero after the same-tick drain: census found
subsection headers in 4 shapes (plain "### Name", "### (warning-emoji)
Name", "(x-emoji) ### Pitfall N: Name", canonical) across 18 rich
files, and 17 module-group READMEs carrying thin unnumbered
"- **Name**: advice" bullets (83 bullets) - all canonized same tick.
Section scanning is fence-aware: bash comment lines inside code
fences are not headers (the tick-482 census's own first draft broke
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

FENCE = re.compile(r"^(```|~~~)")
SUB = re.compile(r"^Pitfall\s+(\d+):\s*(\S.*)$")
ITEM = re.compile(r"^\s*\d+\.\s+\*\*[^*]+:\*\*")
TAB_HEAD = re.compile(r"^\|\s*Pitfall\b", re.IGNORECASE)
TAB_SEP = re.compile(r"^\|[\s:|-]+\|?\s*$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def analyze(text: str) -> tuple[int, list[str]]:
    """One section -> (structured-item count, bad subsection titles)."""
    lines = text.split("\n")
    items = 0
    bad = []
    n_sub = 0
    in_tab = False
    fence = False
    for ln in lines:
        if FENCE.match(ln.strip()):
            fence = not fence
            continue
        if fence:
            continue
        if re.match(r"^###\s", ln):
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
            items += 1
        elif TAB_HEAD.match(ln):
            in_tab = True
            items += 1
        elif in_tab and ln.startswith("|") and not TAB_SEP.match(ln):
            items += 1
        elif ln.strip() and not ln.startswith("|"):
            in_tab = False
    return items, bad


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
            fence = False
            for l2 in lines[i + 1:]:
                if FENCE.match(l2.strip()):
                    fence = not fence
                    continue
                if fence:
                    continue
                h = re.match(r"^(#{1,4})\s", l2)
                if h and len(h.group(1)) <= lvl:
                    break
                body.append(l2)
            items, bad = analyze("\n".join(body))
            if items < 3:
                findings.append(
                    "PS-01 %s: pitfalls section '%s' carries %d structured "
                    "items - below the 3-item floor" % (rel, m.group(2).strip(),
                                                        items))
            for b in bad:
                findings.append(
                    "PS-02 %s: pitfalls subsection not in canonical "
                    "'### Pitfall N: Name' shape: %s" % (rel, b))

    for f in findings:
        print("  " + esc(f))
    print("pitfall_shape_scan: %d pitfalls sections (non-checkpoint); "
          "%d findings - all hard (PS-01 below the 3-structured-item "
          "floor / PS-02 subsection not in canonical '### Pitfall N: "
          "Name' shape; born tick-482 after the 85-header + 83-bullet "
          "shape standardization drain across 35 files)" % (n_secs,
                                                            len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
