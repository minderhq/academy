#!/usr/bin/env python3
"""Difficulty distribution census (DX-01) for PROJECT-OMEGA.

difficulty_census (DI-01..03) locks that every doc carries an exact
Difficulty value, but not what the values TOGETHER say. The platform
uses Difficulty as a filter and a sequence dimension: a learner
picks a track and expects the ramp to climb - if phase 5 is full of
Beginner lessons while phase 2 is wall-to-wall Advanced, the filter
exists but the curriculum it filters is not coherent.

This census reads the distribution per phase (the path spine):

    DX-01  a doc whose Difficulty is >= 2 bands away from its
           phase's median (a Beginner lesson inside an Advanced
           wall, or the reverse) - the per-doc anomaly candidates

REPORT-ONLY at birth (exit 0 always): the corpus is measured first,
2026-09-30 - 408 docs, 93 Beginner / 144 Intermediate / 171
Advanced. Whether the ramp is sane and which outliers are by-design
(enrichment lessons, review checkpoints) is a curriculum judgment
that needs the numbers in front of it, not a hard gate yet.

Docs outside docs/phases/ carry no phase position and are listed
visibly, never silently dropped (house rule).

Run over the whole corpus:
    python scripts/qa/difficulty_distribution_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
DI_FIELD = re.compile(r"^Difficulty:(.*)$")
PHASE_DIR = re.compile(r"^docs/phases/phase(\d+)-")
LEVELS = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
NAMES = {1: "Beginner", 2: "Intermediate", 3: "Advanced"}


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def difficulty(lines: list[str]) -> str | None:
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = DI_FIELD.match(raw)
                if m:
                    return m.group(1).strip()
            return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    phases: dict[int, list[tuple[str, int]]] = {}
    n_outside = 0
    outside: list[str] = []
    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        val = difficulty(lines)
        if val is None:
            continue
        rel = path.relative_to(args.root).as_posix()
        pm = PHASE_DIR.match(rel)
        if not pm:
            n_outside += 1
            outside.append("%s (%s)" % (rel, esc(val)))
            continue
        lvl = LEVELS.get(val)
        if lvl is None:
            continue  # DI-01 territory, already a hard gate elsewhere
        phases.setdefault(int(pm.group(1)), []).append((rel, lvl))

    total = sum(len(v) for v in phases.values())
    print("difficulty_distribution_scan: %d in-phase docs across %d "
          "phases, %d docs outside phases (listed below)"
          % (total, len(phases), n_outside))

    anomalies: list[tuple[float, str, int, int]] = []
    for pnum in sorted(phases):
        docs = phases[pnum]
        n = len(docs)
        counts = [0, 0, 0]
        for _, lvl in docs:
            counts[lvl - 1] += 1
        med_idx = sorted(lvl for _, lvl in docs)[n // 2]
        print("  phase-%d: %3d docs  B %2d / I %2d / A %3d  "
              "(median %s)" % (pnum, n, counts[0], counts[1], counts[2],
                               NAMES[med_idx]))
        for rel, lvl in docs:
            if abs(lvl - med_idx) >= 2:
                anomalies.append((abs(lvl - med_idx), rel, lvl, med_idx))

    if anomalies:
        print("  DX-01 >=2 bands from phase median (%d docs):" % len(anomalies))
        for gap, rel, lvl, med in sorted(anomalies, reverse=True):
            print("    %s in median-%s phase (is %s)"
                  % (esc(rel), NAMES[med], NAMES[lvl]))
    if n_outside:
        print("  outside phases, no path position (%d docs):" % n_outside)
        for line in outside:
            print("    " + esc(line))
    print("difficulty_distribution_scan: %d DX-01 anomaly candidates "
          "- report-only census" % len(anomalies))
    return 0


if __name__ == "__main__":
    sys.exit(main())
