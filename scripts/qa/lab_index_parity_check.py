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
LI-04  section-header arithmetic: the "### Labs (N files: A labs
       + B solutions)" header is a claim a learner budgets from -
       A+B must equal N, A must equal the labs directory's own
       LAB-*.md count and B the solutions directory's. Joined
       tick-564: the numbers were census-proven true (30 = 15+15)
       but unlocked - LI-01..03 read the table rows and never the
       header.
LI-05  part-duration presence: every "## Exercise N" / "## Part N"
       heading carries an "(N minutes)" / "(N hours)" duration -
       except headings marked "(Optional)" (the born case: LAB-006's
       "Part 8: Challenges (Optional)" is untimed by design), so a
       part losing its duration cannot silently undercount the sum
       LI-06 audits.
LI-06  estimated-time ceiling: the corpus contract read off the born
       census - front-matter "Estimated Time: N hours" must equal
       the ceil of the lab's own Exercise/Part duration sum to the
       whole hour (LAB-002's 230 minutes of parts -> 4 hours,
       LAB-009's 690 -> 12), with "Final Challenge" headings
       deliberately outside the sum (bonus work past the core
       budget, LAB-001..005 only) and checklist-style labs with no
       Exercise/Part headings (LAB-000) outside the check entirely.
       Joined tick-572: the census that first read 10 of 15 labs as
       mismatching compared the raw sum against the FM hours - all
       15 labs obey the ceiling exactly, the mismatch was the
       convention itself, unlocked until now.

Hard gate (exit 1 on findings): born tick-553 at 21 findings,
drained in the same tick - the index rows rewritten to the labs'
own contract. LI-05/06 joined tick-572 born at zero findings - the
ceiling held on all 15 labs at birth; the lock exists so the next
duration edit cannot silently strand the budget a learner plans
from.

Run over the whole corpus:
    python scripts/qa/lab_index_parity_check.py --root .
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

MI_SECTION = re.compile(r"^### Labs \(", re.M)
LABS_HEADER = re.compile(
    r"^### Labs \((\d+) files: (\d+) labs \+ (\d+) solutions\)", re.M)
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

    # --- LI-04: section-header arithmetic ---------------------------------
    hm = LABS_HEADER.search(mi_text)
    if hm is None:
        findings.append("MASTER-INDEX Labs header: LI-04 lost the "
                        "'(N files: A labs + B solutions)' form")
    else:
        n, a, b = (int(hm.group(i)) for i in (1, 2, 3))
        c_lab = len(list(labs_dir.glob("LAB-*.md")))
        c_sol = len(list((labs_dir / "solutions").glob("*.md")))
        if a + b != n:
            findings.append(f"MASTER-INDEX Labs header: LI-04 header "
                            f"arithmetic {a}+{b} != {n}")
        if a != c_lab:
            findings.append(f"MASTER-INDEX Labs header: LI-04 header "
                            f"part 1 says {a} labs, disk holds {c_lab}")
        if b != c_sol:
            findings.append(f"MASTER-INDEX Labs header: LI-04 header "
                            f"part 2 says {b} solutions, disk holds "
                            f"{c_sol}")

    # --- LI-05/LI-06: the lab's own time budget -----------------------------
    part_h2 = re.compile(r"^##\s+(?:Exercise|Part)\s+\d+", re.I)
    dur = re.compile(r"\((\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?)\)",
                     re.I)
    fence = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")
    et_hours = re.compile(r"^Estimated Time:\s*(\d+)\s*hours?$")
    for p in sorted(labs_dir.glob("LAB-*.md")):
        total = 0
        timed = 0
        et_val: int | None = None
        in_fence = False
        marker = ""
        for line in p.read_text(encoding="utf-8").splitlines():
            fm_ = fence.match(line)
            if fm_:
                if not in_fence:
                    in_fence, marker = True, fm_.group(1)
                elif len(fm_.group(1)) >= len(marker) and fm_.group(2) == "":
                    in_fence = False
                continue
            if in_fence:
                continue
            em = et_hours.match(line)
            if em and et_val is None:
                et_val = int(em.group(1))
            if part_h2.match(line):
                dm = dur.search(line)
                if dm is None:
                    if "(optional)" not in line.lower():
                        findings.append(f"{p.name}: LI-05 untimed part "
                                        f"heading {line.strip()!r}")
                else:
                    val = float(dm.group(1))
                    total += int(round(val * 60
                                       if dm.group(2).lower().startswith("h")
                                       else val))
                    timed += 1
        if timed == 0:
            continue  # checklist-style lab: no internal part budget to audit
        if et_val is None:
            findings.append(f"{p.name}: LI-06 Estimated Time is not in the "
                            f"'N hour(s)' form but the lab carries {timed} "
                            f"timed parts")
        else:
            need = math.ceil(total / 60)
            if et_val != need:
                findings.append(f"{p.name}: LI-06 Estimated Time {et_val}h "
                                f"!= ceil of its own part sum ({total} min "
                                f"-> {need}h)")

    for f in findings:
        print(f)
    print(f"lab_index_parity_check: {len(findings)} findings "
          f"(LI-01 id-set parity, LI-02 duration parity, LI-03 title "
          f"parity, LI-04 header arithmetic, LI-05 part-duration "
          f"presence, LI-06 estimated-time ceiling) across {len(fm)} lab "
          f"files / {len(mi)} MASTER-INDEX rows")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
