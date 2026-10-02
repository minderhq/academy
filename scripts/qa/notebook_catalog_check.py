#!/usr/bin/env python3
"""notebook catalog parity gate for the PROJECT-OMEGA corpus.

The 20-notebook catalog lives twice: docs/notebooks/README.md (the
fleet's own index, star-rendered difficulty + per-notebook conda
environment column) and MASTER-INDEX.md's "### Notebooks" table
(word difficulty, the Learning Resources sibling format). Tick-549
wired the fleet into MASTER-INDEX by mirroring the README rows
verbatim - duplicating data across two files with no lock, exactly
the rot class the claims gates exist for: an edit to one table
(new duration, renamed topic list, re-tiered difficulty) that never
reaches the other leaves two contradicting catalogs with every
count claim still green. Link checks cannot see this class - both
tables' links resolve; it is the CONTENT that drifts.

NC-01  id-set parity: every NB-NNN row in one catalog must exist in
       the other (a notebook added/retired in one table only is a
       finding).
NC-02  field parity per shared id: title, topics, difficulty word
       (README's star run is stripped to its word) and duration must
       be verbatim-equal across both tables, and each side's link
       target basename must name the same notebook file.
NC-03  section-header arithmetic: the "### Notebooks (N files)"
       header is a count claim a learner plans from - N must equal
       the notebooks directory's own *.ipynb count (the header's
       definition is notebooks only; the directory README is not a
       notebook - the same divergence the SITEMAP section's 21
       documents). Joined tick-564: the number was census-proven
       true (20 = 20) but unlocked - NC-01/02 read the table rows
       and never the header.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-551) -
the mirroring was verbatim, the gate keeps it that way; NC-03
joined tick-564 at zero.

Run over the whole corpus:
    python scripts/qa/notebook_catalog_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MI_SECTION = re.compile(r"^### Notebooks \(", re.M)
NOTEBOOKS_HEADER = re.compile(r"^### Notebooks \((\d+) files\)", re.M)
# MASTER-INDEX row: | **[NB-201](link)** | Title | Topics | Difficulty | Duration |
MI_ROW = re.compile(
    r"^\|\s*\*\*\[(NB-\d+)\]\(([^)]+)\)\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*"
    r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$")
# README row: | **[NB-201: PyTorch Basics](./link.ipynb)** | Topics | D | Dur | env |
README_ROW = re.compile(
    r"^\|\s*\*\*\[(NB-\d+):\s*([^\]]+)\]\(([^)]+)\)\*\*\s*\|\s*(.+?)\s*"
    r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$")
STAR_RUN = re.compile("[\u2b50\\s]+")  # star runs in README difficulty cells


def section_lines(text: str, header: re.Pattern[str]) -> list[str]:
    m = header.search(text)
    if not m:
        return []
    rest = text[m.end():]
    stop = re.search(r"^### ", rest, re.M)
    body = rest[:stop.start()] if stop else rest
    return body.split("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []

    readme = args.root / "docs" / "notebooks" / "README.md"
    master = args.root / "docs" / "00-META" / "MASTER-INDEX.md"
    rd: dict[str, tuple[str, ...]] = {}
    md: dict[str, tuple[str, ...]] = {}
    for ln, raw in enumerate(readme.read_text(encoding="utf-8").split("\n"), 1):
        m = README_ROW.match(raw)
        if m:
            nb, title, link, topics, diff, dur, _env = m.groups()
            rd[nb] = (title.strip(), topics.strip(),
                      STAR_RUN.sub("", diff).strip(), dur.strip(),
                      Path(link).name, f"{readme.name}:{ln}")
    if not rd:
        findings.append(f"{readme.name}: NC-00 no README catalog rows parsed")
    mi_text = master.read_text(encoding="utf-8")
    base_ln = mi_text[:MI_SECTION.search(mi_text).start()].count("\n") + 1 \
        if MI_SECTION.search(mi_text) else 1
    for i, raw in enumerate(section_lines(mi_text, MI_SECTION)):
        m = MI_ROW.match(raw)
        if m:
            nb, link, title, topics, diff, dur = m.groups()
            md[nb] = (title.strip(), topics.strip(), diff.strip(), dur.strip(),
                      Path(link).name, f"{master.name}:{base_ln + i}")

    for nb in sorted(rd.keys() - md.keys()):
        findings.append(f"{nb}: NC-01 in notebooks/README.md "
                        f"({rd[nb][5]}) but missing from MASTER-INDEX "
                        f"Notebooks table")
    for nb in sorted(md.keys() - rd.keys()):
        findings.append(f"{nb}: NC-01 in MASTER-INDEX Notebooks table "
                        f"({md[nb][5]}) but missing from notebooks/README.md")
    for nb in sorted(rd.keys() & md.keys()):
        r, m_ = rd[nb], md[nb]
        fields = ["title", "topics", "difficulty", "duration"]
        for i, fname in enumerate(fields):
            if r[i] != m_[i]:
                findings.append(
                    f"{nb}: NC-02 {fname} mismatch - README "
                    f"({rd[nb][5]}) {r[i]!r} vs MASTER-INDEX "
                    f"({md[nb][5]}) {m_[i]!r}")
        if r[4] != m_[4]:
            findings.append(
                f"{nb}: NC-02 link target mismatch - README "
                f"{r[4]!r} vs MASTER-INDEX {m_[4]!r}")
    # --- NC-03: section-header arithmetic ---------------------------------
    hm = NOTEBOOKS_HEADER.search(mi_text)
    if hm is None:
        findings.append("MASTER-INDEX Notebooks header: NC-03 lost the "
                        "'(N files)' form")
    else:
        n = int(hm.group(1))
        c_nb = len(list((args.root / "docs" / "notebooks").glob("*.ipynb")))
        if n != c_nb:
            findings.append(f"MASTER-INDEX Notebooks header: NC-03 header "
                            f"says {n} files, disk holds {c_nb} notebooks")

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"notebook_catalog_check: {len(findings)} findings "
          f"(NC-01 id-set parity, NC-02 field parity, NC-03 header "
          f"arithmetic) across {len(rd)} README rows / {len(md)} "
          f"MASTER-INDEX rows")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
