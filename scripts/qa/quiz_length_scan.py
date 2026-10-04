#!/usr/bin/env python3
"""quiz correct-answer length-balance scan for Minder Academy.

Answers a quality question no structural gate can see: how long is the
correct answer next to its distractors? Option length is arbitrary, so
a well-authored bank does not let the correct answer sit systematically
at the length extreme - a learner who notices "the right answer is
always the longest one" (or always the shortest) games the bank by
reading option shape instead of knowing the material. Structural gates
check that four options exist (AS-10), that keys match inline answers,
and that two options never share text (tick-621); the LENGTH
distribution is invisible to all of them. Sibling of
quiz_balance_scan: that tool owns the position axis (letters), this
one owns the length axis - the two are orthogonal by construction
(permuting option lines changes every balance verdict and no length
verdict; rebalancing option text changes length verdicts and no
letter).

Parses the 33 module assessment/QUIZ.md banks via quiz_export's own
export_quiz (one parser, one truth) plus the 7 phase quizzes
(docs/00-META/assessment/phaseN-quiz.md) with a local parser for their
"### N." / lowercase "a) text" / inline-answer shape, and reports, per
bank and globally, the share of MCQs whose correct answer is strictly
the longest option and the share whose correct answer is strictly the
shortest. Report-only tool - exit 0 by design (same stance as
quiz_balance_scan, curriculum_metrics and lesson_similarity_scan): a
skewed bank is a review queue, not a failure.

FINDINGS:
    BANK-LONG-SKEW   a bank's correct-is-strictly-longest share exceeds
                     --bank-threshold (default 0.40 - nine of twenty
                     where the long option is always right; a
                     longest-guesser scores 0.40 against the 0.25
                     uniform floor)
    BANK-SHORT-SKEW  the mirror - correct-is-strictly-shortest share
                     exceeds the same threshold, the "pick the short
                     one" tell
    GLOBAL-LONG-SKEW / GLOBAL-SHORT-SKEW  the corpus-wide shares above
                     --global-threshold (default 0.30)

The honest fix for a skewed bank is rebalancing option TEXT - tighten
the correct answer or give distractors plausible elaborations - with
letters, keys, counts and meaning untouched; position order belongs to
quiz_balance_scan and is not touched here.

Usage:
    python scripts/qa/quiz_length_scan.py [--root REPO_ROOT]
        [--bank-threshold 0.40] [--global-threshold 0.30] [--out FILE]

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

# phase quizzes answer inline in lowercase under "### N." headings with
# lowercase "a) text" option rows - a shape the module-bank exporter
# does not cover, parsed locally (texts needed here, not just letters).
PHASE_Q = re.compile(r"^###\s+(\d+)\.\s")
PHASE_OPT = re.compile(r"^\s*([A-Da-d])\)\s+(.+?)\s*$")
PHASE_INLINE = re.compile(r"\*\*Answer:\*\*\s*([A-Da-d])\b")


def parse_phase_quiz(quiz: Path) -> list:
    """Phase-quiz option texts + keys -> [{'options': {A..D}, 'answer': L}]."""
    qs = []
    fence = False
    cur: dict | None = None
    for line in quiz.read_text(encoding="utf-8").split("\n"):
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if PHASE_Q.match(line):
            if cur and len(cur["options"]) == 4 and cur["answer"]:
                qs.append(cur)
            cur = {"options": {}, "answer": None}
            continue
        if cur is None:
            continue
        m = PHASE_OPT.match(line)
        if m:
            cur["options"][m.group(1).upper()] = m.group(2).strip()
            continue
        m = PHASE_INLINE.search(line)
        if m:
            cur["answer"] = m.group(1).upper()
    if cur and len(cur["options"]) == 4 and cur["answer"]:
        qs.append(cur)
    return qs


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def stats(questions: list) -> dict:
    """MCQ records -> n, longest/shortest counts and shares."""
    n = long = short = 0
    for q in questions:
        if q["answer"] not in q["options"] or len(q["options"]) != 4:
            continue
        n += 1
        corr = len(q["options"][q["answer"]])
        dist = [len(t) for k, t in q["options"].items()
                if k != q["answer"]]
        if not dist:
            continue
        if corr > max(dist):
            long += 1
        elif corr < min(dist):
            short += 1
    return {"n": n, "long": long, "short": short,
            "long_share": (round(long / n, 3) if n else 0.0),
            "short_share": (round(short / n, 3) if n else 0.0)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    parser.add_argument("--bank-threshold", type=float, default=0.40,
                        help="long/short share above which a bank prints "
                             "as BANK-*-SKEW (default: %(default)s)")
    parser.add_argument("--global-threshold", type=float, default=0.30,
                        help="long/short share above which the corpus "
                             "prints as GLOBAL-*-SKEW "
                             "(default: %(default)s)")
    parser.add_argument("--out", type=Path, default=None,
                        help="additionally write the length table as a "
                             "JSON snapshot to this file (same feed idiom "
                             "as quiz_balance_scan --out)")
    args = parser.parse_args()
    root = args.root

    # parse findings from export_quiz are owned by the quiz integrity
    # gate, not this dimension; collected and dropped.
    findings: list = []
    banks = []
    phase_dir = root / "docs" / "phases"
    for mod in sorted(p for p in (phase_dir.glob("*/*") if phase_dir.exists()
                                  else []) if p.is_dir()
                      and MODULE_DIR.match(p.name)):
        quiz = mod / "assessment" / "QUIZ.md"
        if not quiz.exists():
            continue
        rel = quiz.relative_to(root).as_posix()
        _, questions = export_quiz(rel, quiz.read_text(encoding="utf-8")
                                   .split("\n"), findings)
        banks.append({"module": mod.name, "file": rel,
                      **stats(questions)})

    meta_dir = root / "docs" / "00-META" / "assessment"
    for quiz in sorted(meta_dir.glob("phase*-quiz.md")
                       if meta_dir.exists() else []):
        banks.append({"module": quiz.stem,
                      "file": quiz.relative_to(root).as_posix(),
                      **stats(parse_phase_quiz(quiz))})

    tot = {"n": sum(b["n"] for b in banks),
           "long": sum(b["long"] for b in banks),
           "short": sum(b["short"] for b in banks)}
    glob = {"long_share": (round(tot["long"] / tot["n"], 3) if tot["n"]
                           else 0.0),
            "short_share": (round(tot["short"] / tot["n"], 3) if tot["n"]
                            else 0.0)}

    print("quiz_length_scan: %d banks, %d mcqs (correct-answer length "
          "vs distractor lengths)" % (len(banks), tot["n"]))
    print("GLOBAL: long=%.1f%% short=%.1f%% of %d mcqs%s"
          % (glob["long_share"] * 100, glob["short_share"] * 100,
             tot["n"],
             "  (uniform floor 25%)" if tot["n"] else "  (empty corpus)"))
    for b in banks:
        print("  %-22s n=%2d  long=%2d (%.0f%%)  short=%2d (%.0f%%)"
              % (esc(b["module"]), b["n"], b["long"],
                 b["long_share"] * 100, b["short"],
                 b["short_share"] * 100))

    bank_longs = [b for b in banks if b["n"]
                  and b["long_share"] > args.bank_threshold]
    bank_shorts = [b for b in banks if b["n"]
                   and b["short_share"] > args.bank_threshold]
    for b in bank_longs:
        print("BANK-LONG-SKEW %.3f %s (%d/%d) - the longest option is "
              "right too often; a longest-guesser beats a uniform guesser"
              % (b["long_share"], esc(b["module"]), b["long"], b["n"]))
    for b in bank_shorts:
        print("BANK-SHORT-SKEW %.3f %s (%d/%d) - the shortest option is "
              "right too often; a shortest-guesser beats a uniform guesser"
              % (b["short_share"], esc(b["module"]), b["short"], b["n"]))
    print("BANK-LONG findings at threshold %.2f: %d"
          % (args.bank_threshold, len(bank_longs)))
    print("BANK-SHORT findings at threshold %.2f: %d"
          % (args.bank_threshold, len(bank_shorts)))
    gl, gs = "0", "0"
    if tot["n"] and glob["long_share"] > args.global_threshold:
        gl = "%.3f" % glob["long_share"]
        print("GLOBAL-LONG-SKEW %.1f%% of correct answers are strictly "
              "the longest option (threshold %.0f%%)"
              % (glob["long_share"] * 100, args.global_threshold * 100))
    else:
        print("GLOBAL-LONG-SKEW: 0 (max share %.1f%% <= %.0f%%)"
              % (glob["long_share"] * 100, args.global_threshold * 100))
    if tot["n"] and glob["short_share"] > args.global_threshold:
        gs = "%.3f" % glob["short_share"]
        print("GLOBAL-SHORT-SKEW %.1f%% of correct answers are strictly "
              "the shortest option (threshold %.0f%%)"
              % (glob["short_share"] * 100, args.global_threshold * 100))
    else:
        print("GLOBAL-SHORT-SKEW: 0 (max share %.1f%% <= %.0f%%)"
              % (glob["short_share"] * 100, args.global_threshold * 100))
    print("quiz_length_scan: report only -> PASS")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "bank_threshold": args.bank_threshold,
            "global_threshold": args.global_threshold,
            "banks": banks,
            "global": {**tot, **glob},
            "findings": [{"kind": "BANK-LONG-SKEW", "module": b["module"],
                          "share": b["long_share"], "n": b["long"],
                          "of": b["n"]} for b in bank_longs]
                        + [{"kind": "BANK-SHORT-SKEW", "module": b["module"],
                            "share": b["short_share"], "n": b["short"],
                            "of": b["n"]} for b in bank_shorts],
            "global_findings": [k for k, v in
                                (("GLOBAL-LONG-SKEW", gl),
                                 ("GLOBAL-SHORT-SKEW", gs)) if v != "0"],
        }
        args.out.write_text(json.dumps(snapshot, indent=1,
                                       ensure_ascii=True),
                            encoding="utf-8")
        print("wrote %s" % esc(str(args.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
