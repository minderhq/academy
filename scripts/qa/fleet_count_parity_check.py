#!/usr/bin/env python3
"""fleet count parity gate for PROJECT-OMEGA.

Count claims are the numbers a learner plans their weeks from: the
MASTER-INDEX File Counts table (the whole-corpus inventory), the
SITEMAP Experiments header (the exhaustive per-fleet listing) and
the README Experiments section (the front-door table of contents).
Nothing locked any of them to disk. Born tick-559 census: MI and
SITEMAP were correct, but the README front door hid 16 of the 47
on-disk experiments - its summary said "46 Experiment Files"
against 47 on disk, and 15 of the 47 (EXP_1102, EXP_1403, EXP_1404,
EXP_1503, EXP_4103, EXP_5102, EXP_5202, EXP_5301, EXP_5302,
EXP_6102, EXP_6202, EXP_6302, EXP_7102, EXP_7202, EXP_7301) were
listed nowhere on the README surface - the CHEAT-SHEET-006 orphan
class: every link resolved, so linkcheck could not see invisible
files (the seven group headers, 4+5+6+4+3+6+4=32, matched their own
blocks - the drift was invisible to any per-surface arithmetic).

FC-01  MI File Counts: every category row's count equals its disk
       definition (the definition map lives below - Experiments
       counts experiments/EXP_*.md and deliberately excludes
       TEMPLATE.md; Phase Documents counts every .md under
       docs/phases including READMEs/assessments/checkpoints;
       Meta Docs counts docs/00-META top level only, its
       assessment/ subtree is not a doc fleet).
FC-02  MI TOTAL row equals the sum of the category rows.
FC-03  SITEMAP "## Experiments (N files: M experiments + 1 TEMPLATE)"
       header equals disk (N = all experiments/*.md, M = EXP_*.md).
FC-04  README "N Experiment Files" summary equals disk EXP count.
FC-05  README Experiments section lists every EXP file on disk in
       both directions (an orphan or a ghost link is a finding).
FC-06  each README group header's "(N)" equals the EXP links under
       that group.

Out of scope, recorded: 0000-LEARNING-PATH.md's experiments table
is a deliberate 6-row per-phase highlight subset, not an inventory;
README line-162/174 fleet claims ("47 experiments", "47 Experiment
Files") were already correct at birth.

Hard gate (exit 1 on findings): born tick-559 at 16 findings
(1 FC-04 + 15 FC-05; FC-01/02/03/06 clean - the definitions and
headers were already honored), drained in the same tick by
completing the README section: the 15 missing experiments placed
in their prefix groups and the summary corrected to 47.

Run over the whole corpus:
    python scripts/qa/fleet_count_parity_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXPERIMENTS_DIR = "experiments"
MI_ROW = re.compile(r"^\| \*\*([^*]+)\*\* \| (\*?\*?)(\d+)\2 \|$", re.M)
SITEMAP_HEADER = re.compile(
    r"^## Experiments \((\d+) files: (\d+) experiments \+ 1 TEMPLATE\)",
    re.M)
README_SUMMARY = re.compile(r"\U0001F52C (\d+) Experiment Files")
README_GROUP = re.compile(r"\*\*(.+?) \((\d+)\):\*\*")
README_LINK = re.compile(r"\./experiments/(EXP_[A-Z_0-9]+)\.md")

# FC-01 disk definitions: MI File Counts category -> how to count it.
# Docs-rooted paths are relative to docs/; "root:" prefixes the repo root.
DEFS = [
    ("Phase READMEs", "docs/phases/phase*/README.md"),
    ("Module READMEs", "docs/phases/phase*/*/README.md"),
    ("Phase Documents", "rglob:docs/phases"),
    ("Tutorials", "docs/learning-resources/tutorials/*.md"),
    ("Labs", "docs/learning-resources/labs/LAB-*.md"),
    ("Lab Solutions", "docs/learning-resources/labs/solutions/*.md"),
    ("Jupyter Notebooks", "docs/notebooks/*.ipynb"),
    ("Practice Files", "rglob-assessment:PRACTICE.md"),
    ("Quiz Files", "rglob-assessment:QUIZ.md"),
    ("Cheat Sheets", "docs/learning-resources/cheat-sheets/*.md"),
    ("Projects", "docs/learning-resources/projects/PROJECT-*.md"),
    ("Experiments", "root:experiments/EXP_*.md"),
    ("Comparisons", "docs/comparisons/*.md"),
    ("Use Cases", "docs/use-cases/*.md"),
    ("Industry Docs", "docs/industry/*.md"),
    ("Solutions", "docs/enterprise-solutions/*.md"),
    ("Diagrams", "docs/diagrams/*.md"),
    ("Meta Docs", "docs/00-META/*.md"),
]


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def disk_count(root: Path, spec: str) -> int:
    docs = root / "docs"
    if spec.startswith("rglob:"):
        base = root / spec[len("rglob:"):]
        return sum(1 for _ in base.rglob("*.md"))
    if spec.startswith("rglob-assessment:"):
        return sum(1 for _ in docs.glob("phases/*/*/assessment/"
                                        + spec.split(":", 1)[1]))
    if spec.startswith("root:"):
        return len(list(root.glob(spec[len("root:"):])))
    return len(list(root.glob(spec)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    args.root = args.root.resolve()
    findings: list[str] = []

    # --- FC-01 + FC-02: MI File Counts vs disk --------------------------
    mi_text = (args.root / "docs" / "00-META" / "MASTER-INDEX.md"
               ).read_text(encoding="utf-8")
    fc = mi_text.split("### File Counts", 1)
    if len(fc) < 2:
        findings.append("FC-01 MASTER-INDEX has no '### File Counts' section")
        rows: dict[str, int] = {}
    else:
        body = fc[1].split("\n## ", 1)[0]
        rows = {name: int(n) for name, _, n in MI_ROW.findall(body)}
    for name, spec in DEFS:
        if name not in rows:
            findings.append("FC-01 MI File Counts row '%s' is missing "
                            "(the inventory must list every fleet)" % name)
            continue
        real = disk_count(args.root, spec)
        if rows[name] != real:
            findings.append("FC-01 MI File Counts '%s' claims %d, disk has %d"
                            % (name, rows[name], real))
    unknown = set(rows) - {n for n, _ in DEFS} - {"TOTAL"}
    for name in sorted(unknown):
        findings.append("FC-01 MI File Counts has a row '%s' with no disk "
                        "definition (phantom or renamed fleet?)" % name)
    if "TOTAL" in rows and len(rows) > 1:
        cat_sum = sum(v for k, v in rows.items() if k != "TOTAL")
        if rows["TOTAL"] != cat_sum:
            findings.append("FC-02 MI File Counts TOTAL is %d, categories "
                            "sum to %d" % (rows["TOTAL"], cat_sum))

    # --- FC-03: SITEMAP experiments header vs disk -----------------------
    sm = (args.root / "docs" / "00-META" / "SITEMAP.md").read_text(
        encoding="utf-8")
    exp_dir = args.root / EXPERIMENTS_DIR
    exp_files = sorted(exp_dir.glob("EXP_*.md"))
    n_all = len(list(exp_dir.glob("*.md")))
    m_sm = SITEMAP_HEADER.search(sm)
    if not m_sm:
        findings.append("FC-03 SITEMAP has no '## Experiments (N files: M "
                        "experiments + 1 TEMPLATE)' header")
    elif (int(m_sm.group(1)) != n_all
          or int(m_sm.group(2)) != len(exp_files)):
        findings.append("FC-03 SITEMAP header claims %s files / %s "
                        "experiments, disk has %d / %d"
                        % (m_sm.group(1), m_sm.group(2), n_all,
                           len(exp_files)))

    # --- FC-04/05/06: README experiments section vs disk -----------------
    rd = (args.root / "README.md").read_text(encoding="utf-8")
    if "## Experiments" not in rd:
        findings.append("FC-04 README has no '## Experiments' section")
    else:
        sec = rd.split("## Experiments", 1)[1].split("\n## ", 1)[0]
        m_sum = README_SUMMARY.search(sec)
        if not m_sum:
            findings.append("FC-04 README experiments summary line missing")
        elif int(m_sum.group(1)) != len(exp_files):
            findings.append("FC-04 README summary claims %s Experiment "
                            "Files, disk has %d"
                            % (m_sum.group(1), len(exp_files)))
        listed = set(README_LINK.findall(sec))
        on_disk = {p.stem for p in exp_files}
        for stem in sorted(on_disk - listed):
            findings.append("FC-05 %s exists on disk but is listed nowhere "
                            "in the README Experiments section" % stem)
        for stem in sorted(listed - on_disk):
            findings.append("FC-05 README lists %s but no such file exists "
                            "on disk" % stem)
        # FC-06: per-group header vs the links under it
        marks = [(m.group(1), int(m.group(2)), m.start(), m.end())
                 for m in README_GROUP.finditer(sec)]
        for i, (name, n, _, end) in enumerate(marks):
            stop = marks[i + 1][2] if i + 1 < len(marks) else len(sec)
            real = len(set(README_LINK.findall(sec[end:stop])))
            if n != real:
                findings.append("FC-06 README group '%s' header claims %d, "
                                "its block links %d" % (name, n, real))

    for f in findings:
        print(esc(f))
    print("fleet_count_parity_check: %d findings (FC-01/02 MI File Counts, "
          "FC-03 SITEMAP header, FC-04/05/06 README experiments) over "
          "%d categories / %d experiments"
          % (len(findings), len(DEFS), len(exp_files)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
