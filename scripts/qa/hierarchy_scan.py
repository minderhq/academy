#!/usr/bin/env python3
"""Catalog placement scan (HZ-01..03) for Minder Academy.

The platform builds its catalog hierarchy (phase -> module ->
lesson) from the FM Phase / Module declarations, while the disk
layout under docs/phases/ is the ground truth those declarations
denormalize - when the copy drifts from the path, the catalog
files a lesson under the wrong phase or module and the learning
path breaks silently, with linkcheck green.

Census tick-609: 260 docs under docs/phases/, 114 carry the
pair (93 direct lesson files + 21 guides/ subtree docs), the
value grammar is uniform bare-digit Phase plus bare 4-digit
Module ('3', '3200') across all 7 phases, 0 Phase/Module
disagreements with the disk across all carriers, and every
content doc carries - the non-carrying classes are keyset
forbidden or keyset distinct by design: the 66 assessment/
banks (CC-20's 9-field assessment keyset admits no placement
fields - a past drain deleted exactly those 4 FM lines from
2300's PRACTICE/QUIZ pair; the catalog files them by their
module-attached directory and their NNNN- Document ID prefix),
the 33 PREREQUISITES.md module support files (their own keyset
shape), and the README.md files.

HZ-01  every FM Phase value must parse as an integer equal to
       the phaseN directory number the doc sits under - a
       non-numeric value, or a value naming a different phase
       than the path, misfiles the lesson in the catalog.

HZ-02  every FM Module value must be a bare 4-digit code equal
       to the NNNN- module directory the doc sits under - the
       module is the catalog's grouping row; a drifted code
       shows the lesson inside the wrong module page.

HZ-03  every module-scoped content doc (any depth under its
       NNNN- module directory, filename neither README.md nor
       PREREQUISITES.md, not inside assessment/) must carry
       BOTH Phase and Module - a lesson or guide whose
       placement the platform cannot reconstruct from prose
       is content the catalog cannot file. A new content
       subtree inherits the duty automatically.

HARD GATE - exit 1 on any finding. All three clauses born
tick-609 at zero (no drain: the census froze the class the
moment it was named).

Run over the whole corpus:
    python scripts/qa/hierarchy_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
PHASE_FIELD = re.compile(r"^Phase:(.*)$")
MODULE_FIELD = re.compile(r"^Module:(.*)$")
PHASE_DIR = re.compile(r"^phase(\d+)-")
MODULE_DIR = re.compile(r"^(\d{4})-")
EXEMPT_ROOT = {"README.md", "PREREQUISITES.md"}
ASSESSMENT_DIR = "assessment"


def fm_field(lines: list[str], field: re.Pattern[str]) -> str | None:
    """Top-level FM value for the field regex, or None."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = field.match(raw)
                if m:
                    return m.group(1).strip()
            return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    phases_dir = args.root / "docs" / "phases"
    paths = sorted(phases_dir.rglob("*.md"))

    findings: list[str] = []
    n_carry = 0
    shapes: Counter[str] = Counter()

    for path in paths:
        rel = path.relative_to(args.root).as_posix()
        parts = path.relative_to(phases_dir).parts
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        ph = fm_field(lines, PHASE_FIELD)
        md = fm_field(lines, MODULE_FIELD)
        if ph is not None or md is not None:
            n_carry += 1
        pm = PHASE_DIR.match(parts[0]) if parts else None
        mm = MODULE_DIR.match(parts[1]) if len(parts) >= 2 else None
        tph = pm.group(1) if pm else None
        tmd = mm.group(1) if mm else None
        if ph is not None:
            shapes[f"ph={ph!r}"] += 1
            # HZ-01 - phase placement truth
            if tph is None:
                findings.append(
                    f"{rel}: HZ-01 phase placement unresolvable "
                    f"(FM Phase {ph!r} but no phaseN- directory "
                    f"resolves above the file)")
            elif not ph.isdigit() or ph != tph:
                findings.append(
                    f"{rel}: HZ-01 phase placement drift (FM Phase "
                    f"{ph!r} vs disk phase{tph}; the catalog files "
                    f"the lesson by the FM, the learner walks the "
                    f"disk)")
        if md is not None:
            shapes[f"md={md!r}"] += 1
            # HZ-02 - module placement truth
            if tmd is None:
                findings.append(
                    f"{rel}: HZ-02 module placement unresolvable "
                    f"(FM Module {md!r} but no NNNN- module "
                    f"directory resolves above the file)")
            elif not re.fullmatch(r"\d{4}", md) or md != tmd:
                findings.append(
                    f"{rel}: HZ-02 module placement drift (FM "
                    f"Module {md!r} vs disk {tmd}; the module row "
                    f"the catalog shows would be the wrong one)")
        # HZ-03 - module-scoped content docs must declare their
        # placement (README/PREREQUISITES keyset classes and the
        # CC-20 assessment/ banks are by-design exempt)
        if (len(parts) >= 3 and parts[-1] not in EXEMPT_ROOT
                and parts[2] != ASSESSMENT_DIR
                and (ph is None or md is None)):
            missing = [f for f, v in (("Phase", ph), ("Module", md))
                       if v is None]
            findings.append(
                f"{rel}: HZ-03 placement undeclared (module-root "
                f"doc carries no {', '.join(missing)}; the catalog "
                f"cannot file it from prose)")

    hz01 = sum(1 for f in findings if " HZ-01 " in f)
    hz02 = sum(1 for f in findings if " HZ-02 " in f)
    hz03 = sum(1 for f in findings if " HZ-03 " in f)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"hierarchy_scan: scanned={len(paths)} carrying={n_carry} "
          f"HZ-01={hz01} HZ-02={hz02} HZ-03={hz03} "
          f"(hard gate; README.md, PREREQUISITES.md and the CC-20 "
          f"assessment/ banks are the HZ-03 by-design exemptions; "
          f"born tick-609 at zero)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
