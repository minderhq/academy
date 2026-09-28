#!/usr/bin/env python3
"""README claims gate for the PROJECT-OMEGA corpus.

The README carries the repo's headline numbers - docs files,
experiments, labs, tutorials, cheat sheets, per-phase document
counts - and those numbers drifted twice in a row (tick-260: the
"463 files" badge vs a measured 408/462; tick-261: experiments
46 vs 47, labs 30 vs 15, cheat-sheet-family counts, a stale
per-phase table). Every claim here is measurable on disk, so this
gate locks each claim to its measured source instead of trusting
prose to stay current:

  RC-00  README.md missing, or the structure_lint borrow failed
  RC-01  a numeric claim in README.md disagrees with disk

Claims are matched by regex, not position, and a pattern that no
longer matches is silently skipped - when the README copy changes
shape, teach the new pattern here rather than letting the gate
rot. Known non-measurable claims (3 learning tracks, "46
experiments"-style prose that is actually covered by a pattern
here) are documented rather than guessed.

Hard gate (exit 1 on findings): baseline 0 on the clean corpus.

Run over the whole corpus:
    python scripts/qa/readme_claims_check.py --root .
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


def _md_count(p: Path, recursive: bool = False) -> int:
    """Count .md files under p; a missing path is an empty corpus (0)."""
    if not p.exists():
        return 0
    return len(list(p.rglob("*.md") if recursive else p.glob("*.md")))


# ---- measurement functions (each returns the disk-truth number) ----

def m_docs_md(root: Path) -> int:
    return _md_count(root / "docs", recursive=True)


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


def m_experiments(root: Path) -> int:
    edir = root / "experiments"
    if not edir.exists():
        return 0
    return len(list(edir.glob("EXP_*.md")))


def m_practice(root: Path) -> int:
    ddir = root / "docs"
    if not ddir.exists():
        return 0
    return len(list(ddir.rglob("PRACTICE.md")))


def m_quiz(root: Path) -> int:
    return sum(1 for _ in (root / "docs").rglob("QUIZ.md")) if (root / "docs").exists() else 0


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


def m_labs(root: Path) -> int:
    return _md_count(root / "docs" / "learning-resources" / "labs")


def m_tutorials(root: Path) -> int:
    return _md_count(root / "docs" / "learning-resources" / "tutorials")


def m_projects(root: Path) -> int:
    return _md_count(root / "docs" / "learning-resources" / "projects", recursive=True)


def m_cheat(root: Path) -> int:
    return _md_count(root / "docs" / "learning-resources" / "cheat-sheets")


def m_lr_all(root: Path) -> int:
    return _md_count(root / "docs" / "learning-resources", recursive=True)


def m_usecases_family(root: Path) -> int:
    total = 0
    for name in ("use-cases", "comparisons", "industry"):
        total += _md_count(root / "docs" / name, recursive=True)
    return total


def m_configs(root: Path) -> int:
    cfg = root / "configs"
    if not cfg.exists():
        return 0
    return len([p for p in cfg.rglob("*") if p.is_file()])


def m_case_study(root: Path) -> int:
    return sum(1 for n in CASE_STUDY_FILES
               if (root / "experiments" / n).exists())


def m_phase_md(phase_no: int):
    def measure(root: Path) -> int:
        total = 0
        pdir = root / "docs" / "phases"
        if not pdir.exists():
            return 0
        for d in pdir.iterdir():
            if d.is_dir() and PHASE_DIR.match(d.name) \
                    and PHASE_DIR.match(d.name).group(1) == str(phase_no):
                total += len(list(d.rglob("*.md")))
        return total
    return measure


def m_phase_total(root: Path) -> int:
    return sum(m_phase_md(n)(root) for n in range(1, m_phases(root) + 1))


# ---- (label, README pattern, measurement) - a pattern with no match
# in README.md is skipped on purpose (see docstring). ----

CLAIMS: list[tuple[str, re.Pattern[str], object]] = [
    ("docs badge", re.compile(r"Docs-(\d+)%20Files"), m_docs_md),
    ("phases badge", re.compile(r"Phases-(\d+)"), m_phases),
    ("modules badge", re.compile(r"Modules-(\d+)"), m_modules),
    ("repo-wide files", re.compile(r"\*\*(\d+) files\*\*"), m_repo_docs),
    ("PRACTICE files", re.compile(r"\*\*(\d+) PRACTICE [Ff]iles\*\*"),
     m_practice),
    ("experiments (prose)",
     re.compile(r"\*\*(\d+) experiments?\*\*"), m_experiments),
    ("Experiment Files", re.compile(r"\*\*(\d+) Experiment Files\*\*"),
     m_experiments),
    ("experiments table",
     re.compile(r"^\|\s*Experiments\s*\|\s*(\d+)\s*\|", re.M),
     m_experiments),
    ("QUIZ files", re.compile(r"\*\*(\d+) QUIZ Files\*\*"), m_quiz),
    ("QUIZ table", re.compile(r"^\|\s*QUIZ Files\s*\|\s*(\d+)\s*\|", re.M),
     m_quiz),
    ("PRACTICE table",
     re.compile(r"^\|\s*PRACTICE Files\s*\|\s*(\d+)\s*\|", re.M),
     m_practice),
    ("learning phases", re.compile(r"\*\*(\d+) Learning Phases\*\*"),
     m_phases),
    ("technical modules", re.compile(r"\*\*(\d+) Technical Modules\*\*"),
     m_modules),
    ("hands-on labs (prose)",
     re.compile(r"\*\*(\d+) hands-on lab files\*\*"), m_labs),
    ("hands-on labs table",
     re.compile(r"Hands-on Labs[^|]*\|\s*(\d+)"), m_labs),
    ("tutorials", re.compile(r"\*\*(\d+) tutorials\*\*"), m_tutorials),
    ("project files", re.compile(r"\*\*(\d+) project files\*\*"),
     m_projects),
    ("cheat sheets", re.compile(r"\*\*(\d+) cheat sheets\*\*"), m_cheat),
    ("learning-resources total",
     re.compile(r"Learning Resources \(labs, tutorials, projects, "
                r"cheat sheets\)\s*\|\s*(\d+)"), m_lr_all),
    ("use-cases family",
     re.compile(r"Use Cases / Comparisons / Industry docs\s*\|\s*(\d+)"),
     m_usecases_family),
    ("configs table", re.compile(r"Config Files\s*\|\s*(\d+)"), m_configs),
    ("case-study appendix",
     re.compile(r"Case Study \(original home-lab build\)\s*\|\s*(\d+)"),
     m_case_study),
    ("footer line", re.compile(
        r"\*(\d+) Documentation Files \| (\d+) Technical Modules \| "
        r"(\d+) Learning Phases\*"),
     None),  # handled specially below
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    readme = args.root / "README.md"
    if not readme.exists():
        print("RC-00 README.md not found at the repo root")
        return 1
    text = readme.read_text(encoding="utf-8")

    checked = 0
    for label, pattern, measure in CLAIMS:
        matches = pattern.findall(text)
        if not matches:
            continue
        if label == "footer line":
            checked += 1
            claimed = (int(matches[0][0]), int(matches[0][1]),
                       int(matches[0][2]))
            actual = (m_repo_docs(args.root), m_modules(args.root),
                      m_phases(args.root))
            if claimed != actual:
                findings.append(
                    "RC-01 README footer claims %d docs / %d modules / %d "
                    "phases but disk measures %d / %d / %d"
                    % (claimed + actual))
            continue
        try:
            actual = measure(args.root)
        except (OSError, RuntimeError) as exc:
            findings.append("RC-00 could not measure %s: %s"
                            % (label, exc))
            continue
        checked += 1
        for claimed_str in matches:
            claimed = int(claimed_str)
            if claimed != actual:
                findings.append(
                    "RC-01 README claims %d for %s but disk measures %d"
                    % (claimed, label, actual))

    # per-phase documentation table: | **N** | count |
    for match in re.finditer(
            r"^\|\s*\*\*(\d)\*\*\s*\|\s*(\d+)\s*\|\s*$", text, re.M):
        phase_no, claimed = int(match.group(1)), int(match.group(2))
        if 1 <= phase_no <= m_phases(args.root):
            checked += 1
            actual = m_phase_md(phase_no)(args.root)
            if claimed != actual:
                findings.append(
                    "RC-01 README claims %d documents for phase %d but "
                    "disk measures %d" % (claimed, phase_no, actual))
    total_match = re.search(
        r"\*\*Phase total\*\*\s*\|\s*\*\*(\d+)\*\*", text)
    if total_match:
        checked += 1
        actual = m_phase_total(args.root)
        if int(total_match.group(1)) != actual:
            findings.append(
                "RC-01 README claims a phase total of %d but disk "
                "measures %d" % (int(total_match.group(1)), actual))

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print("readme_claims_check: %d findings (%d claims checked)"
          % (len(findings), checked))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
