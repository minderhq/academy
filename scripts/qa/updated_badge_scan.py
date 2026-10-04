#!/usr/bin/env python3
"""Body Last Updated badge parity (UB-01, HARD) for Minder Academy.

The FM Last Updated field is the canonical, gated freshness value
(last_updated_check LU-01/02); several docs also render a display
badge in the header block (`**Last Updated:** YYYY-MM-DD`). Where
that badge exists it must mirror the FM field exactly - a body
badge stuck in February while the doc was edited in September
teaches the learner (and the platform's freshness display, if it
parses body text) the wrong age.

UB-01  every body-level Last Updated line (bold or bare form,
       after the FM block, outside fences) must carry the same
       ISO date as the FM field. A doc with no body badge is fine
       - FM is the data (390/408 docs carry none); this gate locks
       only that the decoration never goes stale.

Born tick-461: the birth census found 14 mismatched badges across
two classes - seven February-frozen display badges (0000-LEARNING-
PATH, GLOSSARY, STYLE-GUIDE, TROUBLESHOOTING-QUICKSTART, the three
GUIDE-* docs, CROSS-REFERENCE-GUIDELINES) that predates the docs'
real September edits, and seven late-September near-misses (09-25
..09-29) where the FM moved on a later tick but the badge did not.
All 14 synced to FM same tick, hard from birth-after-drain.

Run over the whole corpus:
    python scripts/qa/updated_badge_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FM_LU = re.compile(r"^Last Updated:\s*(\d{4}-\d{2}-\d{2})\s*$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
BADGE = re.compile(
    r"^\s*(?:\*\*|__)?Last [Uu]pdated(?:\*\*|__)?\s*:?\s*\**\s*"
    r"(\d{4}-\d{2}-\d{2})\s*$")
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
    n_docs = n_badge = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        head = text.split("\n")[:40]
        fm = None
        for ln in head:
            m = FM_LU.match(ln)
            if m:
                fm = m.group(1)
                break
        if fm is None:
            continue  # LU-01/02 territory, not this gate's
        n_docs += 1
        infence, f_char, f_len = False, "", 0
        for ln in body_lines(text):
            m = FENCE.match(ln)
            if m:
                ch, n = m.group(1)[0], len(m.group(1))
                if infence:
                    if ch == f_char and n >= f_len:
                        infence = False
                else:
                    infence = True
                    f_char, f_len = ch, n
                continue
            if infence:
                continue
            m = BADGE.match(ln)
            if m:
                n_badge += 1
                if m.group(1) != fm:
                    findings.append(
                        "UB-01 %s: body badge %s != FM %s"
                        % (path.relative_to(args.root).as_posix(),
                           m.group(1), fm))
    for f in findings:
        print("  " + esc(f))
    print("updated_badge_scan: %d/%d badge-carrying docs canonical; "
          "%d UB findings - all hard (body Last Updated mirrors FM; "
          "born tick-461: 14 badges synced - 7 February-frozen display "
          "badges, 7 late-Sept near-misses)"
          % (n_badge - len(findings), n_badge, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
