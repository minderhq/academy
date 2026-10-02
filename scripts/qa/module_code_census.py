#!/usr/bin/env python3
"""Module code continuity census (MC-01..03) for PROJECT-OMEGA.

The platform renders the catalog from numeric codes: phase pages
list module dirs in code order, module pages list lessons and guides
in stem order, and the volume spine paginates by VOLUME-N. A skipped
code reads as a missing asset on the platform - learners hit a hole
in the sequence that no navigation explains, and page numbering
silently disagrees with the file tree.

MC-01  within each docs/phases/phase*, the 4-digit module-dir
       prefixes must form a contiguous +100 run starting at
       (phase number)*1000 + 100 (1100, 1200, ... for phase 1).
MC-02  within each module dir, the SET of 4-digit numeric stems
       across top-level *.md (lessons), guides/*.md and
       assessment/*.md must form a contiguous integer range.
       Duplicates are allowed (a lesson and a guide may share a
       code - guides are genre extras of the same lesson number);
       gaps are not (a code reserved by nothing is a hole).
MC-03  docs/volumes/VOLUME-<n>-*.md numbers must form 1..N
       contiguous - the spine paginates by it.

Birth census (2026-10-03): 33 module dirs across 7 phases all
contiguous +100 from their phase base; 33/33 module stem sets
contiguous after the tick-604 drain moved the 1400-llmops guides
1404->1403 (vLLM Production Deployment) and 1405->1404 (TGI
Deployment Guide) to close the 1403 hole that existed from birth
(the only baseline 1403 was experiments/EXP_1403_TGI_TUNING.md,
outside docs/); 7400-memory needed nothing - its lesson 7403 skips
the guide code 7402, and the union set {7401, 7402, 7403} is
contiguous; volume spine 1..7 contiguous. Hard from birth (KW-03).

Run over the whole corpus:
    python scripts/qa/module_code_census.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PHASE_DIR = re.compile(r"^phase(\d+)")
MODULE_DIR = re.compile(r"^(\d{4})-")
STEM = re.compile(r"^(\d{4})")
VOLUME = re.compile(r"^VOLUME-(\d+)-")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def contiguous(nums: list[int]) -> tuple[bool, str]:
    """Sorted ints -> (ok, description of the first gap if any)."""
    s = sorted(nums)
    for a, b in zip(s, s[1:]):
        if b != a + 1:
            return False, f"{a}->{b}"
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_phases = 0
    n_modules = 0
    n_volumes = 0

    phases_dir = args.root / "docs" / "phases"
    for ph in sorted(p for p in phases_dir.iterdir() if p.is_dir()):
        m = PHASE_DIR.match(ph.name)
        if not m:
            continue
        n_phases += 1
        base = int(m.group(1)) * 1000 + 100
        mods = sorted(int(MODULE_DIR.match(d.name).group(1))
                      for d in ph.iterdir()
                      if d.is_dir() and MODULE_DIR.match(d.name))
        if not mods:
            continue
        ok, gap = contiguous([(v - base) // 100 + 1 for v in mods])
        if not ok or mods[0] != base:
            why = f"start {mods[0]} want {base}" if mods[0] != base \
                else f"gap {gap}"
            findings.append(f"{ph.name}: MC-01 module codes not "
                            f"contiguous ({why})")
        for md in sorted(p for p in ph.iterdir()
                         if p.is_dir() and MODULE_DIR.match(p.name)):
            n_modules += 1
            stems = []
            for sub in (".", "guides", "assessment"):
                d = md / sub
                if not d.is_dir():
                    continue
                for f in d.glob("*.md"):
                    ms = STEM.match(f.name)
                    if ms:
                        stems.append(int(ms.group(1)))
            if not stems:
                continue
            ok, gap = contiguous(stems)
            if not ok:
                findings.append(
                    f"{ph.name}/{md.name}: MC-02 module stem set not "
                    f"contiguous (gap {gap})")

    vol_dir = args.root / "docs" / "volumes"
    vols = sorted(int(VOLUME.match(f.name).group(1))
                  for f in vol_dir.glob("VOLUME-*-*.md")
                  if VOLUME.match(f.name))
    if vols and vols != list(range(1, len(vols) + 1)):
        findings.append("docs/volumes: MC-03 volume spine not "
                        "contiguous")
        n_volumes = len(vols)
    elif vols:
        n_volumes = len(vols)

    by_class = [sum(1 for f in findings if f" MC-0{i} " in f)
                for i in (1, 2, 3)]
    for f in findings:
        print(esc(f), file=sys.stderr)
    print(f"module_code_census: MC-01={by_class[0]} MC-02={by_class[1]} "
          f"MC-03={by_class[2]} across {n_phases} phases / {n_modules} "
          f"modules / {n_volumes} volumes (hard gate; module codes "
          f"contiguous by phase, lesson+guide stem sets contiguous by "
          f"module, volume spine contiguous)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
