#!/usr/bin/env python3
"""TOC completeness (TC-01 hard, TC-02 report) for PROJECT-OMEGA.

A doc's Table of Contents becomes the platform's in-doc nav pane: a
real content section absent from the TOC is invisible in the doc's
own navigation, however prominent on the page. anchor_check proves
that listed anchors resolve; this gate proves nothing real is
unlisted.

TC-01 (hard): every H2 heading outside frontmatter and code fences,
except the closing trio (Summary, References, Next Steps - the house
style keeps the trio's navigation tail out of the TOC), must appear
as a TOC bullet (link text matched, whitespace-normalized) in the
doc's "## Table of Contents" section. Scope: TOC-carrying LESSON
docs under docs/phases (numbered .md outside guides/ and assessment/
whose name is not a README/PREREQUISITES/CHECKPOINT) - the 93-lesson
TOC discipline is platform-critical nav, so it is a hard gate.

TC-02 (report): the same completeness rule over TOC-carrying docs of
OTHER genres (phase READMEs, volumes/, industry/, guides/). Their
TOC conventions are younger and the standard (which tail sections a
genre owes its readers) is not yet settled per genre; findings print
without failing the run so the drift stays visible until each genre
adopts a standard.

Birth census (2026-09-30): a NAIVE census (no fence tracking) found
2 "missing" H2s in 2301 - both turned out to be literal text inside
a ````python example block, i.e. not headings at all; anchor_check's
fence tracking was right. The fence-aware census measured 0 real
findings across all TOC-carrying lessons: TC-01 born at zero
(KW-03). The genre report listed 45 rows (volumes 16, phase READMEs
19, industry 8, guides 2); the 19 phase-README rows (Prerequisites
x5 on phases 3-7, Assessment x7, Related Topics x7) were drained the
same tick, leaving 26 visible until genre standards land.

Run over the whole corpus:
    python scripts/qa/toc_coverage_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(```|~~~)")
FM = re.compile(r"^---\s*$")
HEADING = re.compile(r"^## (.+?)\s*$")
TOC_HEAD = re.compile(r"^## Table of Contents\s*$", re.I)
TOC_BULLET = re.compile(r"^- \[([^\]]+)\]\(#")
NUMBERED = re.compile(r"^\d")
SKIP = {"README.md", "PREREQUISITES.md", "CHECKPOINT.md"}
CLOSING = {"summary", "references", "next steps"}


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def collect(text: str):
    """Yield (is_toc_head, is_h2, line, inside_fence) line facts."""
    in_f = False
    in_fm = text.startswith("---")
    fm_n = 0
    facts = []
    for ln in text.split("\n"):
        if in_fm:
            if FM.match(ln):
                fm_n += 1
                in_fm = fm_n != 2
            facts.append((False, False, "", in_f))
            continue
        if FENCE.match(ln):
            in_f = not in_f
            facts.append((False, False, "", True))
            continue
        facts.append((bool(TOC_HEAD.match(ln)), not in_f and bool(
            HEADING.match(ln)), ln, in_f))
    return facts


def missing_h2s(facts: list[tuple], path: Path, root: Path):
    """Return the H2s (normalized) absent from the doc's TOC."""
    toc_idx = [i for i, (t, _, _, f) in enumerate(facts)
               if t and not f]
    if not toc_idx:
        return None  # docs without a TOC are not this gate's subject
    toc_end = next((i for i in range(toc_idx[0] + 1, len(facts))
                    if facts[i][1] and not facts[i][3]), len(facts))
    listed = {re.sub(r"\s+", " ", m.group(1)).strip().lower()
              for m in (TOC_BULLET.match(facts[i][2])
                        for i in range(toc_idx[0] + 1, toc_end))
              if m}
    out = []
    for i in range(toc_end, len(facts)):
        _, is_h2, ln, in_f = facts[i]
        if not is_h2 or in_f:
            continue
        h = re.sub(r"\s+", " ", HEADING.match(ln).group(1)).strip()
        if h.lower() not in CLOSING and h.lower() not in listed:
            out.append(h)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    n_lessons = 0
    n_h2 = 0
    hard: list[str] = []
    report: list[str] = []

    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        facts = collect(text)
        miss = missing_h2s(facts, path, args.root)
        if miss is None:
            continue
        rel = path.relative_to(args.root).as_posix()
        is_lesson = ("docs/phases/" in rel and NUMBERED.match(path.name)
                     and "guides/" not in rel and "assessment/" not in rel
                     and path.name not in SKIP)
        if is_lesson:
            n_lessons += 1
            n_h2 += len(miss)
            hard += ("TC-01 H2 %r not in TOC of %s" % (h, rel)
                     for h in miss)
        else:
            report += ("TC-02 H2 %r not in TOC of %s" % (h, rel)
                       for h in miss)

    print("toc_coverage_check: %d TOC-carrying lessons, %d content H2 "
          "unlisted" % (n_lessons, n_h2))
    for f in hard:
        print("  " + esc(f))
    print("toc_coverage_check: %d TC-01 findings - hard gate, born at "
          "zero (fence-aware census 2026-09-30)" % len(hard))
    for f in report:
        print("  TC-02 " + esc(f[len("TC-01 "):]))
    print("toc_coverage_check: %d TC-02 genre rows - report only, "
          "until each genre adopts a TOC standard" % len(report))
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
