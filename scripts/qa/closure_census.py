#!/usr/bin/env python3
"""Closing-block census (CL-01..03) for PROJECT-OMEGA.

A lesson closes the way it opens: after the last content section
the canonical trio of H2s - a Summary-class recap, References,
Next Steps - gives the platform its recap card, its source trail
and the next node of the learning path. Scope is the
lesson_id_scan corpus - docs/phases/<phase>/<NNNN-module>/NNNN-*.md,
114 files. All three checks are fence-invisible H2 matches;
numbered variants are allowed for Summary/References (phases 1
and 4 use "N. Summary" / "10. References" style closings).

CL-01  no Summary-class closing H2 (Summary / Conclusion / Key
       Takeaways). REPORT queue - the tick-417 census found only
       14/114 lessons carrying one; the 100-site queue drains
       phase-by-phase in later ticks and the check hardens at 0.
       Exit 0 by design while the queue is live (the AS-09
       pattern: the gate itself decides via its exit code).

CL-02  no References-class closing H2 (References / Further
       Reading). HARD from birth (tick-417): the single census
       site (7301-Orchestration) was drained in the same tick to
       the sibling-7303 pattern (## References with a
       ### Related Documents subsection inside), so the baseline
       is 0 - 113/114 already carried one.

CL-03  no "Next Steps" closing H2. HARD from birth (tick-417):
       the census found 114/114 already carrying one, so the
       baseline is 0.

GATE - exits 1 on CL-02 or CL-03 findings; CL-01 is reported in
the summary line only (pass --queue to list the drain queue).

Run over the whole corpus:
    python scripts/qa/closure_census.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
PHASE_DIR = re.compile(r"^phase\d+-")
MODULE_DIR = re.compile(r"^\d{4}-")
LESSON_FILE = re.compile(r"^\d{4}-.*\.md$")
SUMMARY_RE = re.compile(r"^(?:\d+\.\s+)?(Summary|Conclusion|Key Takeaways)$")
REFS_RE = re.compile(r"^(?:\d+\.\s+)?(References|Further Reading)$")
NEXT_RE = re.compile(r"^Next Steps$")


def lesson_paths(root: Path) -> list[Path]:
    """Same corpus as lesson_id_scan: NNNN-*.md under
    docs/phases/<phase>/<NNNN-module>/."""
    phases = root / "docs" / "phases"
    out: list[Path] = []
    for path in sorted(phases.glob("*/*")):
        if not (path.is_dir() and PHASE_DIR.match(path.parent.name)
                and MODULE_DIR.match(path.name)):
            continue
        for md in sorted(path.rglob("*.md")):
            if LESSON_FILE.match(md.name):
                out.append(md)
    return out


def closings(lines: list[str]) -> tuple[bool, bool, bool]:
    """(Summary-class, References-class, Next Steps) closing H2s,
    checked outside code fences."""
    state = 0
    summary = False
    refs = False
    nxt = False
    for raw in lines:
        m = FENCE_RE.match(raw)
        if m:
            ticks, lang = len(m.group(1)), m.group(2)
            if state and not lang and ticks >= state:
                state = 0
            elif not state:
                state = ticks
            continue
        if state:
            continue
        hm = H2_RE.match(raw)
        if hm:
            t = hm.group(1).strip()
            if SUMMARY_RE.fullmatch(t):
                summary = True
            elif REFS_RE.fullmatch(t):
                refs = True
            elif NEXT_RE.fullmatch(t):
                nxt = True
    return summary, refs, nxt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--queue", action="store_true",
                        help="list the CL-01 drain queue")
    args = parser.parse_args()
    findings: list[str] = []
    queue: list[str] = []
    n_lessons = 0
    n_summary = 0
    n_refs = 0
    n_next = 0
    for path in lesson_paths(args.root):
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(args.root).as_posix()
        n_lessons += 1
        summary, refs, nxt = closings(lines)
        if summary:
            n_summary += 1
        else:
            queue.append(rel)
        if refs:
            n_refs += 1
        else:
            findings.append(
                f"{rel}: CL-02 no References-class closing H2 (the "
                f"lesson's source trail must outlive the lesson)")
        if nxt:
            n_next += 1
        else:
            findings.append(
                f"{rel}: CL-03 no 'Next Steps' closing H2 (the "
                f"learning path must point onward)")
    if args.queue:
        for rel in queue:
            print(rel.encode("ascii", "backslashreplace").decode("ascii"))
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"closure_census: lessons={n_lessons} "
          f"CL-01={n_lessons - n_summary} CL-02={n_lessons - n_refs} "
          f"CL-03={n_lessons - n_next} "
          f"(CL-01 report queue - drains phase-by-phase, hardens at "
          f"0, exit 0 by design; CL-02 hard from birth tick-417, "
          f"7301 drained same tick; CL-03 hard from birth tick-417, "
          f"114/114)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
