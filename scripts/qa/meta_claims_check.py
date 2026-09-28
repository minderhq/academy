#!/usr/bin/env python3
"""Meta-entry claims gate for the PROJECT-OMEGA corpus.

After README (tick-261) and SITEMAP (tick-262), the remaining count-
bearing entry documents are FAQ.md, MASTER-INDEX.md,
ORGANIZATION-GUIDE.md, VOLUME-GUIDE.md and PROGRESS-TRACKER.md. They
had rotted the same way while every README wave moved the corpus
numbers (FAQ still said "463 documents ... 30 hands-on labs ...
46 experiments"; MASTER-INDEX claimed 427 total files and a "Module
Documents: 256" family that no longer matches how the corpus is laid
out; VOLUME-GUIDE still said "85 files across 7 volumes" with
"(6 files)" tutorials; PROGRESS-TRACKER still targeted "0/97 core
files" with "(15 files)" on a 39-file volume). This gate locks all
five to disk so the next wave cannot rot them again:

  MC-00  a meta entry file is missing, or a measurement itself failed
  MC-01  a numeric claim disagrees with its measurement

Claim families, all regex-matched (a pattern with no match is silently
skipped - when the copy changes shape, teach the new pattern here
rather than letting the gate rot):

  FAQ sentence    the "It consists of N documents across ..." intro
                  sentence (7 numbers vs disk)
  MASTER-INDEX    Total Files line, per-phase Status rows, numbered
                  section headers, the Lab header's 3-way split, the
                  File Counts block line by line (incl. TOTAL as the
                  sum of its own block, both as written and as
                  measured), and every module-table "N docs" cell
  ORG-GUIDE tree  the "N files" / "N tutorial files" / ... labels
  VOLUME-GUIDE    the file-tree labels (tutorials, labs 2-way split,
                  cheat sheets, projects, experiments, SITEMAP line),
                  and the Total Documents footer
  PROGRESS-TRACKER  the per-volume progress bars and "(N files)"
                  headers (vs phase documents on disk), the Total
                  bar and Core Documents target (vs docs/), the
                  SITEMAP line and the stats table targets

Hard gate (exit 1 on findings): baseline 0 on the clean corpus.

Run over the whole corpus:
    python scripts/qa/meta_claims_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PHASE_DIR = re.compile(r"^phase(\d+)-")
MODULE_DIR = re.compile(r"^\d{4}-")

TOTAL_LINE = re.compile(r"^\*\*Total Files:\*\* (\d+) markdown files "
                        r"\(docs/\)$", re.M)
PHASE_ROW = re.compile(r"^\*\*Status:\*\*.*\*\*Modules:\*\* (\d+) \| "
                       r"\*\*Documents:\*\* (\d+)$", re.M)
FILE_COUNT_ROW = re.compile(r"^\| \*\*([^*]+)\*\* \| (\d+) \|$",
                            re.M)
TOTAL_ROW = re.compile(r"^\| \*\*TOTAL\*\* \| \*\*(\d+)\*\* \|$",
                       re.M)
MODULE_CELL = re.compile(
    r"\| \*\*\[(\d{4})\]\([^)]+\)\*\* \| [^|]* \| (\d+) docs? \|")

FAQ_SENTENCE = re.compile(
    r"It consists of (\d+) documents across (\d+) phases, "
    r"(\d+) hands-on labs(?: \(\+(\d+) solutions\))?, "
    r"(\d+) experiments, (\d+) tutorials, and (\d+) cheat sheets")

LAB_HEADER = re.compile(r"^### Labs \((\d+) files: (\d+) labs \+ "
                        r"(\d+) solutions\)$", re.M)

ORG_DOCS = re.compile(r"# All documentation \((\d+) files\)")
ORG_EXPERIMENTS = re.compile(r"# Experiment files \((\d+)\)")
ORG_TUTORIALS = re.compile(r"# (\d+) tutorial files")
ORG_CHEATS = re.compile(r"# (\d+) cheat sheets")

# VOLUME-GUIDE file-tree labels (comment text is part of the pattern;
# rewording the tree means teaching the new wording here)
VG_SITEMAP = re.compile(r"# All (\d+) documents")
VG_TUTORIALS = re.compile(r"# Step-by-step tutorials \((\d+) files\)")
VG_LABS = re.compile(r"# Hands-on lab exercises \((\d+) labs \+ "
                     r"(\d+) solutions\)")
VG_CHEATS = re.compile(r"# Quick reference guides \((\d+) files\)")
VG_PROJECTS = re.compile(r"# Capstone projects \((\d+) files\)")
VG_EXPERIMENTS = re.compile(r"# Practical experiments \((\d+) files\)")
VG_TOTAL = re.compile(r"^\*\*Total Documents:\*\* (\d+) files across "
                      r"(\d+) volumes$", re.M)

# PROGRESS-TRACKER: progress bars (percent and filled fraction vary as
# the learner checks boxes - only the target number is locked),
# volume headers, SITEMAP line and stats-table targets
PT_VOLUME_BAR = re.compile(r"^Volume (\d+): [^[\n]*\[[^\]]*\] "
                           r"\d+% \(\d+/(\d+)\)$", re.M)
PT_TOTAL_BAR = re.compile(r"^Total: [^[\n]*\[[^\]]*\] "
                          r"\d+% \(\d+/(\d+) core files\)$", re.M)
PT_VOLUME_HEADER = re.compile(r"^### Volume (\d+): [^(]+"
                              r"\((\d+) files\)$", re.M)
PT_SITEMAP = re.compile(r"Full document list \((\d+) files\)")
PT_VOLUMES_STAT = re.compile(r"^\| \*\*Volumes Completed\*\* \| (\d+) \|",
                             re.M)
PT_CORE_DOCS = re.compile(r"^\| \*\*Core Documents\*\* \| (\d+) \|", re.M)
PT_LABS_STAT = re.compile(r"^\| \*\*Labs Completed\*\* \| (\d+) \|", re.M)
PT_EXPERIMENTS_STAT = re.compile(r"^\| \*\*Experiments\*\* \| (\d+) \|",
                                 re.M)
PT_TUTORIALS_STAT = re.compile(r"^\| \*\*Tutorials\*\* \| (\d+) \|", re.M)
PT_CAPSTONE = re.compile(r"^\| \*\*Capstone Projects\*\* \| (\d+)\+? \|",
                         re.M)

HEADLINE_NUM = re.compile(r"\((\d+)\b")


def _md_count(p: Path, recursive: bool = False) -> int:
    """Count .md files under p; a missing path is an empty corpus (0)."""
    if not p.exists():
        return 0
    return len(list(p.rglob("*.md") if recursive else p.glob("*.md")))


# ---- disk measurements ----

def m_docs_md(root: Path) -> int:
    return _md_count(root / "docs", recursive=True)


def m_phases(root: Path) -> int:
    pdir = root / "docs" / "phases"
    if not pdir.exists():
        return 0
    return len([d for d in pdir.iterdir()
                if d.is_dir() and PHASE_DIR.match(d.name)])


def m_modules(root: Path) -> int:
    pdir = root / "docs" / "phases"
    if not pdir.exists():
        return 0
    return len([d for p in pdir.iterdir() if p.is_dir()
                for d in p.iterdir()
                if d.is_dir() and MODULE_DIR.match(d.name)])


def m_phase_md(phase_no: int):
    def measure(root: Path) -> int:
        pdir = root / "docs" / "phases"
        if not pdir.exists():
            return 0
        for d in pdir.iterdir():
            if d.is_dir() and PHASE_DIR.match(d.name) \
                    and PHASE_DIR.match(d.name).group(1) == str(phase_no):
                return len(list(d.rglob("*.md")))
        return 0
    return measure


def m_phase_total(root: Path) -> int:
    return sum(m_phase_md(n)(root) for n in range(1, m_phases(root) + 1))


def m_module_sizes(root: Path) -> dict[int, int]:
    """Module number (the 4-digit dir prefix) -> lesson-file count.

    The "N docs" table cells count LESSON files only (files named
    ``NNNN-*.md``); module README/QUIZ/PRACTICE are navigation, not
    documents (baseline: 114 lessons across all 33 modules).
    """
    pdir = root / "docs" / "phases"
    sizes: dict[int, int] = {}
    if not pdir.exists():
        return sizes
    for p in pdir.iterdir():
        if p.is_dir() and PHASE_DIR.match(p.name):
            for d in p.iterdir():
                if d.is_dir() and MODULE_DIR.match(d.name):
                    sizes[int(d.name[:4])] = sum(
                        1 for f in d.rglob("*.md") if f.is_file()
                        and MODULE_DIR.match(f.name))
    return sizes


def _rel(sub: str):
    def measure(root: Path) -> int:
        return _md_count(root / "docs" / sub)
    return measure


def m_experiments(root: Path) -> int:
    edir = root / "experiments"
    return len(list(edir.glob("EXP_*.md"))) if edir.exists() else 0


def m_projects(root: Path) -> int:
    pdir = root / "docs" / "learning-resources" / "projects"
    if not pdir.exists():
        return 0
    return len(list(pdir.glob("PROJECT-*.md")))


def m_module_flag(fname: str):
    def measure(root: Path) -> int:
        pdir = root / "docs" / "phases"
        if not pdir.exists():
            return 0
        return sum(1 for p in pdir.iterdir() if p.is_dir()
                   for d in p.rglob(fname))
    return measure


def m_assessment(kind: str):
    def measure(root: Path) -> int:
        adir = root / "docs" / "00-META" / "assessment"
        if not adir.exists():
            return 0
        return len(list(adir.glob("phase*-%s.md" % kind)))
    return measure


def m_meta_docs(root: Path) -> int:
    mdir = root / "docs" / "00-META"
    return _md_count(mdir, recursive=False) if mdir.exists() else 0


def m_labs(root: Path) -> int:
    return _md_count(root / "docs" / "learning-resources" / "labs")


def m_solutions(root: Path) -> int:
    return _md_count(root / "docs" / "learning-resources"
                     / "labs" / "solutions")


# MASTER-INDEX numbered section prefix -> disk measurement. Sections
# without a natural disk measure (Bridges, topic guides) never match a
# prefix and are skipped deliberately.
SECTION_MEASURES = [
    ("Tutorials", _rel("learning-resources/tutorials")),
    ("Labs (", lambda root: m_labs(root) + m_solutions(root)),
    ("Cheat Sheets", _rel("learning-resources/cheat-sheets")),
    ("Projects", m_projects),
    ("Career Guides", _rel("learning-resources/guides")),
    ("Phase Practice Files", m_assessment("practice")),
    ("Phase Quiz Files", m_assessment("quiz")),
    ("Comparisons", _rel("comparisons")),
    ("Industry Applications", _rel("industry")),
    ("Use Cases", _rel("use-cases")),
    ("Solutions", _rel("enterprise-solutions")),
    ("Diagrams", _rel("diagrams")),
]

# File Counts block: row label -> disk measurement. TOTAL is handled
# separately (sum of its own block).
FILE_COUNT_MEASURES = {
    "Phase READMEs": m_phases,
    "Module READMEs": m_modules,
    "Phase Documents": m_phase_total,
    "Tutorials": _rel("learning-resources/tutorials"),
    "Labs": m_labs,
    "Lab Solutions": m_solutions,
    "Practice Files": m_module_flag("PRACTICE.md"),
    "Quiz Files": m_module_flag("QUIZ.md"),
    "Cheat Sheets": _rel("learning-resources/cheat-sheets"),
    "Projects": m_projects,
    "Experiments": m_experiments,
    "Comparisons": _rel("comparisons"),
    "Use Cases": _rel("use-cases"),
    "Industry Docs": _rel("industry"),
    "Solutions": _rel("enterprise-solutions"),
    "Diagrams": _rel("diagrams"),
    "Meta Docs": m_meta_docs,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    checked = 0

    def note(ok: bool, msg: str) -> None:
        nonlocal checked
        checked += 1
        if not ok:
            findings.append("MC-01 " + msg)

    def measure(guard_label: str, fn, *rest) -> int | None:
        """Measure, turning any failure into MC-00 (skip the claim)."""
        try:
            return fn(args.root, *rest)
        except (OSError, RuntimeError) as exc:
            findings.append("MC-00 could not measure %s: %s"
                            % (guard_label, exc))
            return None

    # ---- FAQ: the intro count sentence ----
    faq = args.root / "docs" / "00-META" / "FAQ.md"
    faq_measures = (m_docs_md, m_phases, m_labs, m_solutions,
                    m_experiments, _rel("learning-resources/tutorials"),
                    _rel("learning-resources/cheat-sheets"))
    if not faq.exists():
        print("MC-00 FAQ.md not found under docs/00-META")
        return 1
    match = FAQ_SENTENCE.search(faq.read_text(encoding="utf-8"))
    if match is not None:
        labels = ("documents", "phases", "labs", "solutions",
                  "experiments", "tutorials", "cheat sheets")
        for value, label, mfn in zip(match.groups(), labels, faq_measures):
            if value is None:
                continue  # optional "(+N solutions)" group absent
            actual = measure("FAQ %s" % label, mfn)
            if actual is None:
                continue
            note(int(value) == actual,
                 "FAQ claims %s=%s but disk measures %d"
                 % (label, value, actual))

    # ---- MASTER-INDEX ----
    mi = args.root / "docs" / "00-META" / "MASTER-INDEX.md"
    if not mi.exists():
        print("MC-00 MASTER-INDEX.md not found under docs/00-META")
        return 1
    text = mi.read_text(encoding="utf-8")

    match = TOTAL_LINE.search(text)
    if match is not None:
        actual = measure("MASTER-INDEX total", m_docs_md)
        if actual is not None:
            note(int(match.group(1)) == actual,
                 "MASTER-INDEX claims %s total files but disk measures %d"
                 % (match.group(1), actual))

    # per-phase Status rows, in document order = phase order
    phase_rows = list(PHASE_ROW.finditer(text))
    n_phases = m_phases(args.root)
    if phase_rows:
        note(len(phase_rows) == n_phases,
             "MASTER-INDEX has %d phase Status rows but disk measures %d "
             "phases" % (len(phase_rows), n_phases))
    for idx, row in enumerate(phase_rows, 1):
        if idx > n_phases:
            break
        mods = measure("phase %d modules" % idx, m_module_sizes)
        if mods is not None:
            phase_mods = len([k for k in mods if k // 1000 == idx])
            note(int(row.group(1)) == phase_mods,
                 "MASTER-INDEX claims %s modules for phase %d but disk "
                 "measures %d" % (row.group(1), idx, phase_mods))
        actual = measure("phase %d files" % idx, m_phase_md(idx))
        if actual is not None:
            note(int(row.group(2)) == actual,
                 "MASTER-INDEX claims %s documents for phase %d but disk "
                 "measures %d" % (row.group(2), idx, actual))

    # numbered section headers vs disk
    for sec in re.split(r"^### ", text, flags=re.M)[1:]:
        title = sec.split("\n", 1)[0].strip()
        num_m = HEADLINE_NUM.search(title)
        if num_m is None:
            continue
        measure_fn = next((m for prefix, m in SECTION_MEASURES
                           if title.startswith(prefix)), None)
        if measure_fn is None:
            continue
        actual = measure("MASTER-INDEX section '%s'" % title, measure_fn)
        if actual is None:
            continue
        note(int(num_m.group(1)) == actual,
             "MASTER-INDEX header '%s' claims %s but disk measures %d"
             % (title, num_m.group(1), actual))

    # the Lab header's 3-way split ("N files: L labs + S solutions")
    match = LAB_HEADER.search(text)
    if match is not None:
        for value, label, mfn in zip(match.groups(),
                                     ("lab files total", "labs",
                                      "lab solutions"),
                                     (lambda r: m_labs(r) + m_solutions(r),
                                      m_labs, m_solutions)):
            actual = measure("MASTER-INDEX lab header %s" % label, mfn)
            if actual is None:
                continue
            note(int(value) == actual,
                 "MASTER-INDEX lab header claims %s=%s but disk measures "
                 "%d" % (label, value, actual))

    # File Counts block: row by row, then TOTAL as the block's own sum
    rows: list[tuple[str, int]] = []
    for row_match in FILE_COUNT_ROW.finditer(text):
        label, value = row_match.group(1), int(row_match.group(2))
        rows.append((label, value))
        measure_fn = FILE_COUNT_MEASURES.get(label)
        if measure_fn is None:
            continue
        actual = measure("MASTER-INDEX File Counts %s" % label, measure_fn)
        if actual is None:
            continue
        note(value == actual,
             "MASTER-INDEX File Counts claims %s=%d but disk measures %d"
             % (label, value, actual))
    total_rows = [int(v) for v in TOTAL_ROW.findall(text)]
    all_known = all(label in FILE_COUNT_MEASURES for label, _ in rows)
    if rows and total_rows:
        written_sum = sum(v for _, v in rows)
        note(total_rows[0] == written_sum,
             "MASTER-INDEX File Counts TOTAL=%d but its own rows sum to %d"
             % (total_rows[0], written_sum))
        if all_known:
            measured_sum = 0
            failed = False
            for label, _ in rows:
                actual = measure(
                    "MASTER-INDEX File Counts %s (sum)" % label,
                    FILE_COUNT_MEASURES[label])
                if actual is None:
                    failed = True
                    break
                measured_sum += actual
            if not failed:
                note(total_rows[0] == measured_sum,
                     "MASTER-INDEX File Counts TOTAL=%d but disk measures "
                     "%d" % (total_rows[0], measured_sum))

    # module-table "N docs" cells vs the module dir on disk
    module_sizes = measure("module sizes", m_module_sizes)
    if module_sizes is not None:
        for cell in MODULE_CELL.finditer(text):
            mod_no, claimed = int(cell.group(1)), int(cell.group(2))
            if mod_no not in module_sizes:
                continue  # linked module dir vanished: linkcheck's job
            note(claimed == module_sizes[mod_no],
                 "MASTER-INDEX module table claims %d docs for module %d "
                 "but disk measures %d" % (claimed, mod_no,
                                           module_sizes[mod_no]))

    # ---- ORGANIZATION-GUIDE tree labels ----
    og = args.root / "docs" / "00-META" / "ORGANIZATION-GUIDE.md"
    if not og.exists():
        print("MC-00 ORGANIZATION-GUIDE.md not found under docs/00-META")
        return 1
    og_text = og.read_text(encoding="utf-8")
    org_claims = [
        (ORG_DOCS, m_docs_md, "all documentation files"),
        (ORG_EXPERIMENTS, m_experiments, "experiment files"),
        (ORG_TUTORIALS, _rel("learning-resources/tutorials"),
         "tutorial files"),
        (ORG_CHEATS, _rel("learning-resources/cheat-sheets"),
         "cheat sheets"),
    ]
    for pattern, mfn, label in org_claims:
        match = pattern.search(og_text)
        if match is None:
            continue
        actual = measure("ORGANIZATION-GUIDE %s" % label, mfn)
        if actual is None:
            continue
        note(int(match.group(1)) == actual,
             "ORGANIZATION-GUIDE claims %s=%s but disk measures %d"
             % (label, match.group(1), actual))

    # ---- VOLUME-GUIDE tree labels and Total Documents footer ----
    vg = args.root / "docs" / "00-META" / "VOLUME-GUIDE.md"
    if not vg.exists():
        print("MC-00 VOLUME-GUIDE.md not found under docs/00-META")
        return 1
    vg_text = vg.read_text(encoding="utf-8")
    vg_claims = [
        (VG_SITEMAP, m_docs_md, "SITEMAP document count"),
        (VG_TUTORIALS, _rel("learning-resources/tutorials"),
         "tutorial files"),
        (VG_CHEATS, _rel("learning-resources/cheat-sheets"),
         "cheat sheet files"),
        (VG_PROJECTS, m_projects, "capstone project files"),
        (VG_EXPERIMENTS, m_experiments, "experiment files"),
    ]
    for pattern, mfn, label in vg_claims:
        match = pattern.search(vg_text)
        if match is None:
            continue
        actual = measure("VOLUME-GUIDE %s" % label, mfn)
        if actual is None:
            continue
        note(int(match.group(1)) == actual,
             "VOLUME-GUIDE claims %s=%s but disk measures %d"
             % (label, match.group(1), actual))

    match = VG_LABS.search(vg_text)
    if match is not None:
        for value, label, mfn in zip(match.groups(),
                                     ("labs", "lab solutions"),
                                     (m_labs, m_solutions)):
            actual = measure("VOLUME-GUIDE labs %s" % label, mfn)
            if actual is None:
                continue
            note(int(value) == actual,
                 "VOLUME-GUIDE claims %s=%s but disk measures %d"
                 % (label, value, actual))

    match = VG_TOTAL.search(vg_text)
    if match is not None:
        docs = measure("VOLUME-GUIDE total files", m_docs_md)
        phases = measure("VOLUME-GUIDE volume count", m_phases)
        if docs is not None:
            note(int(match.group(1)) == docs,
                 "VOLUME-GUIDE claims %s total files but disk measures %d"
                 % (match.group(1), docs))
        if phases is not None:
            note(int(match.group(2)) == phases,
                 "VOLUME-GUIDE claims %s volumes but disk measures %d "
                 "phases" % (match.group(2), phases))

    # ---- PROGRESS-TRACKER bars, headers and stats table ----
    pt = args.root / "docs" / "00-META" / "PROGRESS-TRACKER.md"
    if not pt.exists():
        print("MC-00 PROGRESS-TRACKER.md not found under docs/00-META")
        return 1
    pt_text = pt.read_text(encoding="utf-8")
    pt_claims = [
        (PT_SITEMAP, m_docs_md, "SITEMAP document count"),
        (PT_VOLUMES_STAT, m_phases, "volumes completed"),
        (PT_CORE_DOCS, m_docs_md, "core documents"),
        (PT_LABS_STAT, m_labs, "labs"),
        (PT_EXPERIMENTS_STAT, m_experiments, "experiments"),
        (PT_TUTORIALS_STAT, _rel("learning-resources/tutorials"),
         "tutorials"),
        (PT_CAPSTONE, m_projects, "capstone projects"),
    ]
    for pattern, mfn, label in pt_claims:
        match = pattern.search(pt_text)
        if match is None:
            continue
        actual = measure("PROGRESS-TRACKER %s" % label, mfn)
        if actual is None:
            continue
        note(int(match.group(1)) == actual,
             "PROGRESS-TRACKER claims %s=%s but disk measures %d"
             % (label, match.group(1), actual))

    for kind, pattern in (("bar", PT_VOLUME_BAR),
                          ("header", PT_VOLUME_HEADER)):
        for vm in pattern.finditer(pt_text):
            vol, claimed = int(vm.group(1)), int(vm.group(2))
            actual = measure("PROGRESS-TRACKER volume %d %s" % (vol, kind),
                             m_phase_md(vol))
            if actual is None:
                continue
            note(claimed == actual,
                 "PROGRESS-TRACKER volume %d %s claims %d files but disk "
                 "measures %d" % (vol, kind, claimed, actual))

    match = PT_TOTAL_BAR.search(pt_text)
    if match is not None:
        actual = measure("PROGRESS-TRACKER total bar", m_docs_md)
        if actual is not None:
            note(int(match.group(1)) == actual,
                 "PROGRESS-TRACKER total bar claims %s core files but "
                 "disk measures %d" % (match.group(1), actual))

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print("meta_claims_check: %d findings (%d claims checked)"
          % (len(findings), checked))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
