#!/usr/bin/env python3
"""Lesson anatomy census (LA-01) for PROJECT-OMEGA.

Every lesson doc opens its pedagogy with the canonical
"Learning Objectives" H2: the platform's syllabus card and
progress model key on that heading, so a lesson without it has
no machine-visible goal statement. Scope is the lesson_id_scan
corpus - docs/phases/<phase>/<NNNN-module>/NNNN-*.md, 114 files.

LA-01  no H2 heading exactly "Learning Objectives" (fence-invisible,
       trimmed). REPORT - born from the tick-413 census: 104/114
       lessons already carry the exact canonical heading; the 10
       missing sites are the drain queue, the gate goes hard
       after that drain (census -> drain -> gate cycle).

Hands-on and quiz sections are deliberately not gated here:
assessment lives in the separate assessment/QUIZ.md and lab files
(lesson_id_scan / lab_registry are the identity gates for those),
so a lesson without an inline quiz section is not a finding.

REPORT GATE - prints findings, mirrors the corpus, exits 1 only
when findings exist (scorecard counts it as report until the
drain promotes it).

Run over the whole corpus:
    python scripts/qa/lesson_anatomy_census.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
PHASE_DIR = re.compile(r"^phase\d+-")
MODULE_DIR = re.compile(r"^\d{4}-")
LESSON_FILE = re.compile(r"^\d{4}-.*\.md$")
CANON_H2 = "Learning Objectives"


def lesson_paths(root: Path) -> list[Path]:
    """Same corpus as lesson_id_scan: NNNN-*.md under
    docs/phases/<phase>/<NNNN-module>/."""
    phases = root / "docs" / "phases"
    out: list[Path] = []
    for path in sorted(phases.glob("*/*")):
        if not (path.is_dir() and PHASE_DIR.match(path.parent.name)
                and MODULE_DIR.match(path.name)):
            continue
        for md in sorted(path.rglob("*.md")):
            if LESSON_FILE.match(md.name):
                out.append(md)
    return out


def canonical_objectives(lines: list[str]) -> bool:
    """True when an unfenced H2 equals the canonical heading."""
    state = 0
    for raw in lines:
        m = FENCE_RE.match(raw)
        if m:
            ticks, lang = len(m.group(1)), m.group(2)
            if state and not lang and ticks >= state:
                state = 0
            elif not state:
                state = ticks
            continue
        if state:
            continue
        hm = H2_RE.match(raw)
        if hm and hm.group(1).strip() == CANON_H2:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []
    n_lessons = 0
    n_canonical = 0
    for path in lesson_paths(args.root):
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(args.root).as_posix()
        n_lessons += 1
        if canonical_objectives(lines):
            n_canonical += 1
        else:
            findings.append(
                f"{rel}: LA-01 no canonical 'Learning Objectives' H2 "
                f"(the platform syllabus card keys on this heading)")
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"lesson_anatomy_census: lessons={n_lessons} "
          f"canonical={n_canonical} LA-01={len(findings)} "
          f"(report gate; born tick-413, canonical H2 "
          f"'{CANON_H2}', hard after the drain)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
