#!/usr/bin/env python3
"""tutorial index parity gate for Minder Academy.

MASTER-INDEX.md's "### Tutorials" table is the planning contract for
the 15-file tutorial fleet; every tutorial's front matter should
carry the same contract so the platform can read either side. Born
tick-554 at the maximal finding: 13 of 15 front matters carried no
Estimated Time at all and 13 carried no Prerequisites field (the
index's Duration and Prerequisites columns floated with no machine-
readable counterpart), the Difficulty column disagreed with front
matter on TUTORIAL-006 (Advanced against an Intermediate body), and
durations drifted against body evidence on four tutorials (the index
said 4 hours where TUTORIAL-006's body says 60 minutes and
TUTORIAL-007's front matter says 1 hour). Unlike the lab lock (where
the richer side is the lab front matter), here the mirror direction
follows the richer side per field: body/FM evidence wins on time and
difficulty, the index's richer prerequisite sets seed the front
matter.

TI-01  difficulty parity: the row's Difficulty equals the front
       matter Difficulty verbatim.
TI-02  estimated-time completeness and parity: every front matter
       carries Estimated Time and the row's Duration equals it
       verbatim.
TI-03  prerequisites completeness and parity: every front matter
       carries Prerequisites and the normalized set in the row's
       Prerequisites cell equals the normalized FM list
       (TUT-NNN expands to TUTORIAL-NNN, "Phase N" normalizes to
       PHASE-N, None-shaped cells normalize to the empty set).
TI-04  every prerequisite item must normalize (free text like
       "Python basics" is a finding - prerequisites are ids).
TI-05  id-set parity: every TUTORIAL-NNN with front matter has a
       Tutorials row and every row has a tutorial file (either
       direction alone is a finding).
TI-06  section-header arithmetic: the "### Tutorials (N files)"
       header is a count claim a learner plans from - N must equal
       both the MASTER-INDEX table's own row count and the
       tutorials directory's TUTORIAL-*.md count. Joined tick-564:
       the numbers were census-proven true (15 = 15 rows = 15
       files) but unlocked - TI-01..05 read the table rows and
       never the header.

Hard gate (exit 1 on findings): born tick-554 at the maximal
finding, drained in the same tick - front matters seeded from the
evidence-backed values, drifted index cells corrected; TI-06
joined tick-564 at zero.

Run over the whole corpus:
    python scripts/qa/tutorial_index_parity_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MI_SECTION = re.compile(r"^### Tutorials \(", re.M)
TUTORIALS_HEADER = re.compile(r"^### Tutorials \((\d+) files\)", re.M)
MI_ROW = re.compile(
    r"^\|\s*\*\*\[(TUTORIAL-\d+)\]\(([^)]+)\)\*\*\s*\|\s*(.+?)\s*\|"
    r"\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", re.M)
FM_ID = re.compile(r"^Document ID: (TUTORIAL-\d+)", re.M)
FM_DIFF = re.compile(r"^Difficulty: (.+)$", re.M)
FM_TIME = re.compile(r"^Estimated Time: (.+)$", re.M)
FM_PRE = re.compile(r"^Prerequisites: \[([^\]]*)\]", re.M)

ID_ITEM = re.compile(r"^(TUTORIAL-\d+|LAB-\d+|PHASE-\d+)$")
SHORT_TUT = re.compile(r"^TUT-(\d+)$")
PHASE_ITEM = re.compile(r"^Phase (\d+)$")


def norm_item(raw: str) -> str | None:
    s = raw.strip().strip("*").strip()
    if s.lower().startswith("none") or s == "":
        return ""
    s = SHORT_TUT.sub(r"TUTORIAL-\1", s)
    s = PHASE_ITEM.sub(r"PHASE-\1", s)
    return s if ID_ITEM.match(s) else None


def norm_set(cell: str) -> set[str]:
    out = set()
    for part in cell.split(","):
        n = norm_item(part)
        if n:
            out.add(n)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []

    tut_dir = args.root / "docs" / "learning-resources" / "tutorials"
    fm: dict[str, tuple[str, str, str, str]] = {}
    for p in sorted(tut_dir.glob("TUTORIAL-*.md")):
        t = p.read_text(encoding="utf-8")
        did = FM_ID.search(t)
        dif = FM_DIFF.search(t)
        et = FM_TIME.search(t)
        pre = FM_PRE.search(t)
        if not did:
            findings.append(f"{p.name}: TI-00 front matter missing Document ID")
            continue
        tid = did.group(1)
        if not dif:
            findings.append(f"{tid}: TI-01 front matter missing Difficulty")
        if not et:
            findings.append(f"{tid}: TI-02 front matter missing Estimated Time")
        if not pre:
            findings.append(f"{tid}: TI-03 front matter missing Prerequisites")
        fm[tid] = (
            dif.group(1).strip() if dif else "",
            et.group(1).strip() if et else "",
            norm_set(pre.group(1)) if pre else set(),
            p.name)

    master = args.root / "docs" / "00-META" / "MASTER-INDEX.md"
    if not master.exists():
        print("tutorial_index_parity_check: SKIP - docs/00-META/MASTER-INDEX.md not found, nothing to check")
        return 0
    mi_text = master.read_text(encoding="utf-8")
    mi: dict[str, tuple[str, str, str, str]] = {}
    sec = MI_SECTION.search(mi_text)
    if sec:
        rest = mi_text[sec.end():]
        stop = re.search(r"^### ", rest, re.M)
        body = rest[:stop.start()] if stop else rest
        for tid, _link, title, dur, dif, pre in MI_ROW.findall(body):
            mi[tid] = (dur.strip(), dif.strip(), pre.strip(), title.strip())

    for tid in sorted(fm.keys() - mi.keys()):
        findings.append(f"{tid}: TI-05 tutorial exists ({fm[tid][3]}) "
                        f"but has no MASTER-INDEX Tutorials row")
    for tid in sorted(mi.keys() - fm.keys()):
        findings.append(f"{tid}: TI-05 MASTER-INDEX Tutorials row "
                        f"but no tutorial file on disk")
    for tid in sorted(fm.keys() & mi.keys()):
        fdif, fet, fpre, _ = fm[tid]
        mdur, mdif, mpre, _ = mi[tid]
        if fdif and mdif != fdif:
            findings.append(f"{tid}: TI-01 difficulty mismatch - "
                            f"MASTER-INDEX {mdif!r} vs front matter {fdif!r}")
        if fet and mdur != fet:
            findings.append(f"{tid}: TI-02 duration mismatch - "
                            f"MASTER-INDEX {mdur!r} vs front matter {fet!r}")
        if fpre is not None:
            bad = [x for x in mpre.split(",") if norm_item(x) is None]
            if bad:
                findings.append(f"{tid}: TI-04 unnormalizable prerequisite "
                                f"item(s) {bad!r} in MASTER-INDEX")
            elif norm_set(mpre) != fpre:
                findings.append(f"{tid}: TI-03 prerequisites mismatch - "
                                f"MASTER-INDEX {sorted(norm_set(mpre))!r} vs "
                                f"front matter {sorted(fpre)!r}")

    # --- TI-06: section-header arithmetic ---------------------------------
    hm = TUTORIALS_HEADER.search(mi_text)
    if hm is None:
        findings.append("MASTER-INDEX Tutorials header: TI-06 lost the "
                        "'(N files)' form")
    else:
        n = int(hm.group(1))
        c_tut = len(list(tut_dir.glob("TUTORIAL-*.md")))
        if n != len(mi):
            findings.append(f"MASTER-INDEX Tutorials header: TI-06 header "
                            f"says {n} files, MASTER-INDEX table holds "
                            f"{len(mi)} rows")
        if n != c_tut:
            findings.append(f"MASTER-INDEX Tutorials header: TI-06 header "
                            f"says {n} files, disk holds {c_tut} tutorial "
                            f"files")

    for f in findings:
        print(f)
    print(f"tutorial_index_parity_check: {len(findings)} findings "
          f"(TI-01 difficulty, TI-02 estimated time, TI-03 prerequisites, "
          f"TI-04 normalizable items, TI-05 id-set parity, TI-06 header "
          f"arithmetic) across {len(fm)} tutorial files / {len(mi)} "
          f"MASTER-INDEX rows")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
