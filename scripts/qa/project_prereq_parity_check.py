#!/usr/bin/env python3
"""project prerequisites parity gate for Minder Academy.

The projects fleet lives in docs/learning-resources/projects: the
7 PROJECT-NNN files the project index lock (PJ-01..06) already
pins to MASTER-INDEX, plus supporting guides the project lock
never saw - PREREQUISITES-NNN.md walkthroughs and SETUP-GUIDE.md.
Born tick-558 at 5 findings: PROJECT-001 and PROJECT-007 carried
rich inline "## Prerequisites" sections (tutorial/lab links) but
never mentioned their own dedicated setup walkthroughs, and none
of the three supporting guides had a MASTER-INDEX row - a learner
browsing the Projects table (the surface that plans their weeks)
could not know PREREQUISITES-001 existed.

PP-01  target resolution: every PREREQUISITES-NNN.md's front-matter
       Document ID matches its filename, its "**For:**" line links
       PROJECT-NNN, and that link resolves to an existing project
       file (a ghost walkthrough or a link to the wrong project is
       a finding).
PP-02  back-link: every PREREQUISITES-NNN's target project body
       links to the walkthrough (navigation is not one-directional;
       the walkthrough links forward, the project must answer).
PP-03  index visibility: the MASTER-INDEX "### Projects" section
       body links every supporting guide in the directory (every
       *.md that is not PROJECT-NNN and not templates/) - bullet
       or table form, only the link target is required.

The project bodies' own inline prerequisite lists stay out of
scope: legacy short ids like "7101: ReAct Loop System" are prose
shorthand that resolve to real phase7 files linked elsewhere in
the same body.

Hard gate (exit 1 on findings): born tick-558 at 5 findings
(2 PP-02 + 3 PP-03), drained in the same tick - back-links added
to both projects' "## Prerequisites" sections and a "Supporting
guides" list added under the MASTER-INDEX Projects table.

Run over the whole corpus:
    python scripts/qa/project_prereq_parity_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PRJ_DIR = "docs/learning-resources/projects"
PREREQ_FILE = re.compile(r"^PREREQUISITES-(\d+)\.md$")
PROJECT_FILE = re.compile(r"^PROJECT-(\d+)[\w-]*\.md$")
FM_ID = re.compile(r"^Document ID: PREREQUISITES-(\d+)", re.M)
FOR_LINE = re.compile(r"\*\*For:\*\* \[PROJECT-(\d+)[^\]]*\]\(([^)]+)\)")
PROJECT_SECTION = re.compile(r"^### Projects \(", re.M)


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []

    prj_dir = args.root / PRJ_DIR
    files = sorted(prj_dir.glob("*.md"))
    project_stems = {p.stem for p in files if PROJECT_FILE.match(p.name)}
    project_ids = {PROJECT_FILE.match(p.stem + ".md").group(1)
                   for p in files if PROJECT_FILE.match(p.name)}
    supporting = [p for p in files
                  if not PROJECT_FILE.match(p.name)]

    # PP-01 + PP-02: per PREREQUISITES-NNN walkthrough
    for p in supporting:
        if not PREREQ_FILE.match(p.name):
            continue
        nnn = PREREQ_FILE.match(p.name).group(1)
        text = p.read_text(encoding="utf-8")
        m_id = FM_ID.search(text)
        if not m_id or m_id.group(1) != nnn:
            findings.append("PP-01 %s: front-matter Document ID %s does "
                            "not match filename"
                            % (p.name,
                               m_id.group(1) if m_id else "missing"))
        m_for = FOR_LINE.search(text)
        if not m_for:
            findings.append("PP-01 %s: no '**For:** [PROJECT-...](...) "
                            "target line" % p.name)
        elif m_for.group(1) != nnn:
            findings.append("PP-01 %s: For-line names PROJECT-%s, file "
                            "is PREREQUISITES-%s"
                            % (p.name, m_for.group(1), nnn))
        else:
            target = (prj_dir / m_for.group(2)).resolve()
            if target.parent != prj_dir.resolve() or not target.exists():
                findings.append("PP-01 %s: For-line link does not resolve "
                                "inside the projects directory" % p.name)
            # PP-02: the project must answer with a back-link
            proj = prj_dir / m_for.group(2).lstrip("./")
            if proj.exists():
                ptext = proj.read_text(encoding="utf-8")
                if ("PREREQUISITES-%s" % nnn) not in ptext:
                    findings.append("PP-02 %s: target project %s never "
                                    "links back to its setup walkthrough"
                                    % (p.name, proj.name))

    # PP-03: MASTER-INDEX visibility for every supporting guide
    master = args.root / "docs" / "00-META" / "MASTER-INDEX.md"
    if not master.exists():
        print("project_prereq_parity_check: SKIP - docs/00-META/MASTER-INDEX.md not found, nothing to check")
        return 0
    mi = master.read_text(encoding="utf-8")
    sec = PROJECT_SECTION.search(mi)
    body = ""
    if sec:
        rest = mi[sec.end():]
        stop = re.search(r"^##+ ", rest, re.M)
        body = rest[:stop.start()] if stop else rest
    else:
        findings.append("PP-03 MASTER-INDEX has no '### Projects' section")
    for p in supporting:
        if p.name + ")" not in body:
            findings.append("PP-03 %s: not linked in MASTER-INDEX's "
                            "Projects section (a learner planning their "
                            "weeks from the table cannot know it exists)"
                            % p.name)

    for f in findings:
        print(esc(f))
    print("project_prereq_parity_check: %d findings (PP-01 target "
          "resolution, PP-02 back-link, PP-03 index visibility) over "
          "%d supporting guides / %d project files"
          % (len(findings), len(supporting), len(project_stems)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
