#!/usr/bin/env python3
"""Quiz self-claim integrity (QC-01..03, HARD) for PROJECT-OMEGA.

Every QUIZ.md makes promises to the learner about itself - how many
questions it holds, what score passes. quiz_export parses the real
bank and quiz_integrity_scan locks the bank's internal logic, but
nothing checked the PROMISES against the parsed reality: a quiz that
grows to 25 questions while its header still says "**20 questions**"
silently mis-tells every learner what they are walking into.

Born tick-473: the birth census (borrowing quiz_export's parser for
both question formats - the 32 bold-marker banks and the 2300
heading-form bank) measured all 33 QUIZ files clean: every claim of
"**20 questions**" matched a parsed 20, every pass line's arithmetic
held. The census's first pass flagged 2300 as "claimed 20, actual 0"
- that was the census's own format blindness (it only counted
"**N.**" markers, 2300 uses "### Question N:" headings), not a
content defect. This gate is the format-aware lock over the class.

QC-01  a "**N questions**" bold claim does not match the parsed
       question count
QC-02  a "**Passing score: P%** (N/M correct)" line mis-states the
       arithmetic (N != ceil(M*P/100)) or M does not match the
       parsed question count
QC-03  a "**Passing Score:** N/M (P%)" points-form line mis-states
       the arithmetic (N != ceil(M*P/100)) - M is points there
       (2300: 15x1 + 5x2 = 25), so no count cross-check

HARD GATE - exit 1 on any finding. Born-at-zero after the tick-473
census (same census -> drain -> gate cycle as checkpoint_coverage).

Run over the whole corpus:
    python scripts/qa/quiz_claim_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quiz_export import export_quiz, fence_aware  # noqa: E402

CLAIM = re.compile(r"\*\*\s*(\d+)\s+questions?\s*\*\*", re.IGNORECASE)
PASS_CORRECT = re.compile(
    r"Passing score:?\s*\**\s*(\d+)\s*%\s*\**\s*\((\d+)\s*/\s*(\d+)\s+correct\)",
    re.IGNORECASE)
PASS_POINTS = re.compile(
    r"Passing Score:?\s*\**\s*:?(\d+)\s*/\s*(\d+)\s*\((\d+)\s*%\s*\)")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_files = 0
    for path in sorted((args.root / "docs" / "phases").rglob("QUIZ.md")):
        n_files += 1
        rel = os.path.relpath(path, args.root).replace("\\", "/")
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.replace("\r\n", "\n").split("\n")
        scratch: list[str] = []
        _, qs = export_quiz(rel, lines, scratch)
        n = len(qs)
        for i, (ln, fence) in enumerate(fence_aware(lines), 1):
            if fence:
                continue
            for m in CLAIM.finditer(ln):
                if int(m.group(1)) != n:
                    findings.append("QC-01 %s:%d claims **%s questions**, "
                                    "bank holds %d"
                                    % (rel, i, m.group(1), n))
            for m in PASS_CORRECT.finditer(ln):
                pct, need, tot = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if need != math.ceil(tot * pct / 100):
                    findings.append("QC-02 %s:%d pass %d/%d (%d%%): need "
                                    "should be %d"
                                    % (rel, i, need, tot, pct,
                                       math.ceil(tot * pct / 100)))
                if tot != n:
                    findings.append("QC-02 %s:%d pass (%d/%d correct) but "
                                    "bank holds %d"
                                    % (rel, i, need, tot, n))
            for m in PASS_POINTS.finditer(ln):
                need, tot, pct = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if need != math.ceil(tot * pct / 100):
                    findings.append("QC-03 %s:%d pass %d/%d (%d%%): need "
                                    "should be %d"
                                    % (rel, i, need, tot, pct,
                                       math.ceil(tot * pct / 100)))

    for f in findings:
        print("  " + esc(f))
    print("quiz_claim_scan: %d quiz banks; %d findings - all hard "
          "(QC-01 count claim / QC-02 correct-form pass line / "
          "QC-03 points-form pass line; born tick-473 after the "
          "all-clean census)" % (n_files, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
