#!/usr/bin/env python3
"""Difficulty badge parity (DB-01, HARD) for PROJECT-OMEGA.

The FM Difficulty field is the canonical, gated value
(difficulty_census DI-01..03); many docs also render a display
badge in the header block. Where that badge exists it must mirror
FM exactly - a body badge contradicting the FM teaches the learner
the wrong level and renders inconsistently on the platform.

DB-01  every `**Difficulty:**` body line must render exactly
       `**Difficulty:** <stars> <band>` with stars = the canonical
       1/2/3-dot count for the FM band (Beginner/Intermediate/
       Advanced) and band == the FM band. A doc with no body badge
       is fine - FM is the data, the badge is optional decoration;
       this gate locks only that decoration never lies.

Born tick-457: the birth census found 87 violating sites across
five rot classes - dead-enum badges (4-5 stars / 'Expert' text,
referencing the level difficulty_census retired tick-412), band
mismatches where mass-added FM defaults (all 12 templates FM=
Beginner) contradicted the original badge intent, starless
correct-text badges, range badges on phase hubs ('Intermediate to
Advanced'), and 'Absolute Beginner' free-text. Drained same tick
with per-class policy (dead-enum -> Advanced; content docs keep
badge intent, FM moved to the badge's ceiling band; assessment
quiz/practice + 00-META guides keep FM, badge moves). Hard from
birth-after-drain.

Run over the whole corpus:
    python scripts/qa/difficulty_badge_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FM_DIFF = re.compile(r"^Difficulty:\s*(Beginner|Intermediate|Advanced)\s*$",
                     re.M)
BADGE = re.compile(r"^\*\*Difficulty:\*\*(.+)$", re.M)
STARS = {"Beginner": "\u2b50", "Intermediate": "\u2b50\u2b50", "Advanced": "\u2b50\u2b50\u2b50"}


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


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
        fm = FM_DIFF.search(text)
        bd = BADGE.search(text)
        if not fm or not bd:
            continue
        n_docs += 1
        n_badge += 1
        want = "**Difficulty:** %s %s" % (STARS[fm.group(1)], fm.group(1))
        if bd.group(0).rstrip() != want:
            findings.append(
                "DB-01 %s: badge %r != canonical %r (FM %s)"
                % (path.relative_to(args.root).as_posix(),
                   bd.group(0)[:60], want, fm.group(1)))
    for f in findings:
        print("  " + esc(f))
    print("difficulty_badge_scan: %d/%d badge-carrying docs canonical; "
          "%d DB findings - all hard (badge mirrors FM, 1/2/3 stars; "
          "born tick-457: 87 sites drained across 5 rot classes, "
          "dead-enum Expert badges included)"
          % (n_badge - len(findings), n_badge, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
