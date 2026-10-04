#!/usr/bin/env python3
"""project index parity gate for Minder Academy.

MASTER-INDEX.md's "### Projects" table is the planning entry for the
7-file capstone fleet. Born tick-556 at 13 findings: 6 of 7 Project
cells abbreviated away the front-matter Title ("AI Assistant" against
"Build Your AI Assistant", "Fine-tune Model" against "Fine-Tune
Domain Model") and every row lacked the Difficulty the front matter
declares - the inverse of the tutorial lock's drain: here the front
matter is the richer side, so the index gains the column.

PJ-01  id-set parity: every project file with front matter has a row
       and every row has a file (either direction alone is a finding).
PJ-02  project parity: the row's Project cell equals the front-matter
       Title verbatim after stripping the "CAPSTONE PROJECT-NNN: "
       prefix (the lab lock's verbatim-mirror convention).
PJ-03  the section header's "(N files)" count equals the row count.
PJ-04  link parity: every row's link basename names that row's own
       file (a link to a different existing project resolves cleanly
       for linkcheck yet misroutes the learner).
PJ-05  difficulty parity: every row carries the front-matter
       Difficulty verbatim (a 4-column row is a finding - the column
       exists since tick-556).
PJ-06  duration form: the Duration cell is "N weeks" or "N-N weeks"
       (project-scale work, not reading time - projects deliberately
       carry no Estimated Time; seeding one would poison the pacing
       census's hour/minute arithmetic, so the weeks form stays an
       index-side planning surface with a locked shape).

Hard gate (exit 1 on findings): born tick-556 at 13 findings, drained
in the same tick - 6 Project cells mirrored to title truth, the
Difficulty column added from front-matter values.

Run over the whole corpus:
    python scripts/qa/project_index_parity_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MI_SECTION = re.compile(r"^### Projects \(", re.M)
MI_HEADER = re.compile(r"^### Projects \((\d+) files?\)", re.M)
MI_ROW_ID = re.compile(r"^\|\s*\*\*\[(PROJECT-\d+)\]\(([^)]+)\)\*\*")
FM_ID = re.compile(r"^Document ID: (PROJECT-\d+)", re.M)
FM_TITLE = re.compile(r'^Title:\s*"(.+?)"', re.M)
FM_DIFF = re.compile(r"^Difficulty: (.+)$", re.M)

PREFIX_CAPSTONE = re.compile(r"^CAPSTONE PROJECT-\d+:\s*")
DURATION_FORM = re.compile(r"^\d+(-\d+)? weeks?$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []

    prj_dir = args.root / "docs" / "learning-resources" / "projects"
    fm: dict[str, tuple[str, str, str]] = {}  # id -> (title, difficulty, fname)
    for p in sorted(prj_dir.glob("PROJECT-*.md")):
        t = p.read_text(encoding="utf-8")
        did = FM_ID.search(t)
        ttl = FM_TITLE.search(t)
        dif = FM_DIFF.search(t)
        if not did or not ttl or not dif:
            findings.append("%s: PJ-01 front matter missing Document ID, "
                            "Title or Difficulty" % p.name)
            continue
        fm[did.group(1)] = (ttl.group(1).strip(), dif.group(1).strip(),
                            p.name)

    master = args.root / "docs" / "00-META" / "MASTER-INDEX.md"
    if not master.exists():
        print("project_index_parity_check: SKIP - docs/00-META/MASTER-INDEX.md not found, nothing to check")
        return 0
    mi_text = master.read_text(encoding="utf-8")
    sec = MI_SECTION.search(mi_text)
    hdr = MI_HEADER.search(mi_text)
    rows: dict[str, list[str]] = {}  # id -> [link, project, duration, skills, difficulty?]
    if sec:
        rest = mi_text[sec.end():]
        stop = re.search(r"^### ", rest, re.M)
        body = rest[:stop.start()] if stop else rest
        for line in body.split("\n"):
            m = MI_ROW_ID.match(line)
            if not m:
                continue
            cells = line.split("|")
            # | **[ID](link)** | b | c | d [| e |] -> 6 or 7 parts; the
            # link comes from the regex group, cells[1] is the whole
            # markdown cell including **[...](...)**
            rows[m.group(1)] = ([m.group(2).strip()]
                                + [c.strip() for c in cells[2:6]])

    if hdr:
        hdr_count = int(hdr.group(1))
        if hdr_count != len(rows):
            findings.append("PJ-03 header says %d files but the table "
                            "carries %d rows" % (hdr_count, len(rows)))

    for pid in sorted(fm.keys() - rows.keys()):
        findings.append("%s: PJ-01 project file exists (%s) but has no "
                        "MASTER-INDEX Projects row" % (pid, fm[pid][2]))
    for pid in sorted(rows.keys() - fm.keys()):
        findings.append("%s: PJ-01 MASTER-INDEX Projects row but no "
                        "project file on disk" % pid)
    for pid in sorted(fm.keys() & rows.keys()):
        link, project, duration, _skills = rows[pid][:4]
        title, difficulty, fname = fm[pid]
        want = PREFIX_CAPSTONE.sub("", title).strip()
        if project != want:
            findings.append("%s: PJ-02 project drift - MASTER-INDEX %r "
                            "vs title %r" % (pid, project, want))
        base = link.rstrip("/").rsplit("/", 1)[-1]
        if base != fname:
            findings.append("%s: PJ-04 link names %r but the file is %r"
                            % (pid, base, fname))
        if len(rows[pid]) < 5 or not rows[pid][4]:
            findings.append("%s: PJ-05 row carries no Difficulty cell "
                            "(column exists since tick-556)" % pid)
        elif rows[pid][4] != difficulty:
            findings.append("%s: PJ-05 difficulty mismatch - MASTER-INDEX "
                            "%r vs front matter %r"
                            % (pid, rows[pid][4], difficulty))
        if not DURATION_FORM.match(duration):
            findings.append("%s: PJ-06 duration %r is not \"N weeks\" or "
                            "\"N-N weeks\"" % (pid, duration))

    for f in findings:
        print(esc(f))
    print("project_index_parity_check: %d findings (PJ-01 id-set parity, "
          "PJ-02 project parity, PJ-03 header count, PJ-04 link parity, "
          "PJ-05 difficulty parity, PJ-06 duration form) across %d "
          "project files / %d MASTER-INDEX rows"
          % (len(findings), len(fm), len(rows)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
