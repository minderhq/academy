#!/usr/bin/env python3
"""lab index parity gate for PROJECT-OMEGA.

Every lab declares its own contract in front matter (Document ID,
Title, Estimated Time), and MASTER-INDEX.md's "### Labs" table
mirrors that contract for planning. Nothing locked the mirror:
born tick-553 at the maximal finding - 12 of 15 labs carried a
Duration drift (the index summed ~53 hours while the labs' own
Estimated Time summed ~85; LAB-009 read 4 hours against a declared
12) and 9 of 15 carried a title drift, so a learner budgeting time
from the index would badly underestimate every phase. The verbatim
mirror is the same convention the notebook catalog lock (tick-551)
keeps.

LI-01  id-set parity: every LAB-NNN with front matter has a Labs
       table row and every row has a lab file (either direction
       alone is a finding).
LI-02  duration parity: the row's Duration equals the lab's
       Estimated Time verbatim.
LI-03  title parity: the row's title equals the lab's Title with
       its "LAB-NNN: " prefix stripped, verbatim.

Hard gate (exit 1 on findings): born tick-553 at 21 findings,
drained in the same tick - the index rows rewritten to the labs'
own contract.

Run over the whole corpus:
    python scripts/qa/lab_index_parity_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MI_SECTION = re.compile(r"^### Labs \(", re.M)
MI_ROW = re.compile(
    r"^\|\s*\*\*\[(LAB-\d+)\]\(([^)]+)\)\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|",
    re.M)
FM_ID = re.compile(r"^Document ID: (LAB-\d+)", re.M)
FM_TITLE = re.compile(r'^Title: "(.+)"', re.M)
FM_TIME = re.compile(r"^Estimated Time: (.+)$", re.M)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []

    labs_dir = args.root / "docs" / "learning-resources" / "labs"
    fm: dict[str, tuple[str, str, str]] = {}
    for p in sorted(labs_dir.glob("LAB-*.md")):
        t = p.read_text(encoding="utf-8")
        did = FM_ID.search(t)
        ti = FM_TITLE.search(t)
        et = FM_TIME.search(t)
        if not (did and ti and et):
            findings.append(f"{p.name}: LI-00 lab front matter missing "
                            f"Document ID / Title / Estimated Time")
            continue
        fm[did.group(1)] = (ti.group(1), et.group(1).strip(), f"{p.name}")

    master = args.root / "docs" / "00-META" / "MASTER-INDEX.md"
    mi_text = master.read_text(encoding="utf-8")
    mi: dict[str, tuple[str, str, str]] = {}
    sec = MI_SECTION.search(mi_text)
    if sec:
        rest = mi_text[sec.end():]
        stop = re.search(r"^### ", rest, re.M)
        body = rest[:stop.start()] if stop else rest
        for lab_id, _link, title, dur in MI_ROW.findall(body):
            mi[lab_id] = (title.strip(), dur.strip(), "MASTER-INDEX.md")

    for lab_id in sorted(fm.keys() - mi.keys()):
        findings.append(f"{lab_id}: LI-01 lab exists ({fm[lab_id][2]}) "
                        f"but has no MASTER-INDEX Labs row")
    for lab_id in sorted(mi.keys() - fm.keys()):
        findings.append(f"{lab_id}: LI-01 MASTER-INDEX Labs row "
                        f"but no lab file on disk")
    for lab_id in sorted(fm.keys() & mi.keys()):
        title, dur, _ = fm[lab_id]
        short = title.split(": ", 1)[1] if ": " in title else title
        if mi[lab_id][1] != dur:
            findings.append(f"{lab_id}: LI-02 duration mismatch - "
                            f"MASTER-INDEX {mi[lab_id][1]!r} vs front "
                            f"matter Estimated Time {dur!r}")
        if mi[lab_id][0] != short:
            findings.append(f"{lab_id}: LI-03 title mismatch - "
                            f"MASTER-INDEX {mi[lab_id][0]!r} vs front "
                            f"matter title {short!r}")

    for f in findings:
        print(f)
    print(f"lab_index_parity_check: {len(findings)} findings "
          f"(LI-01 id-set parity, LI-02 duration parity, LI-03 title "
          f"parity) across {len(fm)} lab files / {len(mi)} MASTER-INDEX "
          f"rows")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
