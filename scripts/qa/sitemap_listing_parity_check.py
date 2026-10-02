#!/usr/bin/env python3
"""sitemap listing parity gate for PROJECT-OMEGA.

The SITEMAP is the curriculum's index of record - the surface a
learner trusts to enumerate what exists. sitemap_claims_check
(SC-00/01) already locks every COUNT claim (each "(N files)" header
against its own bullet entries and against disk, the statistics
block, the per-phase lines), but no gate locked the IDENTITIES
behind those counts. Count parity hides four drift classes: an
entry can link the WRONG existing file (resolves cleanly for
linkcheck, misroutes the learner - the PJ-04 class), a file can be
listed twice inside one section, a fleet file can vanish from its
section while the header drifts with it (both sides wrong together),
and a document can exist with no SITEMAP listing at all (the
CHEAT-SHEET-006 orphan class - unreachable from the index of
record). A third unclaimed surface sat inside the phase sections:
each module header states "(N lessons, M guides)" and nothing
checked that N+M equals the module's own non-boilerplate entries.

Born tick-560 census-proven CLEAN at zero findings: all 19 fleet
sections carry both-direction listing parity against disk, all 33
phase modules satisfy their lesson+guide arithmetic, and every
docs/**/*.md plus the root README is reachable from SITEMAP.md.
The first census pass itself produced 12 phantom "never listed"
files - its link regex only matched "../" forms and missed the
Getting Started section's same-directory links; broadened to all
relative forms, every phantom dissolved. The born state is honestly
zero.

SL-01  fleet-section listing identity parity, both directions: every
       bullet entry in a fleet section must resolve to a member of
       that section's documented disk fleet (no cross-fleet
       misroute, no ghost), every fleet file on disk must be listed
       exactly once in its own section (no orphan, no duplicate).
SL-02  corpus completeness: every docs/**/*.md and the root README
       must be a SITEMAP.md link target at least once - the index
       of record reaches everything a learner can be assigned.
SL-03  module arithmetic: each phase module header's
       "(N lessons, M guides)" equals the module body's non-boiler
       bullet entries (boilerplate = PREREQUISITES, README,
       assessment: PRACTICE, assessment: QUIZ bullets, which the
       lesson/guide split deliberately does not count).

Out of scope, recorded: the Meta & Reference (11 mixed-family
entries across 00-META/bridges/resources), Reference Configuration
(3, a partial listing of configs/), Case Study Appendix (2, a
curated subset of experiments) and Getting Started (11, no count
header) sections stay out of SL-01's fleet map - their counts are
SC-locked and their reachability is SL-02-locked. SITEMAP.md itself
is excluded from the SL-02 corpus (self-listing is circular) and
CHANGELOG.md is not a curriculum document. MI's "Notebooks (20)"
counts *.ipynb only while the SITEMAP Notebooks section counts the
21 listed files including the directory README - a definitional
divergence where both surfaces are true under their own definitions;
cross-surface count comparison is fleet_count_parity_check's
territory.

Hard gate (exit 1 on findings): born at zero, kept there by lock.

Run over the whole corpus:
    python scripts/qa/sitemap_listing_parity_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# SL-01 fleet map: SITEMAP "## <name> ..." section -> disk spec list.
# Paths are repo-root relative; every spec was census-verified at
# born state with exact both-direction parity.
FLEETS = [
    ("Volumes", ["docs/volumes/*.md"]),
    ("Phase Assessments", ["docs/00-META/assessment/*.md"]),
    ("Tutorials", ["docs/learning-resources/tutorials/*.md"]),
    ("Labs", ["docs/learning-resources/labs/*.md"]),
    ("Lab Solutions", ["docs/learning-resources/labs/solutions/*.md"]),
    ("Cheat Sheets", ["docs/learning-resources/cheat-sheets/*.md"]),
    ("Capstone Projects", [
        "docs/learning-resources/projects/PROJECT-*.md",
        "docs/learning-resources/projects/PREREQUISITES-*.md",
        "docs/learning-resources/projects/SETUP-GUIDE.md"]),
    ("Comparisons", ["docs/comparisons/*.md"]),
    ("Diagrams", ["docs/diagrams/*.md"]),
    ("Enterprise Solutions", ["docs/enterprise-solutions/*.md"]),
    ("Industry Applications", ["docs/industry/*.md"]),
    ("Use Cases", ["docs/use-cases/*.md"]),
    ("Notebooks", ["docs/notebooks/README.md", "docs/notebooks/*.ipynb"]),
    ("Project Templates",
     ["docs/learning-resources/projects/templates/*.md"]),
    ("Experiments", ["experiments/*.md"]),
    ("Learning Guides", ["docs/learning-resources/guides/*.md"]),
    ("Interactive", ["docs/learning-resources/interactive/*.md"]),
    ("Troubleshooting", ["docs/learning-resources/troubleshooting/*.md"]),
    ("Case Studies", ["docs/learning-resources/case-studies/*.md"]),
]

ENTRY = re.compile(r"^\s*- \[[^\]]*\]\(([^)#]+)\)", re.M)
ANY_LINK = re.compile(r"\]\(([^)#]+)\)")
MODULE = re.compile(r"^### \[([^\]]+)\] \((\d+) lessons?, (\d+) guides?\)$",
                    re.M)
BOILER = re.compile(
    r"^\s*- \[(PREREQUISITES|README|assessment: (?:PRACTICE|QUIZ))\]", re.M)


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def sections(text: str) -> list[tuple[str, str]]:
    """Split SITEMAP text into (title, body) pairs at '## ' headings."""
    out = []
    for m in re.finditer(r"^## (.+)$", text, re.M):
        start = m.end()
        nxt = re.search(r"^## ", text[start:], re.M)
        body = text[start:start + nxt.start()] if nxt else text[start:]
        out.append((m.group(1).strip(), body))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    args.root = args.root.resolve()
    sm_path = args.root / "docs" / "00-META" / "SITEMAP.md"
    sm_dir = sm_path.parent
    text = sm_path.read_text(encoding="utf-8")
    secs = sections(text)
    findings: list[str] = []
    n_modules = 0

    # --- SL-01: fleet listing identity, both directions ------------------
    for fname, specs in FLEETS:
        hits = [(t, b) for t, b in secs if t.startswith(fname + " ")]
        if not hits:
            findings.append("SL-01 SITEMAP has no '## %s' section (a "
                            "renamed or deleted fleet heading breaks the "
                            "listing lock)" % fname)
            continue
        body = hits[0][1]
        listed: dict[Path, int] = {}
        for lm in ENTRY.finditer(body):
            p = (sm_dir / lm.group(1)).resolve()
            listed[p] = listed.get(p, 0) + 1
        disk = {p.resolve() for spec in specs for p in args.root.glob(spec)}

        def rel(p: Path) -> str:
            try:
                return str(p.relative_to(args.root))
            except ValueError:
                return str(p)

        for p in sorted(listed.keys() - disk):
            findings.append("SL-01 %s: SITEMAP links %s which is not a "
                            "member of the %s fleet (misrouted or ghost "
                            "link)" % (fname, rel(p), fname))
        for p in sorted(disk - listed.keys()):
            findings.append("SL-01 %s: %s exists on disk but is listed "
                            "nowhere in its SITEMAP section"
                            % (fname, rel(p)))
        for p in sorted(p for p, c in listed.items() if c > 1):
            findings.append("SL-01 %s: %s is listed %d times (duplicate "
                            "entry)" % (fname, rel(p), listed[p]))

    # --- SL-02: corpus completeness --------------------------------------
    targets = set()
    for lm in ANY_LINK.finditer(text):
        t = lm.group(1)
        if "://" in t or t.startswith(("mailto:", "#")):
            continue
        targets.add((sm_dir / t).resolve())
    corpus = {p.resolve() for p in (args.root / "docs").rglob("*.md")}
    corpus.add((args.root / "README.md").resolve())
    corpus.discard(sm_path.resolve())
    for p in sorted(corpus - targets):
        findings.append("SL-02 %s exists on disk but is never linked from "
                        "SITEMAP.md (unreachable from the index of record)"
                        % p.relative_to(args.root))

    # --- SL-03: module lesson+guide arithmetic ----------------------------
    for title, body in secs:
        if not re.match(r"Phase \d", title):
            continue
        for mm in MODULE.finditer(body):
            n_modules += 1
            mod, nl, ng = mm.group(1), int(mm.group(2)), int(mm.group(3))
            mend = re.search(r"^### |\Z", body[mm.end():], re.M)
            mbody = (body[mm.end():mm.end() + mend.start()] if mend
                     else body[mm.end():])
            links = len(ENTRY.findall(mbody))
            boiler = len(BOILER.findall(mbody))
            nonboil = links - boiler
            if nl + ng != nonboil:
                findings.append("SL-03 module %s header claims %d+%d, its "
                                "body holds %d non-boilerplate entries "
                                "(%d links incl. %d boilerplate)"
                                % (mod, nl, ng, nonboil, links, boiler))

    for f in findings:
        print(esc(f))
    print("sitemap_listing_parity_check: %d findings (SL-01 listing "
          "identity across %d fleets, SL-02 corpus completeness, SL-03 "
          "module arithmetic) over %d sections / %d modules"
          % (len(findings), len(FLEETS), len(secs), n_modules))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
