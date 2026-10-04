#!/usr/bin/env python3
"""sitemap listing parity gate for Minder Academy.

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
SL-04  self-explaining count headers: every registered fleet
       header must keep the "(N files: A x + B y)" decomposition
       form (Experiments' convention) with A+B == N, A equal to
       its part-1 disk definition and B equal to its part-2 disk
       definition.
SL-05  count-header form uniformity: every "##" header that
       carries a count must open with "(N files" (singular
       "(N file" at N==1 - canonical grammar); the suffix after
       it stays free (": decomposition", " in configs/"). SC-01
       already counts every "(N" header under any form, so the
       numbers never depended on this - the form a platform
       parser sees is what was drifting.

SL-05 joined tick-563: the header-form census found 7 of the 29
counted headers carrying the bare "(N)" form (Tutorials, Labs,
Lab Solutions, Cheat Sheets, Interactive, Troubleshooting, Case
Studies) against the corpus convention SC's own docstring
documents ("## Section (N files)") - drained to "(N files)" /
"(N file)" in the same tick, born at zero.

SL-04 joined tick-561: the MI-vs-SITEMAP census over 14 fleet
pairs found 4 definitional divergences (Notebooks 20 vs 21,
Capstone Projects 7 vs 10, Experiments 47 vs 48, Meta Docs 20 vs
11) where each surface was true under its own definition - the
cure is self-explanation on the SITEMAP side: the three bare
headers now decompose themselves and SL-04 locks that
decomposition to disk, so a future drift cannot hide behind a
bare count.

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
territory. Experiments is deliberately absent from SL-04 - its
"(48 files: 47 experiments + 1 TEMPLATE)" header is
fleet_count_parity_check FC-03's territory. The Meta & Reference
"(11 files: 9 reference docs + 2 companion indexes)" suffix is
learner-facing prose, not machine scope: its 9+2 split is a
curated cross-directory set (9 of the 20 00-META top-level docs
plus one bridge plus one resource) that no glob expresses - the
11 count stays SC-locked and the section's reachability
SL-02-locked.

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

# SL-04 registered self-explaining headers: (section name, part-1
# globs, part-2 globs). The header must read "(N files: A ... + B ...)"
# with A+B == N, A == the part-1 disk count and B == the part-2 disk
# count. Experiments is deliberately absent - FC-03's territory.
SELF_EXPLAINING = [
    ("Notebooks",
     ["docs/notebooks/*.ipynb"],
     ["docs/notebooks/README.md"]),
    ("Capstone Projects",
     ["docs/learning-resources/projects/PROJECT-*.md"],
     ["docs/learning-resources/projects/PREREQUISITES-*.md",
      "docs/learning-resources/projects/SETUP-GUIDE.md"]),
]
EXPLAINED = re.compile(r"\((\d+) files: (\d+) [^)]+ \+ (\d+) [^)]+\)$")

# SL-05: counted "##" headers must open with "(N files" (singular
# "(N file" at N==1); whatever follows the prefix stays free. SC-01's
# HEADLINE_NUM takes the number from any form, so this locks the FORM
# only - never a count.
SL05_COUNTED = re.compile(r"^## .+\(\d+\b")
SL05_FILES = re.compile(r"^## .+\(\d+ files?\b")


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
    if not sm_path.exists():
        print("sitemap_listing_parity_check: SKIP - docs/00-META/SITEMAP.md not found, nothing to check")
        return 0
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

    # --- SL-04: self-explaining header arithmetic -------------------------
    for fname, part1, part2 in SELF_EXPLAINING:
        hits = [t for t, _ in secs if t.startswith(fname + " ")]
        if not hits:
            continue  # SL-01 already reports the missing fleet heading
        em = EXPLAINED.search(hits[0])
        if not em:
            findings.append("SL-04 %s: header '%s' lost the self-explaining "
                            "'(N files: A ... + B ...)' form"
                            % (fname, hits[0]))
            continue
        n, a, b = int(em.group(1)), int(em.group(2)), int(em.group(3))
        c1 = sum(len(list(args.root.glob(s))) for s in part1)
        c2 = sum(len(list(args.root.glob(s))) for s in part2)
        if a + b != n:
            findings.append("SL-04 %s: header decomposition %d+%d does not "
                            "equal the header count %d" % (fname, a, b, n))
        if a != c1:
            findings.append("SL-04 %s: header part 1 says %d, its disk "
                            "definition holds %d" % (fname, a, c1))
        if b != c2:
            findings.append("SL-04 %s: header part 2 says %d, its disk "
                            "definition holds %d" % (fname, b, c2))

    # --- SL-05: count-header form uniformity ------------------------------
    n_forms = 0
    for line in text.split("\n"):
        if not SL05_COUNTED.match(line):
            continue
        if not SL05_FILES.match(line):
            findings.append("SL-05 %s: header carries a bare count; the "
                            "corpus form is '(N files ...)' (the number "
                            "stays SC-01-locked, the form a platform "
                            "parser reads must be uniform)"
                            % line[3:].strip())
        else:
            n_forms += 1

    for f in findings:
        print(esc(f))
    print("sitemap_listing_parity_check: %d findings (SL-01 listing "
          "identity across %d fleets, SL-02 corpus completeness, SL-03 "
          "module arithmetic, SL-04 self-explaining headers across %d "
          "registrations, SL-05 count-header forms across %d headers) "
          "over %d sections / %d modules"
          % (len(findings), len(FLEETS), len(SELF_EXPLAINING), n_forms,
             len(secs), n_modules))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
