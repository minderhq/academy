#!/usr/bin/env python3
"""quiz correct-answer position balance scan for Minder Academy.

Answers a quality question no structural gate can see: where do the
correct answers sit? A/B/C/D option order is arbitrary, so a
well-authored bank places correct answers roughly uniformly - a
learner who notices "it's usually B" gains points by guessing a
letter instead of knowing the material. Structural gates check that
four options exist (AS-10) and that keys match inline answers; the
POSITION distribution is invisible to them.

Parses the 33 module assessment/QUIZ.md banks via quiz_export's own
export_quiz (one parser, one truth) plus the 7 phase quizzes
(docs/00-META/assessment/phaseN-quiz.md) with a local parser for
their "### N." / lowercase-inline shape, and reports, per bank and
globally, the letter counts, shares, and a dep-free chi-square against
uniform. Report-only tool - exit 0 by design (same stance as
curriculum_metrics and lesson_similarity_scan): a skewed bank is a
review queue, not a failure.

FINDINGS:
    BANK-SKEW   a bank's most common letter exceeds --bank-threshold
                (default 0.45 - nine of twenty on one letter)
    GLOBAL-SKEW the corpus-wide most common letter exceeds
                --global-threshold (default 0.30 - uniform is 0.25 and
                835 mcqs make even a few points of drift significant)

The honest fix for a skewed bank is permuting that bank's option lines
and remapping its key - content untouched, presentation order only.

Usage:
    python scripts/qa/quiz_balance_scan.py [--root REPO_ROOT]
        [--bank-threshold 0.45] [--global-threshold 0.30] [--out FILE]

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quiz_export import MODULE_DIR, export_quiz  # noqa: E402

LETTERS = "ABCD"
# chi-square critical value, df=3, p=0.01 (a 4-letter uniform test)
CHI2_P01 = 11.34

# phase quizzes answer inline in lowercase under "### N." headings -
# a shape the module-bank exporter does not cover, parsed locally.
PHASE_Q = re.compile(r"^###\s+(\d+)\.\s")
PHASE_INLINE = re.compile(r"\*\*Answer:\*\*\s*([A-Da-d])\b")


def parse_phase_quiz(quiz: Path) -> dict:
    counts = {k: 0 for k in LETTERS}
    fence = False
    last = None
    for line in quiz.read_text(encoding="utf-8").split("\n"):
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = PHASE_Q.match(line)
        if m:
            last = int(m.group(1))
            continue
        m = PHASE_INLINE.search(line)
        if m and last is not None and m.group(1).upper() in counts:
            counts[m.group(1).upper()] += 1
    return counts


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def stats(counts: dict) -> dict:
    """Letter counts -> counts, shares, chi-square vs uniform."""
    n = sum(counts.values())
    if not n:
        return {"counts": counts, "n": 0,
                "shares": {k: 0.0 for k in counts}, "chi2": 0.0}
    exp = n / len(LETTERS)
    chi2 = sum((c - exp) ** 2 / exp for c in counts.values())
    return {"counts": counts, "n": n,
            "shares": {k: (round(c / n, 3) if n else 0.0)
                       for k, c in counts.items()},
            "chi2": round(chi2, 1) if n else 0.0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    parser.add_argument("--bank-threshold", type=float, default=0.45,
                        help="max-letter share above which a bank prints "
                             "as BANK-SKEW (default: %(default)s)")
    parser.add_argument("--global-threshold", type=float, default=0.30,
                        help="max-letter share above which the corpus "
                             "prints as GLOBAL-SKEW (default: %(default)s)")
    parser.add_argument("--out", type=Path, default=None,
                        help="additionally write the balance table as a "
                             "JSON snapshot to this file (same feed idiom "
                             "as quiz_export / lesson_similarity_scan --out)")
    args = parser.parse_args()
    root = args.root

    findings = []  # parse findings from export_quiz - owned by the
    # quiz integrity gate, not this dimension; collected and dropped.
    banks = []
    for mod in sorted(p for p in (root / "docs" / "phases").glob("*/*")
                      if p.is_dir() and MODULE_DIR.match(p.name)):
        quiz = mod / "assessment" / "QUIZ.md"
        if not quiz.exists():
            continue
        rel = quiz.relative_to(root).as_posix()
        _, questions = export_quiz(rel, quiz.read_text(encoding="utf-8")
                                   .split("\n"), findings)
        counts = {k: 0 for k in LETTERS}
        for q in questions:
            if q["type"] == "mcq" and q["answer"] in counts:
                counts[q["answer"]] += 1
        banks.append({"module": mod.name, "file": rel, **stats(counts)})

    for quiz in sorted((root / "docs" / "00-META" / "assessment")
                       .glob("phase*-quiz.md")):
        banks.append({"module": quiz.stem,
                      "file": quiz.relative_to(root).as_posix(),
                      **stats(parse_phase_quiz(quiz))})

    total = {k: sum(b["counts"][k] for b in banks) for k in LETTERS}
    glob = stats(total)

    print("quiz_balance_scan: %d banks, %d mcqs (correct-letter counts, "
          "chi2 vs uniform)" % (len(banks), glob["n"]))
    print("GLOBAL: %s  ->  shares %s  chi2=%.1f%s"
          % (" ".join("%s=%d" % (k, glob["counts"][k]) for k in LETTERS),
             " ".join("%s=%.1f%%" % (k, glob["shares"][k] * 100)
                      for k in LETTERS),
             glob["chi2"],
             "  [p<0.01]" if glob["chi2"] > CHI2_P01 else ""))
    for b in banks:
        top = max(LETTERS, key=lambda k: b["counts"][k])
        print("  %-22s n=%2d  %s  chi2=%5.1f%s  top=%s %.0f%%"
              % (esc(b["module"]), b["n"],
                 " ".join("%s=%2d" % (k, b["counts"][k]) for k in LETTERS),
                 b["chi2"], " [p<0.01]" if b["chi2"] > CHI2_P01 else "",
                 top, b["shares"][top] * 100))

    bank_skews = [(b, max(LETTERS, key=lambda k: b["counts"][k]))
                  for b in banks if b["n"]
                  and b["shares"][max(LETTERS, key=lambda k: b["counts"][k])]
                  > args.bank_threshold]
    global_top = max(LETTERS, key=lambda k: glob["counts"][k])
    if glob["n"] and glob["shares"][global_top] > args.global_threshold:
        findings_msg = ("GLOBAL-SKEW %.1f%% of correct answers are %s "
                        "(uniform 25%%, threshold %.0f%%) - a letter-guesser "
                        "outperforms a uniform guesser; rebalance by "
                        "permuting option lines and remapping keys"
                        % (glob["shares"][global_top] * 100, global_top,
                           args.global_threshold * 100))
        print("GLOBAL-SKEW: " + findings_msg)
        glob["finding"] = findings_msg
    else:
        print("GLOBAL-SKEW: 0 (max share %.1f%% <= %.0f%%)"
              % (glob["shares"][global_top] * 100,
                 args.global_threshold * 100))
    for b, top in bank_skews:
        print("BANK-SKEW %.3f %s (%s=%d/%d)"
              % (b["shares"][top], esc(b["module"]), top,
                 b["counts"][top], b["n"]))
    print("BANK-SKEW findings at threshold %.2f: %d"
          % (args.bank_threshold, len(bank_skews)))
    print("quiz_balance_scan: report only -> PASS")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "bank_threshold": args.bank_threshold,
            "global_threshold": args.global_threshold,
            "banks": banks,
            "global": glob,
            "findings": [{"share": b["shares"][top], "letter": top,
                          "module": b["module"]} for b, top in bank_skews],
        }
        args.out.write_text(json.dumps(snapshot, indent=1, ensure_ascii=True),
                            encoding="utf-8")
        print("wrote %s" % esc(str(args.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
