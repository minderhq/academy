#!/usr/bin/env python3
"""Tags coverage check (TG-01 hard, TG-02/03 report) for PROJECT-OMEGA.

tag_vocabulary_census (TV-01..03) locks WHAT tags say; this gate
locks WHO carries them. The platform's tag filter and
related-content navigation only see docs that carry Tags - a lesson
without tags is invisible to both.

Birth census (2026-09-30, after the 6-lesson drain in 133e6a2):

TG-01  a numbered in-phase lesson doc outside guides/ with no Tags
       field. HARD. 102/102 carry Tags now; the 6 born missing
       (5103, 5203, 5204, 6203, 7302, 7403 - all 5-key-minimum
       docs) were drained same day with their modules' own sibling
       tag pools.

TG-02  guides/ genre consistency, REPORT-ONLY: 9 of 21 guides
       carry Tags, 12 do not. A real standardization decision
       (tag all guides or none) is pending; the inventory keeps
       it visible until it is made.

TG-03  module/phase meta docs, REPORT-ONLY: 10 meta docs carry
       Tags - all in the phase2-foundations revamp zone (README +
       PREREQUISITES x4 modules + 2300 assessment PRACTICE/QUIZ) -
       while 126 other meta docs do not. Same pending decision.

HARD on TG-01 only - exit 1 if any lesson lacks Tags; TG-02/03
counts are printed either way.

Run over the whole corpus:
    python scripts/qa/tags_coverage_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
TG_FIELD = re.compile(r"^Tags:")
LESSON_NUM = re.compile(r"^\d{4}-")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def has_tags(lines: list[str]) -> bool | None:
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            return any(TG_FIELD.match(r) for r in lines[1:i])
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    n_lesson = n_lesson_tagged = 0
    findings: list[str] = []
    n_guides = n_guides_tagged = 0
    n_meta = n_meta_tagged = 0
    for path in sorted((args.root / "docs" / "phases").rglob("*.md")):
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        tagged = has_tags(lines)
        if tagged is None:
            continue
        rel = path.relative_to(args.root).as_posix()
        in_guides = "guides" in path.parts
        if LESSON_NUM.match(path.name) and not in_guides:
            n_lesson += 1
            if tagged:
                n_lesson_tagged += 1
            else:
                findings.append("TG-01 lesson without Tags: %s" % rel)
        elif in_guides:
            n_guides += 1
            n_guides_tagged += 1 if tagged else 0
        else:
            n_meta += 1
            n_meta_tagged += 1 if tagged else 0

    print("tags_coverage_check: %d/%d numbered lessons carry Tags"
          % (n_lesson_tagged, n_lesson))
    print("  TG-02 guides genre (report): %d/%d tagged"
          % (n_guides_tagged, n_guides))
    print("  TG-03 meta docs (report): %d/%d tagged "
          "(phase2 revamp zone holds the tagged ones)"
          % (n_meta_tagged, n_meta))
    for f in findings:
        print("  " + esc(f))
    print("tags_coverage_check: %d TG-01 findings - hard on lessons; "
          "guides/meta consistency is a pending standard (TG-02/03)"
          % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
