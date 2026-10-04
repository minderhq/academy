#!/usr/bin/env python3
"""SITEMAP claims gate for the Minder Academy corpus.

SITEMAP.md calls itself "derived directly from the file tree" - but it
is hand-maintained prose, and while the README's headline numbers were
being locked down (tick-260/261), its Statistics block had quietly
rotted (total 458 vs measured 462, docs 407 vs 408, configs 1 vs 4).
This gate gives SITEMAP.md the same treatment readme_claims_check
gives README.md:

  SC-00  SITEMAP.md missing, or a measurement itself failed
  SC-01  a numeric claim disagrees with its measurement

Three claim families, all regex-matched (a pattern with no match is
silently skipped - when the copy changes shape, teach the new pattern
here rather than letting the gate rot):

  headline vs disk   "## Section (N files)" headers whose section has a
                     natural disk measure (phase dirs, volumes,
                     assessments, learning-resources subdirs, ...)
  headline vs list   every numbered header must equal the number of
                     markdown-list link entries under it (list lines
                     only - inline prose links are not entries; this is
                     what keeps partial listings like "Reference
                     Configuration (3 files in configs/)" legitimate)
  Statistics block   every line of the fenced ```text statistics block

Hard gate (exit 1 on findings): baseline 0 on the clean corpus.

Run over the whole corpus:
    python scripts/qa/sitemap_claims_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

PHASE_DIR = re.compile(r"^phase(\d+)-")
MODULE_DIR = re.compile(r"^\d{4}-")
CASE_STUDY_FILES = ("EXP_1101_GPON.md", "EXP_1102_STAR_TOPOLOGY.md")
LIST_ENTRY = re.compile(r"^\s*-\s*\[[^\]]+\]\([^)]+\)", re.M)


def _md_count(p: Path, recursive: bool = False) -> int:
    """Count .md files under p; a missing path is an empty corpus (0)."""
    if not p.exists():
        return 0
    return len(list(p.rglob("*.md") if recursive else p.glob("*.md")))


# ---- disk measurements ----

def m_repo_docs(root: Path) -> int:
    """Borrow structure_lint's own count - no second walk to drift."""
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent
                             / "structure_lint.py"), "--root", str(root)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    match = re.search(r"structure_lint: (\d+) files scanned",
                      proc.stdout or "")
    if proc.returncode != 0 or match is None:
        raise RuntimeError("structure_lint borrow failed (rc=%d)"
                           % proc.returncode)
    return int(match.group(1))


def m_docs_md(root: Path) -> int:
    return _md_count(root / "docs", recursive=True)


def m_root_md(root: Path) -> int:
    return _md_count(root)


def m_experiments(root: Path) -> int:
    edir = root / "experiments"
    return len(list(edir.glob("EXP_*.md"))) if edir.exists() else 0


def m_experiments_total(root: Path) -> int:
    return m_experiments(root) + (1 if (root / "experiments"
                                        / "TEMPLATE.md").exists() else 0)


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


def _rel(sub: str):
    def measure(root: Path) -> int:
        return _md_count(root / "docs" / sub)
    return measure


def m_configs(root: Path) -> int:
    cfg = root / "configs"
    if not cfg.exists():
        return 0
    return len([p for p in cfg.rglob("*") if p.is_file()])


def m_case_study(root: Path) -> int:
    return sum(1 for n in CASE_STUDY_FILES
               if (root / "experiments" / n).exists())


# Section header prefix -> disk measurement. Sections without a
# natural disk measure (single-doc listings, the mixed Meta & Reference
# family, partial configs listing) are checked headline-vs-list only.
HEADLINE_MEASURES = [
    ("Phase 1 ", m_phase_md(1)), ("Phase 2 ", m_phase_md(2)),
    ("Phase 3 ", m_phase_md(3)), ("Phase 4 ", m_phase_md(4)),
    ("Phase 5 ", m_phase_md(5)), ("Phase 6 ", m_phase_md(6)),
    ("Phase 7 ", m_phase_md(7)),
    ("Volumes", _rel("volumes")),
    ("Phase Assessments", _rel("00-META/assessment")),
    ("Experiments", m_experiments_total),
    ("Tutorials", _rel("learning-resources/tutorials")),
    ("Labs (", _rel("learning-resources/labs")),
    ("Lab Solutions", _rel("learning-resources/labs/solutions")),
    ("Capstone Projects", _rel("learning-resources/projects")),
    ("Cheat Sheets", _rel("learning-resources/cheat-sheets")),
    ("Learning Guides", _rel("learning-resources/guides")),
    ("Comparisons", _rel("comparisons")),
    ("Diagrams", _rel("diagrams")),
    ("Enterprise Solutions", _rel("enterprise-solutions")),
    ("Industry Applications", _rel("industry")),
    ("Use Cases", _rel("use-cases")),
    ("Project Templates", _rel("learning-resources/projects/templates")),
    ("Case Study Appendix", m_case_study),
]

