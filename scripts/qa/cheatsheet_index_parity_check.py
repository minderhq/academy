#!/usr/bin/env python3
"""cheat sheet index parity gate for Minder Academy.

MASTER-INDEX.md's "### Cheat Sheets" table is the planning entry for
the 13-file cheat-sheet fleet (5 CHEAT-SHEET-* + 7 QUICK-REF-VOLUME-*).
Born tick-555 at a maximal discoverability finding: CHEAT-SHEET-006
(Kubernetes for LLM Deployment) existed on disk, was counted in the
File Counts section (13) and listed in SITEMAP.md, but its Tutorials-
style row was never added - the table listed 12 rows under a "13
files" header, and the newest cheat sheet was invisible to the one
surface learners browse first (linkcheck cannot see orphans: every
existing link resolves whether or not an orphan exists).

CI-01  id-set parity: every cheat-sheet file with front matter has a
       row and every row has a file (either direction alone is a
       finding); row ids QUICK-REF-VN normalize to QUICK-REF-VOLUME-N.
CI-02  topic parity: the row's Topic cell equals the front-matter
       Title verbatim after stripping the "CHEAT-SHEET-NNN: " or
       "Volume N: " prefix (the lab lock's verbatim-mirror
       convention - abbreviations are findings).
CI-03  the section header's "(N files)" count equals the number of
       table rows (the drift signal that fired at birth).
CI-04  link parity: every row's link basename names that row's own
       file (a link to a different existing cheat sheet resolves
       cleanly for linkcheck yet misroutes the learner).

Hard gate (exit 1 on findings): born tick-555 at 13 findings, drained
in the same tick - CHEAT-SHEET-006's row added, 11 abbreviated Topic
cells mirrored to title truth.

Run over the whole corpus:
    python scripts/qa/cheatsheet_index_parity_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MI_SECTION = re.compile(r"^### Cheat Sheets \(", re.M)
MI_HEADER = re.compile(r"^### Cheat Sheets \((\d+) files?\)", re.M)
MI_ROW = re.compile(
    r"^\|\s*\*\*\[(CHEAT-SHEET-\d+|QUICK-REF-V\d+)\]\(([^)]+)\)\*\*"
    r"\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", re.M)
FM_ID = re.compile(r"^Document ID: (CHEAT-SHEET-\d+|QUICK-REF-VOLUME-\d+)",
                   re.M)
FM_TITLE = re.compile(r'^Title:\s*"(.+?)"', re.M)

PREFIX_CHEAT = re.compile(r"^CHEAT-SHEET-\d+:\s*")
PREFIX_VOLUME = re.compile(r"^Volume \d+:\s*")
ROW_ID_NORM = re.compile(r"^QUICK-REF-V(\d+)$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def norm_row_id(raw: str) -> str:
    m = ROW_ID_NORM.match(raw)
    return "QUICK-REF-VOLUME-" + m.group(1) if m else raw


def expected_topic(title: str) -> str:
    t = title.strip().strip('"').strip()
    t = PREFIX_CHEAT.sub("", t)
    t = PREFIX_VOLUME.sub("", t)
    return t.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []

    cs_dir = args.root / "docs" / "learning-resources" / "cheat-sheets"
    fm: dict[str, tuple[str, str]] = {}  # id -> (title, filename)
    for p in sorted(cs_dir.glob("*.md")):
        t = p.read_text(encoding="utf-8")
        did = FM_ID.search(t)
        ttl = FM_TITLE.search(t)
        if not did or not ttl:
            findings.append("%s: CI-01 front matter missing "
                            "Document ID or Title" % p.name)
            continue
        fm[did.group(1)] = (ttl.group(1).strip(), p.name)

    master = args.root / "docs" / "00-META" / "MASTER-INDEX.md"
    if not master.exists():
        print("cheatsheet_index_parity_check: SKIP - docs/00-META/MASTER-INDEX.md not found, nothing to check")
        return 0
    mi_text = master.read_text(encoding="utf-8")
    sec = MI_SECTION.search(mi_text)
    hdr = MI_HEADER.search(mi_text)
    rows: dict[str, tuple[str, str, str]] = {}  # norm id -> (link, topic, raw id)
    if sec:
        rest = mi_text[sec.end():]
        stop = re.search(r"^### ", rest, re.M)
        body = rest[:stop.start()] if stop else rest
        for rid, link, topic, _cov in MI_ROW.findall(body):
            rows[norm_row_id(rid)] = (link.strip(), topic.strip(), rid)

    if hdr:
        hdr_count = int(hdr.group(1))
        if hdr_count != len(rows):
            findings.append("CI-03 header says %d files but the table "
                            "carries %d rows" % (hdr_count, len(rows)))

    for cid in sorted(fm.keys() - rows.keys()):
        findings.append("%s: CI-01 cheat-sheet file exists (%s) "
                        "but has no MASTER-INDEX Cheat Sheets row"
                        % (cid, fm[cid][1]))
    for cid in sorted(rows.keys() - fm.keys()):
        findings.append("%s: CI-01 MASTER-INDEX Cheat Sheets row "
                        "but no cheat-sheet file on disk" % cid)
    for cid in sorted(fm.keys() & rows.keys()):
        link, topic, rid = rows[cid]
        title, fname = fm[cid]
        want = expected_topic(title)
        if topic != want:
            findings.append("%s: CI-02 topic drift - MASTER-INDEX %r vs "
                            "title %r" % (cid, topic, want))
        base = link.rstrip("/").rsplit("/", 1)[-1]
        if base != fname:
            findings.append("%s: CI-04 link names %r but the file is %r"
                            % (cid, base, fname))

    for f in findings:
        print(esc(f))
    print("cheatsheet_index_parity_check: %d findings (CI-01 id-set "
          "parity, CI-02 topic parity, CI-03 header count, CI-04 link "
          "parity) across %d cheat-sheet files / %d MASTER-INDEX rows"
          % (len(findings), len(fm), len(rows)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
