#!/usr/bin/env python3
"""Pacing consistency census (PC-01) for PROJECT-OMEGA.

estimated_time_census (ET-01..03) locks that every doc's Estimated
Time parses, but not that the number is TRUE. The platform's
scheduling and progress math consumes that field: a lesson labelled
"1 hour" whose real read is 8k words mislabels every learner's
calendar built on it, in both directions - overpromised hours bore
learners, underpromised hours break their schedule.

This census compares the claimed time against the lesson's real
reading load, measured with curriculum_metrics.lesson_stats (the
same CommonMark length-aware fence model structure_lint uses):

    load_minutes = words/200 wpm * 60 + code_words/100 wpm * 60

200 wpm for prose, 100 wpm for in-fence code - technical material
is skimmed slower, and code blocks are dense, not free. The ratio
load/claimed is the pacing signal:

    PC-01  ratio >= 2x (content far heavier than the label) or
           ratio <= 0.5x (label far heavier than the content)

REPORT-ONLY at birth (exit 0 always): the thresholds are the naive
2x band until the birth distribution says otherwise. Census first,
triage second, harden third - the drain-then-harden cycle every
fuzzy gate in this repo followed. Parsing of the Estimated Time
value reuses estimated_time_census's grammar exactly: the dual-mode
string's FULL-REVIEW hour is the honest scheduling number, range
values collapse to their midpoint (ET-03's canonical).

Run over the whole corpus:
    python scripts/qa/pacing_consistency_census.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from curriculum_metrics import lesson_stats  # noqa: E402

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
ET_FIELD = re.compile(r"^Estimated Time:(.*)$")

MINUTES = re.compile(r"^(\d+(?:\.\d+)?) minutes?$")
HOURS = re.compile(r"^(\d+(?:\.\d+)?) hours?$")
DUAL = re.compile(r"^\d+(?:\.\d+)? (?:minutes?|hours?) \(quick review\) - "
                  r"(\d+(?:\.\d+)?) hours \(full review\)$")
RANGE = re.compile(r"^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?) hours$")

WPM_PROSE = 200.0
WPM_CODE = 100.0
FLAG_LO = 0.5   # label at least 2x the real load
FLAG_HI = 2.0   # real load at least 2x the label


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def claimed_hours(val: str) -> float | None:
    m = MINUTES.match(val)
    if m:
        return float(m.group(1)) / 60.0
    m = HOURS.match(val)
    if m:
        return float(m.group(1))
    m = DUAL.match(val)
    if m:
        return float(m.group(1))
    m = RANGE.match(val)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2.0
    return None


def load_minutes(stats: dict) -> float:
    return stats["words"] / WPM_PROSE * 60.0 \
        + stats["code_words"] / WPM_CODE * 60.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    n_parsed = 0
    n_unparsed = 0
    rows: list[tuple[float, str, str, float, float]] = []
    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        if not lines or not FM_OPEN.match(lines[0]):
            continue
        val = None
        for i in range(1, min(len(lines), 40)):
            if FM_CLOSE.match(lines[i]):
                for raw in lines[1:i]:
                    m = ET_FIELD.match(raw)
                    if m:
                        val = m.group(1).strip()
                        break
                break
        if val is None:
            continue
        rel = path.relative_to(args.root).as_posix()
        hours = claimed_hours(val)
        if hours is None or hours <= 0:
            n_unparsed += 1
            print("  skipped, unparseable value (%s): %s"
                  % (esc(val), esc(rel)))
            continue
        stats = lesson_stats(lines)
        lm = load_minutes(stats)
        ratio = lm / (hours * 60.0)
        n_parsed += 1
        rows.append((ratio, rel, val, hours, lm))

    ratios = sorted(r[0] for r in rows)
    flagged = [r for r in rows if r[0] <= FLAG_LO or r[0] >= FLAG_HI]
    if ratios:
        n = len(ratios)
        median = ratios[n // 2] if n % 2 else (ratios[n // 2 - 1]
                                               + ratios[n // 2]) / 2.0
        print("pacing_consistency_census: %d docs measured, median "
              "load/claimed ratio %.2f (p10 %.2f, p90 %.2f)"
              % (n, median, ratios[max(0, n // 10)],
                 ratios[min(n - 1, n * 9 // 10)]))
    if n_unparsed:
        print("  skipped, unparseable Estimated Time (%d docs)" % n_unparsed)
    for ratio, rel, val, hours, lm in sorted(flagged):
        direction = "heavier" if ratio >= FLAG_HI else "lighter"
        print("  PC-01 %s than label (ratio %.2f): %s "
              "(claimed '%s', load %.0f min)"
              % (direction, ratio, esc(rel), esc(val), lm))
    print("pacing_consistency_census: %d PC-01 flags in %d docs "
          "- report-only census" % (len(flagged), n_parsed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