# Statistics-block claims: (label, line regex, measures tuple). re.M,
# anchored; first match only. A two-element measure tuple consumes two
# capture groups in order.
STATS = [
    ("total files", re.compile(r"^Total markdown files: (\d+)$", re.M),
     (m_repo_docs,)),
    ("docs split", re.compile(r"^  docs/: (\d+), experiments/: (\d+), "
                              r"configs/: (\d+), repo root: (\d+)$", re.M),
     (m_docs_md, m_experiments_total, m_configs, m_root_md)),
    ("phases", re.compile(r"^Phases: (\d+)$", re.M), (m_phases,)),
    ("modules", re.compile(r"^Learning modules \(topics\): (\d+)$", re.M),
     (m_modules,)),
    ("phase files", re.compile(r"^Phase files [^:]*: (\d+)$", re.M),
     (m_phase_total,)),
    ("volume guides", re.compile(r"^Volume guides: (\d+)$", re.M),
     (_rel("volumes"),)),
    ("assessment sets", re.compile(r"^Phase assessment sets: (\d+)", re.M),
     (_rel("00-META/assessment"),)),
    ("experiments", re.compile(r"^Experiments: (\d+) \(\+ TEMPLATE\)$", re.M),
     (m_experiments,)),
    ("tutorials", re.compile(r"^Tutorials: (\d+)$", re.M),
     (_rel("learning-resources/tutorials"),)),
    ("labs", re.compile(r"^Labs: (\d+) \(\+ (\d+) solutions\)$", re.M),
     (_rel("learning-resources/labs"),
      _rel("learning-resources/labs/solutions"))),
    ("capstone projects", re.compile(r"^Capstone projects: (\d+)$", re.M),
     (_rel("learning-resources/projects"),)),
    ("project templates", re.compile(r"^Project templates: (\d+)$", re.M),
     (_rel("learning-resources/projects/templates"),)),
    ("cheat sheets", re.compile(r"^Cheat sheets: (\d+)$", re.M),
     (_rel("learning-resources/cheat-sheets"),)),
    ("learning guides", re.compile(r"^Learning guides: (\d+)$", re.M),
     (_rel("learning-resources/guides"),)),
    ("cmp/diag/ent",
     re.compile(r"^Comparisons: (\d+) \| Diagrams: (\d+) \| "
                r"Enterprise solutions: (\d+)$", re.M),
     (_rel("comparisons"), _rel("diagrams"), _rel("enterprise-solutions"))),
    ("ind/uc/nb",
     re.compile(r"^Industry applications: (\d+) \| Use cases: (\d+) \| "
                r"Notebooks: (\d+)$", re.M),
     (_rel("industry"), _rel("use-cases"), None)),  # notebooks: no md measure
]

HEADLINE_NUM = re.compile(r"\((\d+)\b")
PHASE_LINE = re.compile(r"^  Phase (\d) - .+: (\d+)$", re.M)  # .+: names may contain colons (Phase 5 "Model Adaptation: ...")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    sitemap = args.root / "docs" / "00-META" / "SITEMAP.md"
    if not sitemap.exists():
        print("SC-00 SITEMAP.md not found under docs/00-META")
        return 1
    text = sitemap.read_text(encoding="utf-8")
    checked = 0

    def note(ok: bool, msg: str) -> None:
        nonlocal checked
        checked += 1
        if not ok:
            findings.append("SC-01 " + msg)

    # ---- family 1+2: section headlines vs disk and vs list entries ----
    for sec in re.split(r"^## ", text, flags=re.M)[1:]:
        title = sec.split("\n", 1)[0].strip()
        num_m = HEADLINE_NUM.search(title)
        if num_m is None:
            continue
        claimed = int(num_m.group(1))
        entries = len(LIST_ENTRY.findall(
            sec.split("\n", 1)[1] if "\n" in sec else ""))
        note(claimed == entries,
             "SITEMAP header '%s' claims %d but lists %d entries"
             % (title, claimed, entries))
        measure = next((m for prefix, m in HEADLINE_MEASURES
                        if title.startswith(prefix)), None)
        if measure is None:
            continue
        try:
            actual = measure(args.root)
        except (OSError, RuntimeError) as exc:
            findings.append("SC-00 could not measure '%s': %s"
                            % (title, exc))
            continue
        note(claimed == actual,
             "SITEMAP header '%s' claims %d but disk measures %d"
             % (title, claimed, actual))

    # ---- family 3: the fenced statistics block ----
    for label, pattern, measures in STATS:
        match = pattern.search(text)
        if match is None:
            continue
        groups = match.groups()
        for value, measure in zip(groups, measures):
            if measure is None:
                continue  # notebooks count is an index-doc claim, not md
            try:
                actual = measure(args.root)
            except (OSError, RuntimeError) as exc:
                findings.append("SC-00 could not measure %s: %s"
                                % (label, exc))
                continue
            note(int(value) == actual,
                 "SITEMAP statistics claims %s=%s but disk measures %d"
                 % (label, value, actual))

    # per-phase statistics lines: "  Phase N - Name: count"
    for match in PHASE_LINE.finditer(text):
        phase_no, claimed = int(match.group(1)), int(match.group(2))
        if 1 <= phase_no <= m_phases(args.root):
            try:
                actual = m_phase_md(phase_no)(args.root)
            except (OSError, RuntimeError) as exc:
                findings.append("SC-00 could not measure phase %d: %s"
                                % (phase_no, exc))
                continue
            note(claimed == actual,
                 "SITEMAP statistics claims %d files for phase %d but disk "
                 "measures %d" % (claimed, phase_no, actual))

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print("sitemap_claims_check: %d findings (%d claims checked)"
          % (len(findings), checked))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
