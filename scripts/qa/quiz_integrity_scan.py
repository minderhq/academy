#!/usr/bin/env python3
"""Quiz-bank integrity gate for the PROJECT-OMEGA corpus.

Runs on top of quiz_export's parser (borrowed, not reinvented) and
locks the content-level classes that a structural parse cannot see:

QI-01  self-referential positional option: "Both A and B" sitting AT
       position B (or "All of the above" at A) - the option's own
       letter is inside its reference, so the question is logically
       unsatisfiable for a test-taker. Born from the tick-284 census:
       2 real bugs (1300-kubernetes Q16, 3200-embeddings Q15), both
       fixed by re-pointing the reference to the two true options.

QI-02  duplicate question stem within one module (casefold, whitespace
       normalized). A module asking the same question twice double-
       counts it in the bank. Census: 0 in all 33 modules.

QI-03  duplicate option text within one question - two options with
       the same content make the key ambiguous. Census: 0 in 655 mcq.

QI-04  option letter beyond A-D ("E. ..."): quiz_export's OPTION
       regex silently drops it, so the rendered question has an
       option the bank never saw. Census: 0.

QI-05  question numbering gap: quiz_export flags duplicate numbers
       but not missing ones - a bank that jumps 1..5,7 mis-joins
       against its own Answer Key rows. Census: all 33 quizzes are
       contiguous 1..N.

QI-08  duplicate Answer Key rows for one question ("| 3 | A |" and
       "| 3 | C |" in the same table): quiz_export's key dict
       overwrites, so the last row silently wins and a learner sees
       whichever row sorts last. Born from the tick-285 census: 0
       across all 33 modules.

QI-09  orphan Answer Key row - a key row whose question number does
       not exist ("| 11 | B |" in a 10-question quiz). quiz_export's
       join is one-directional (questions pull from the key, key rows
       are never checked back), so nothing else sees this class.
       Census: 0 across all 33 modules.

QI-11  join asymmetry between the Answer Key and the option rows: the
       key letter quiz_export's join pulled in has no matching option
       row in the question (stale key, mis-written or parser-dropped
       option), or an mcq parsed fewer than two options - either way
       the rendered question is unanswerable. quiz_export trusts both
       sides of the join and QI-04 only sees the raw-text E+ case.
       Born from the tick-374 census (660 questions: 0 duplicate
       stems, 0 MCQ defects) as a lock.

Report inventory (never fails the gate - the drain queues, same
contract as duplicate_heading_scan / AS-09):

QI-06  cross-module duplicate stem (casefold, whitespace
       normalized): the same question label reused across two
       modules - a platform sampling across modules quizzes the
       learner twice on one stem. Started as a report census (6,
       all short concept labels like "KV cache stores" reused
       across modules that tested their own framing with
       different options), drained in tick-343 (6 stem rewords
       across 5 modules, meaning and answer keys preserved) and
       promoted to HARD in tick-345 - the house census->drain->
       gate pattern (BB-02, TL-01): a new collision now fails
       the build instead of queueing.
QI-07  skewed answer keys per module (max letter >= 50% of answered
       mcq, or any of A-D absent; census: 14 modules, corpus-wide
       B=40%, 4100-low-bit at 65% - just under assessment_lint's
       70% AS-09 tripwire, so the finer baseline is what actually
       sees the drift). This is the option-shuffle queue: rebalancing
       needs semantic care because 36 questions carry positional
       options ("Both A and B" / "All of the above") that cannot
       move. Drained in tick-288/289 (34 letter swaps across 14
       modules) - the queue is now 0.

QI-10  answer-length bias per module (report queue): the correct
       option is the longest-or-tied option (words AND chars) in
       >=50% of the module's mcq questions. A learner who always
       picks the longest option wins ~70% of this bank (chance
       ~25%), so the assessment measures length, not knowledge.
       Born from the tick-290 census: 69.8% corpus-wide (457/655),
       mean correct option 4.3 words vs 2.7 for distractors, 31/33
       modules at >=50%. Unlike the QI-07 letter shuffle there is
       no safe mechanical fix - draining needs per-module content
       passes that make distractors parallel in form and length.

Hard gate on QI-01..06, QI-08/09 and QI-11 (exit 1): baseline 0 at
birth (tick-284 / tick-285); QI-06 joined in tick-345 (baseline 0
since the tick-343 drain); QI-11 joined in tick-374 (born baseline
0). QI-10 is report inventory at birth (tick-290: 31 modules
queued).

Run over the whole corpus:
    python scripts/qa/quiz_integrity_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quiz_export import (MODULE_DIR, AK_BOLD, AK_HEADING, AK_ROW, HEADING,  # noqa: E402
                         export_quiz, fence_aware)

MODULES_ROOT = Path("docs") / "phases"

BOTH_RE = re.compile(r"^\s*Both\s+([A-D])\s*(?:and|&|\+)\s*([A-D])\b",
                     re.IGNORECASE)
ALL_ABOVE_RE = re.compile(r"^\s*All\s+of\s+the\s+above\b", re.IGNORECASE)
EXTRA_OPTION_RE = re.compile(r"^\s*[-*]?\s*\*{0,2}([E-Z])[\).]\s+\S")
SKEW_SHARE = 0.5
SKEW_MIN_MCQ = 10
LEN_BIAS_SHARE = 0.5
LEN_BIAS_MIN_MCQ = 10


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).casefold().strip()


def scan_module(rel: str, lines: list[str],
                hard: list[str], cross: list[tuple[str, int, str]],
                skew: list[str], lenbias: list[str]) -> None:
    _, questions = export_quiz(rel, lines, [])
    stems: dict[str, int] = {}
    for q in questions:
        stem = norm(q["text"])
        if stem:
            if stem in stems:
                hard.append(
                    f"{rel}: QI-02 duplicate stem in module: question "
                    f"{q['n']} repeats question {stems[stem]} '{q['text'][:50]}'")
            else:
                stems[stem] = q["n"]
                cross.append((rel, q["n"], stem))
        if q["type"] != "mcq":
            continue
        seen_opts: set[str] = set()
        for letter, text in sorted(q["options"].items()):
            t = norm(text)
            if t in seen_opts:
                hard.append(
                    f"{rel}: QI-03 duplicate option text in question "
                    f"{q['n']}: '{text[:50]}'")
            seen_opts.add(t)
            m = BOTH_RE.match(text)
            if m and letter in (m.group(1).upper(), m.group(2).upper()):
                hard.append(
                    f"{rel}: QI-01 self-referential option in question "
                    f"{q['n']}: option {letter} says 'Both {m.group(1)} "
                    f"and {m.group(2)}' - includes itself")
            elif ALL_ABOVE_RE.match(text) and letter == "A":
                hard.append(
                    f"{rel}: QI-01 self-referential option in question "
                    f"{q['n']}: option A says 'All of the above' - "
                    f"includes itself")
        # QI-11 join asymmetry: quiz_export trusts both sides of its
        # key join - the key letter must point at a parsed option and
        # an mcq needs two options to discriminate at all. QI-04 only
        # sees the raw-text E+ drop; a stale key letter or a one-
        # option question passes everything else and renders
        # unanswerable.
        ans = (q.get("answer") or "").strip().upper()
        if ans and ans not in q["options"]:
            hard.append(
                f"{rel}: QI-11 answer key {ans} has no option row in "
                f"question {q['n']} (parsed options "
                f"{','.join(sorted(q['options']))}) - unanswerable")
        if len(q["options"]) < 2:
            hard.append(
                f"{rel}: QI-11 question {q['n']} parsed only "
                f"{len(q['options'])} option(s) - an mcq needs at "
                f"least two to discriminate")
    nums = [q["n"] for q in questions]
    nset = set(nums)
    if nums != list(range(1, len(nums) + 1)):
        hard.append(
            f"{rel}: QI-05 question numbering is not contiguous 1..N "
            f"(got {nums[:8]}{'...' if len(nums) > 8 else ''})")

    # QI-08/09 need the Answer Key join in reverse: quiz_export only
    # pulls the key INTO questions and never checks key rows back.
    key_rows: dict[int, list[str]] = {}
    in_ak = False
    for line, fence in fence_aware(lines):
        if fence:
            continue
        if AK_HEADING.match(line):
            in_ak = True
            continue
        if in_ak:
            if HEADING.match(line):
                in_ak = False
                continue
            m = AK_ROW.match(line) or AK_BOLD.match(line)
            if m:
                key_rows.setdefault(int(m.group(1)), []).append(m.group(2))
    for n, letters in sorted(key_rows.items()):
        if len(letters) > 1:
            hard.append(
                f"{rel}: QI-08 duplicate Answer Key rows for question "
                f"{n}: {','.join(letters)} - last row silently wins")
        if n not in nset:
            hard.append(
                f"{rel}: QI-09 orphan Answer Key row for question "
                f"{n} - quiz has {len(nums)} questions")

    # QI-04 needs a raw fence-aware pass: the parser never sees E+.
    for line, fence in fence_aware(lines):
        if fence:
            continue
        m = EXTRA_OPTION_RE.match(line)
        if m:
            hard.append(
                f"{rel}: QI-04 option beyond A-D: '{line.strip()[:40]}' "
                f"- quiz_export silently drops it")
            break

    answered = [q["answer"] for q in questions
                if q["type"] == "mcq" and q["answer"]]
    if len(answered) >= SKEW_MIN_MCQ:
        c = Counter(answered)
        top, count = c.most_common(1)[0]
        missing = sorted(set("ABCD") - set(c))
        if count >= SKEW_SHARE * len(answered) or missing:
            skew.append(
                f"{rel.split('/')[3]}: '{top}' on {count}/{len(answered)}"
                + (f", missing {''.join(missing)}" if missing else ""))

    # QI-10: the pick-the-longest tell. A learner who always picks the
    # longest option wins ~70% of this bank (chance ~25%), so report
    # the modules where length gives the answer away. No mechanical
    # fix: rebalancing means rewriting option text (per-module content
    # passes), which is why this is a report queue, not a hard gate.
    mcq = [q for q in questions
           if q["type"] == "mcq" and q["answer"]
           and len(q["options"]) >= 4]
    if len(mcq) >= LEN_BIAS_MIN_MCQ:
        longest = 0
        for q in mcq:
            a = q["answer"]
            ow = [len(q["options"][k].split())
                  for k in q["options"] if k != a]
            oc = [len(q["options"][k]) for k in q["options"] if k != a]
            if (len(q["options"][a].split()) >= max(ow)
                    and len(q["options"][a]) >= max(oc)):
                longest += 1
        if longest >= LEN_BIAS_SHARE * len(mcq):
            lenbias.append(
                f"{rel.split('/')[3]}: {longest}/{len(mcq)} questions "
                f"have the correct option as longest-or-tied")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    hard: list[str] = []
    stems: list[tuple[str, int, str]] = []
    skew: list[str] = []
    lenbias: list[str] = []
    n_modules = 0
    for mod in sorted(p for p in (args.root / MODULES_ROOT).glob("*/*")
                      if p.is_dir() and MODULE_DIR.match(p.name)):
        quiz = mod / "assessment" / "QUIZ.md"
        if not quiz.exists():
            continue
        rel = quiz.relative_to(args.root).as_posix()
        n_modules += 1
        scan_module(rel, quiz.read_text(encoding="utf-8").split("\n"),
                    hard, stems, skew, lenbias)

    seen: dict[str, tuple[str, int]] = {}
    cross_dups: list[str] = []
    for rel, n, stem in stems:
        if stem in seen:
            cross_dups.append(
                f"{rel.split('/')[3]} q{n} '{stem[:40]}' duplicates "
                f"{seen[stem][0].split('/')[3]} q{seen[stem][1]}")
        else:
            seen[stem] = (rel, n)

    for c in cross_dups:
        hard.append("QI-06 cross-module stem dup: " + c)
    for f in hard:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    for s in skew:
        print(("QI-07 (shuffle queue) " + s)
              .encode("ascii", "backslashreplace").decode("ascii"))
    for lb in lenbias:
        print(("QI-10 (length-bias queue) " + lb)
              .encode("ascii", "backslashreplace").decode("ascii"))
    print(f"quiz_integrity_scan: {len(hard)} hard findings "
          f"(QI-01 self-referential option / QI-02 in-module duplicate "
          f"stem / QI-03 duplicate option text / QI-04 option beyond "
          f"A-D / QI-05 numbering gap / QI-06 cross-module stem dup "
          f"/ QI-08 duplicate Answer Key row "
          f"/ QI-09 orphan Answer Key row / QI-11 key letter with no "
          f"option row or <2-option mcq), QI-06 {len(cross_dups)} "
          f"cross-module stem dups (hard since tick-345; drained "
          f"tick-343), QI-07 "
          f"{len(skew)} skewed answer keys (option-shuffle queue; "
          f"refines AS-09's 70% tripwire), QI-10 {len(lenbias)} "
          f"length-bias modules (correct-option-longest queue; born "
          f"tick-290) across {n_modules} quizzes")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
