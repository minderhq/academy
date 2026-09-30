#!/usr/bin/env python3
"""Module README navigation coverage (NV-01/NV-02) for PROJECT-OMEGA.

linkcheck proves that links which exist resolve; it says nothing about
docs that no README links at all. A learner opening a module page sees
the README's links - a lesson absent from them is invisible on the
platform, however good its content.

NV-01 (hard): every learner-facing doc in a module - numbered lessons
at the module root, guides/*.md, assessment/*.md - must be linked from
its module README (the README-bearing directory it lives in). The
predicate is filename-link reachability: the doc's path, resolved from
the README's directory, must appear among the README's relative .md
link targets.

NV-02 (report): phase-level extras - CHECKPOINT.md and
PREREQUISITES.md at phase roots, where no module README applies.
Their standard is pending; the inventory stays visible.

Birth census (2026-09-30) measured 45 in-scope orphans across 17
module READMEs (30 lessons described in prose but never linked,
6 lessons with no mention at all, 9 assessments missing from the
Assessment section) - all drained the same tick by linkifying the
described headers, appending the unmentioned lessons under
Module Contents, and inserting the house-style Location lines.
Zero from then on: HARD gate, born at zero.

Run over the whole corpus:
    python scripts/qa/nav_coverage_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_SUB = "docs/phases"
SKIP = {"README.md", "PREREQUISITES.md", "CHECKPOINT.md"}
NUMBERED = re.compile(r"^\d")
LINK_RE = re.compile(r"\]\(([^)#]+?\.md)\)")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def linked_targets(mod: Path, text: str) -> set[Path]:
    out = set()
    for l in LINK_RE.findall(text):
        try:
            out.add((mod / l).resolve())
        except OSError:
            continue
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    phases = args.root / ROOT_SUB
    n_modules = 0
    n_docs = 0
    findings: list[str] = []
    report: list[str] = []

    readme_dirs = sorted({p.parent for p in phases.rglob("*.md")
                          if (p.parent / "README.md").exists()})
    for mod in readme_dirs:
        try:
            text = (mod / "README.md").read_text(encoding="utf-8",
                                                 errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        targets = linked_targets(mod, text)
        kids = list(mod.glob("*.md"))
        is_module = (any(NUMBERED.match(k.name) for k in kids)
                     or (mod / "guides").exists()
                     or (mod / "assessment").exists())
        if is_module:
            n_modules += 1
            subjects = [k for k in kids
                        if k.name not in SKIP and NUMBERED.match(k.name)]
            for sub in ("guides", "assessment"):
                d = mod / sub
                if d.exists():
                    subjects.extend(d.glob("*.md"))
            for k in subjects:
                n_docs += 1
                if k.resolve() not in targets:
                    rel = k.relative_to(args.root).as_posix()
                    findings.append("NV-01 %s not linked from %s"
                                    % (rel, (mod / "README.md")
                                       .relative_to(args.root).as_posix()))
        else:
            for name in ("CHECKPOINT.md", "PREREQUISITES.md"):
                extra = mod / name
                if extra.exists() and extra.resolve() not in targets:
                    rel = extra.relative_to(args.root).as_posix()
                    report.append("NV-02 phase-level %s not linked from its "
                                  "phase README (pending standard)" % rel)

    print("nav_coverage_check: %d modules, %d learner-facing docs checked"
          % (n_modules, n_docs))
    for f in findings:
        print("  " + esc(f))
    for r in report:
        print("  " + esc(r))
    print("nav_coverage_check: %d NV-01 findings (hard, born at zero) - "
          "%d NV-02 report rows (phase-level, pending standard)"
          % (len(findings), len(report)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
