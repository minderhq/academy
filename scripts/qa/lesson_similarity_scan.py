#!/usr/bin/env python3
"""lesson clone-similarity scan for the PROJECT-OMEGA curriculum.

Answers a quality question the structural gates cannot see: do any two
lessons say the same thing? Copy-paste lineage is invisible to link,
structure and census gates - a lesson forked from a sibling keeps
passing every check while the learner reads near-identical pages and
the fixes land in only one copy (drifted clones). This scan shingles
every lesson (5-word sequences over normalized text, frontmatter
stripped) and Jaccard-compares all pairs; only the top of the
distribution is printed so the shape is auditable by eye.

Report-only tool - exit 0 by design (same stance as curriculum_metrics
and fm_staleness): a high-similarity pair is a review queue, not a
failure. Pairs at or above --threshold print as CLONE-PAIR findings;
the full top-N table always prints so a threshold recalibration has
data. 4-digit lesson files only (assessments/labs are separate docs
whose PRACTICE/SOLUTION overlap is by design).

Usage:
    python scripts/qa/lesson_similarity_scan.py [--root REPO_ROOT]
        [--threshold 0.35] [--top 15] [--out FILE]

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from itertools import combinations
from pathlib import Path

# Same classification as quality_report / curriculum_metrics.
LESSON_FILE = re.compile(r"^(\d{4})-[^/]*\.md$")

FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
WORD = re.compile(r"[a-z0-9_]+")
SHINGLE = 5


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def shingles(text: str) -> frozenset:
    words = WORD.findall(FRONTMATTER.sub("", text).lower())
    if len(words) < SHINGLE:
        return frozenset({tuple(words)}) if words else frozenset()
    return frozenset(tuple(words[i:i + SHINGLE]) for i in range(len(words) - SHINGLE + 1))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    parser.add_argument("--threshold", type=float, default=0.35,
                        help="Jaccard similarity at or above which a pair "
                             "prints as a CLONE-PAIR review finding "
                             "(default: %(default)s)")
    parser.add_argument("--top", type=int, default=15,
                        help="how many highest-similarity pairs to always "
                             "print regardless of threshold (default: %(default)s)")
    parser.add_argument("--out", type=Path, default=None,
                        help="additionally write the pair table as a JSON "
                             "snapshot to this file (same feed idiom as "
                             "manifest_export and quiz_export --out)")
    args = parser.parse_args()
    root = args.root

    lessons = sorted(p for p in (root / "docs" / "phases").rglob("*.md")
                     if LESSON_FILE.match(p.name))
    sets: dict[str, frozenset] = {}
    for path in lessons:
        rel = path.relative_to(root).as_posix()
        sets[rel] = shingles(path.read_text(encoding="utf-8"))

    pairs = []
    for a, b in combinations(sorted(sets), 2):
        sa, sb = sets[a], sets[b]
        union = len(sa | sb)
        if not union:
            continue
        pairs.append((len(sa & sb) / union, a, b))
    pairs.sort(reverse=True)

    findings = [(s, a, b) for s, a, b in pairs if s >= args.threshold]
    print("lesson_similarity_scan: %d lessons, %d pairs compared "
          "(5-word shingles, Jaccard)" % (len(sets), len(pairs)))
    print("top %d pairs:" % min(args.top, len(pairs)))
    for s, a, b in pairs[:args.top]:
        print("  %.3f  %s  <->  %s" % (s, esc(a), esc(b)))
    if findings:
        print("CLONE-PAIR findings at threshold %.2f: %d"
              % (args.threshold, len(findings)))
        for s, a, b in findings:
            print("CLONE-PAIR %.3f  %s  <->  %s" % (s, esc(a), esc(b)))
    else:
        print("CLONE-PAIR findings at threshold %.2f: 0" % args.threshold)
    print("lesson_similarity_scan: report only -> PASS")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "threshold": args.threshold,
            "lessons": len(sets),
            "pairs": [{"similarity": round(s, 4), "a": a, "b": b}
                      for s, a, b in pairs[:50]],
            "findings": [{"similarity": round(s, 4), "a": a, "b": b}
                         for s, a, b in findings],
        }
        args.out.write_text(json.dumps(snapshot, indent=1, ensure_ascii=True),
                            encoding="utf-8")
        print("wrote %s" % esc(str(args.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
