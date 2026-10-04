#!/usr/bin/env python3
"""Learning-objectives template-artifact detector for the Minder Academy corpus.

Scans lesson-class files (docs/phases/**/NNNN-*.md, guides/ included) and
flags Learning Objectives bullets that mechanically echo one of the file's
own H2/H3 headings, e.g. "- Explain GPU Architecture Overview" in a file
with a "## GPU Architecture Overview" section. Real objectives never match:
they carry lowercase function words plus substance ("Explain why IOMMU
groups must ..."), so the normalized verbatim-heading match is the signal.

  OL-01  objectives bullet = <verb> <Heading>            (verbatim heading echo)
  OL-02  objectives bullet = <verb> the <X> behind <Heading> (formula + echo)

Detected artifact verbs (corpus-derived): Explain, Apply, Configure and
operate, Diagnose and resolve, Understand, Implement, Analyze, Describe,
Explore, Identify, Install, Deploy, Evaluate, Compare, Troubleshoot,
Demonstrate, Optimize, Discuss, Practice, Review, Master, Build, Design,
Create, Learn (about), Use, Work with, Set up, Get started with.

Report mode by default (exit 0, findings + count) because the artifact
queue is drained phase by phase; pass --strict for a CI-style gate once
the queue is empty.

Usage:
    python scripts/qa/objectives_lint.py [--root REPO_ROOT] [--strict]

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LESSON_FILE = re.compile(r"^\d{4}-.*\.md$")
OBJECTIVES = re.compile(r"^(#{2,6})\s+Learning Objectives\s*$", re.IGNORECASE)
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
BULLET = re.compile(r"^-\s+(.+?)\s*$")

VERBS = [
    "configure and operate", "diagnose and resolve", "get started with",
    "learn about", "work with", "set up", "understand", "implement",
    "analyze", "describe", "explore", "identify", "install", "deploy",
    "evaluate", "compare", "troubleshoot", "demonstrate", "optimize",
    "discuss", "practice", "review", "master", "explain", "build",
    "design", "create", "learn", "apply", "use",
]
FORMULAS = [
    "the reasoning behind", "the motivation behind", "the purpose behind",
    "the design behind", "the idea behind", "the purpose of",
]


def norm(text: str) -> str:
    """Lowercase and collapse everything non-alphanumeric to single spaces."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def fence_aware(lines):
    """Yield (line, in_fence); fence = previous ``` toggles."""
    fence = False
    for line in lines:
        yield line, fence
        if line.strip().startswith("```"):
            fence = not fence


class Linter:
    def __init__(self) -> None:
        self.findings: list[str] = []
        self.files_flagged: set[str] = set()

    def report(self, rel: str, lineno: int, rule: str, bullet: str) -> None:
        self.findings.append("%s:%d: %s" % (rel, lineno, rule))
        self.files_flagged.add(rel)
        snip = bullet if len(bullet) <= 72 else bullet[:69] + "..."
        print("%s:%d: %s - %s" % (rel, lineno, rule,
              snip.encode("ascii", "backslashreplace").decode("ascii")))

    def lint_file(self, root: Path, path: Path) -> None:
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").split("\n")
        nf = [(i, l) for i, (l, f) in enumerate(fence_aware(lines)) if not f]

        headings = set()
        for _, l in nf:
            m = HEADING.match(l)
            if m:
                headings.add(norm(m.group(2)))
        if not headings:
            return

        start = next((i for i, l in nf if OBJECTIVES.match(l)), None)
        if start is None:
            return  # not OL's job to demand the section; skeleton covers that
        start_level = len(OBJECTIVES.match(nf[start][1]).group(1))
        end = next((i for i, l in nf if i > start
                    and HEADING.match(l)
                    and len(HEADING.match(l).group(1)) <= start_level), None)
        section = [(i, l) for i, l in nf if start < i < (end or len(nf))]

        for i, l in section:
            m = BULLET.match(l)
            if not m:
                continue
            b = norm(m.group(1))
            for verb in VERBS:
                if b != verb and not b.startswith(verb + " "):
                    continue
                rest = b[len(verb):].strip()
                formula = next((f for f in FORMULAS
                                if rest.startswith(f + " ")), None)
                if formula:
                    rest = rest[len(formula):].strip()
                    rule = "OL-02"
                else:
                    rule = "OL-01"
                if rest and rest in headings:
                    self.report(rel, i + 1, rule, m.group(1))
                break


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 on findings (CI gate; default report)")
    args = parser.parse_args()

    linter = Linter()
    for path in sorted((args.root / "docs" / "phases").rglob("*.md")):
        if LESSON_FILE.match(path.name):
            linter.lint_file(args.root, path)

    mode = "strict" if args.strict else "report"
    print("objectives_lint (%s): %d template-objective findings in %d files"
          % (mode, len(linter.findings), len(linter.files_flagged)))
    return 1 if (args.strict and linter.findings) else 0


if __name__ == "__main__":
    sys.exit(main())
