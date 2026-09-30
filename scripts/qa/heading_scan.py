#!/usr/bin/env python3
"""Heading skeleton soundness (HS-01..03, HARD) for PROJECT-OMEGA.

The platform renders a TOC and anchor deep-links from heading
structure, so the skeleton every doc carries must be sound:

HS-01  no level skip: a heading may nest at most one level under
       its parent (H2 -> H4 breaks TOC trees and a11y outlines;
       the first heading of a doc is exempt - title/H1 parity is
       title_h1_parity_scan's contract)
HS-02  no empty heading text (`## ` with nothing to render)
HS-03  every doc carries at least one H2 - a flat body has no TOC
       tree at all

Scan is fence-aware and starts after the front-matter block
(FS-01 guarantees it closes within 40 lines).

Born tick-459 at 0/0/0 across 408 docs (KW-03 pattern - prophylactic,
no drain). The birth census also measured 245 duplicate heading
texts across 30 docs (Task/Requirements/Pros/Cons template repeats
under per-item parents: exercises, database columns, case studies).
That class is triaged ACCEPT, deliberately not gated: the repeats
are hierarchical-correct (each sits under its own item parent),
anchor slugs dedup deterministically, and every internal link that
targets one is verified by the anchor gate - renaming would be
churn against a legitimate pattern.

Run over the whole corpus:
    python scripts/qa/heading_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^(```|~~~)")
HEADING = re.compile(r"^(#{1,6})(?:\s+(.*))?$")
FM_CLOSE = re.compile(r"^---\s*$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def body_lines(text: str) -> list[str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return lines
    for i, ln in enumerate(lines[1:40], 1):
        if FM_CLOSE.match(ln):
            return lines[i + 1:]
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(args.root).as_posix()
        n_docs += 1
        infence = False
        prev = 0
        n_h2 = 0
        for ln in body_lines(text):
            if FENCE.match(ln):
                infence = not infence
                continue
            if infence:
                continue
            m = HEADING.match(ln)
            if not m:
                continue
            lvl = len(m.group(1))
            txt = (m.group(2) or "").strip().rstrip("#").strip()
            if not txt:
                findings.append("HS-02 %s: empty heading (`%s`)"
                                % (rel, ln.strip()))
                continue
            if prev and lvl > prev + 1:
                findings.append(
                    "HS-01 %s: level skip H%d -> H%d after %r"
                    % (rel, prev, lvl, txt[:40]))
            if lvl == 2:
                n_h2 += 1
            prev = lvl
        if n_h2 == 0:
            findings.append("HS-03 %s: no H2 in body (flat doc)" % rel)
    for f in findings:
        print("  " + esc(f))
    print("heading_scan: %d docs scanned; %d HS findings - all hard "
          "(skeleton soundness: no level skip, no empty heading, "
          "no flat body; born tick-459 at 0/0/0, KW-03; duplicate-"
          "heading template repeats triaged ACCEPT - see docstring)"
          % (n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
