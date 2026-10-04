#!/usr/bin/env python3
"""Quiz-bank integrity gate for the Minder Academy corpus.

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

QI-12  ungradeable question: a parsed question that is neither mcq
       (option rows) nor coding (a **Score:** points line) - it
       lands as type "open". quiz_export only flags the empty-text
       degenerate case, so a real question that lost its option
       block or its Score line parses clean through every other
       class and renders unscoreable on the platform (nothing to
       click, nothing to self-grade). Census tick-474: 660
       questions = 655 mcq + 5 coding (2300's Q16-20), 0 open.

QI-13  unparseable Answer Key row: a line inside the Answer Key
       section shaped like a key row ("| N | X ..." or "**N. X**")
       that AK_ROW/AK_BOLD cannot parse - an E+ letter, a two-letter
       cell ("AB") or trailing junk. The [A-D]-only row regexes drop
       it silently, so unlike QI-09's orphans (rows that DO parse)
       this row vanishes from every join: no duplicate check, no
       orphan check, no key pull. Census tick-475: 0 in all 33
       banks.

QI-14  checkpoint-quiz item duplicating a bank stem: the phase
       CHECKPOINT.md files carry a 3-item **Checkpoint Quiz:** per
       module, and a verbatim item re-asks a question the module's
       own (or a sibling's) QUIZ.md bank already asks - the learner
       meets the identical stem twice in one module flow. The check
       reuses the QI-06 stem map: quiz_export never sees checkpoint
       files and QI-06 only pairs QUIZ.md against QUIZ.md. Census
       tick-476: 99 checkpoint items across 7 files vs 660 bank
       stems, 1 verbatim dup (phase7 7200's own bank Q2 "What is
       function calling?"), drained the same tick by rewording the
       checkpoint item; 0 numbering gaps (all 33 blocks 1..3).

QI-15  phase-quiz item duplicating a bank or phase-quiz stem (hard
       since tick-567): the seven phase quizzes quiz the learner
       across a whole phase's modules, so a verbatim stem re-asked
       from one of those module banks - or from a sibling phase
       quiz - means the platform serves the identical question
       twice in one learning path. Reuses the QI-06 stem map like
       QI-14, this time against the phase quizzes' "### N. title"
       headings. Census tick-567: 4 exact normalized dups, all
       phase5-quiz vs its own phase's banks ("What is QLoRA?" and
       "What is prefix tuning?" vs 5100-peft q5/q9, "What is DPO?"
       vs 5200-alignment q5, "What is federated learning?" vs
       5300-synthetic q8), drained the same tick by rewording the
       phase items to different angles (acronym expansion, best-
       description, PEFT-context forms) with answer letters and
       options untouched; phase-vs-phase and the other six phase
       quizzes born clean.

QI-16  option letters written out of A,B,C,D order with the set
       complete (hard since tick-629): AS-10 vouches the set,
       QI-04 the E+ drop and QI-11 the join, but the written
       order is read by nothing - a bank authored C ... A ...
       renders scrambled radio buttons while the key still
       joins. Fires only on a complete 4-letter A-D run so a
       broken-set question stays AS-10's class and one mutation
       fires once fleet-wide (a duplicated letter either breaks
       the set - AS-10 - or duplicates the text - QI-03).
       Census tick-629: 655/655 mcq write ABCD, born-at-zero.
       The phase surface joined tick-630: the seven phase
       quizzes carry their options in lowercase a)-d) and
       assessment_lint collects them into a letter-keyed
       dict - duplicate letters collapse at capture and the
       written order is destroyed - so this surface vouches
       nothing about the option block and the rule owns both
       sub-classes here: a complete A-D set in any other
       order (scrambled radio buttons) and a broken set
       (letter missing, duplicated, beyond D, or no option
       rows at all). Census tick-630: 180/180 questions
       write exact abcd, born-at-zero.
       QI-17 tick-631 checkpoint quiz item
       numbering - the 3-item **Checkpoint Quiz:** per
       module block must run 1..K contiguous; checkpoint_
       coverage_scan's CK-04 reads only the item COUNT
       and QI-14 reads only stems, so a gap, duplicate or
       restart inside the count was unread. Census
       tick-631: 33/33 module blocks write exact 1,2,3
       (99 items across 7 files), born-at-zero.

       QI-18 tick-642 within-bank duplicate answer-key
       explanation text - AS-11 vouches the cell's PRESENCE
       and QI-08 the duplicate ROW, but the text itself was
       read by nothing: two rows of one bank carrying the
       identical normalized explanation teach the learner the
       same sentence twice in the per-question review UI.
       Exact norm() (casefold + whitespace-collapse) inside
       one bank's Answer Key table; cross-bank repeats are
       legitimate module-specific framing (the QI-06 stem
       precedent) and a same-N pair is QI-08's class, so a
       group fires only on >= 2 distinct question numbers.
       A bare/empty cell stays AS-11's (the capture guards
       len >= 3 and truthy). Census tick-642: 33 banks /
       655 key rows parsed, 0 duplicate groups, born-at-zero.

       QI-19 tick-643 answer-key explanation restating the
       keyed option verbatim - AS-11 vouches the cell's
       presence and QI-18 the cross-question duplicate, but
       the within-question MIRROR was read by nothing: the
       review UI renders the same sentence twice for ONE
       question, the second time as the teaching text. Mirror
       normalization mnorm() adds surrounding-quote and
       trailing-punctuation stripping on top of norm(), so
       an explanation written "X." still mirrors the option
       X; an echo of a NON-keyed (distractor) option and a
       partial restatement stay out of the class (full mirror
       only). Census tick-643: 33 banks / 655 key rows,
       exactly 1 mirror (3500-multimodal Q18), 0 punct-only
       neighbors - born at 1, drained same tick.

       QI-20 tick-644 answer-key explanation restating the
       question stem verbatim - AS-11 vouches the cell's
       presence, QI-18 the cross-question duplicate, QI-19
       the keyed-option mirror and AS-17 the stem-to-keyed-
       option leak, but the explanation-to-STEM mirror was
       read by nothing: the review UI renders the question
       a second time labeled as the explanation. The same
       mnorm() full-mirror equality (quote + trailing-
       punctuation strip on top of norm) catches the
       quoted/period cousin; definition-shaped explanations
       that share words with the stem and partial
       restatements stay out of the class (full mirror
       only). Census tick-644: 33 banks / 655 key rows,
       0 mirrors against 82 partial containments -
       born-at-zero.

Report inventory (never fails the gate - the drain queues, same
contract as duplicate_heading_scan):

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
       B=40%, 4100-low-bit at 65%). Superseded tick-566: AS-09
       graduated to a hard ceil(N/4) ceiling - strictly finer than
       this 50% tripwire - over module banks and phase quizzes
       alike, so any bank passing AS-09 passes this test; kept as
       a report census only. Rebalancing needs semantic care
       because 36 questions carry positional options ("Both A and
       B" / "All of the above") that cannot move. Drained in
       tick-288/289 (34 letter swaps across 14 modules) - the
       queue is now 0.

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
       The module banks drained to a 2.4% corpus rate under this
       queue (tick-568 census); the 7 phase quizzes never measured
       until assessment_lint's AS-15 graduated this exact metric to
       a hard line over both quiz shapes (tick-568, born catching
       all seven, drained same tick) - this report remains the
       module-side trend view.

Hard gate on QI-01..06, QI-08/09 and QI-11..20 (exit 1): baseline 0
at birth (tick-284 / tick-285); QI-06 joined in tick-345 (baseline
0 since the tick-343 drain); QI-11 joined in tick-374 (born
baseline 0); QI-12 tick-474, QI-13 tick-475, QI-14 tick-476, QI-15
tick-567, QI-16
tick-629, phase surface tick-630, QI-17
tick-631, QI-18 tick-642, QI-19 tick-643, QI-20 tick-644 (all
born-at-zero; QI-19 born at its single mirror, drained same
tick). QI-10 is report inventory at birth (tick-290: 31
modules queued).

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
                         OPTION, QUESTION_BOLD, QUESTION_H3,
                         export_quiz, fence_aware)

MODULES_ROOT = Path("docs") / "phases"

BOTH_RE = re.compile(r"^\s*Both\s+([A-D])\s*(?:and|&|\+)\s*([A-D])\b",
                     re.IGNORECASE)
ALL_ABOVE_RE = re.compile(r"^\s*All\s+of\s+the\s+above\b", re.IGNORECASE)
EXTRA_OPTION_RE = re.compile(r"^\s*[-*]?\s*\*{0,2}([E-Z])[\).]\s+\S")
AK_ROWISH = re.compile(r"^\s*\|?\s*\*{0,2}(\d+)\s*[.|]\s*\*{0,2}\s*([A-Za-z]{1,2})[\).|\s*]")
SKEW_SHARE = 0.5
SKEW_MIN_MCQ = 10
LEN_BIAS_SHARE = 0.5
LEN_BIAS_MIN_MCQ = 10


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).casefold().strip()


def mnorm(s: str) -> str:
    # mirror normalization for QI-19: norm() plus surrounding-
    # quote and trailing-punctuation stripping, so an explanation
    # written as "X." or 'X' still mirrors the option X.
    s = s.strip("\"'`")
    while s and s[-1] in ".!?:;,":
        s = s[:-1].rstrip()
    return s


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
        # QI-12 ungradeable: neither mcq (option rows) nor coding
        # (a Score points line) - quiz_export only flags the
        # empty-text degenerate case, so a real question that lost
        # its option block or Score line parses clean everywhere
        # else and renders unscoreable.
        if q["type"] == "open":
            hard.append(
                f"{rel}: QI-12 question {q['n']} is ungradeable - no "
                f"option rows and no Score line, parses as neither "
                f"mcq nor coding")
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
    expl_rows: list[tuple[int, str]] = []
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
            mrow = AK_ROW.match(line)
            m = mrow or AK_BOLD.match(line)
            if m:
                key_rows.setdefault(int(m.group(1)), []).append(m.group(2))
                if mrow:
                    # QI-18 capture: the explanation cell, the same
                    # idiom as AS-11. A bare/empty cell is AS-11's
                    # class - QI-18 stays silent there.
                    cells = [c.strip()
                             for c in line.strip().strip("|").split("|")]
                    if len(cells) >= 3 and cells[2]:
                        expl_rows.append(
                            (int(m.group(1)), norm(cells[2])))
            elif AK_ROWISH.match(line):
                hard.append(
                    f"{rel}: QI-13 Answer Key row quiz_export cannot "
                    f"parse: '{line.strip()[:60]}' - the [A-D]-only row "
                    f"regexes silently drop it (E+ letter, two-letter "
                    f"cell or trailing junk), so the key row vanishes "
                    f"from every join")
    for n, letters in sorted(key_rows.items()):
        if len(letters) > 1:
            hard.append(
                f"{rel}: QI-08 duplicate Answer Key rows for question "
                f"{n}: {','.join(letters)} - last row silently wins")
        if n not in nset:
            hard.append(
                f"{rel}: QI-09 orphan Answer Key row for question "
                f"{n} - quiz has {len(nums)} questions")

    # QI-18: within-bank duplicate answer-key explanation texts.
    # Groups keyed by the normalized text; a group fires only on
    # >= 2 DISTINCT question numbers (a same-N pair is QI-08's
    # class), so one mutation fires once fleet-wide.
    expl_groups: dict[str, list[int]] = {}
    for n, t in expl_rows:
        expl_groups.setdefault(t, []).append(n)
    for t, ns in sorted(expl_groups.items()):
        uniq = sorted(set(ns))
        if len(uniq) >= 2:
            hard.append(
                f"{rel}: QI-18 answer-key explanation identical for "
                f"questions {', '.join(str(n) for n in uniq)}: "
                f"'{t[:60]}' - the per-question review UI teaches "
                f"the same sentence twice (AS-11 vouches presence, "
                f"QI-08 the duplicate row - the text itself was "
                f"read by nothing)")

    # QI-19: the explanation cell that merely restates the keyed
    # option's text. AS-11 vouches the cell's presence and QI-18
    # the cross-question duplicate; the within-question mirror
    # was read by nothing - the review UI renders the same
    # sentence twice for ONE question. mnorm() (quote +
    # trailing-punctuation strip on top of norm) catches the
    # "X." cousin; a distractor echo or a partial restatement
    # stays out of the class (full mirror only).
    keyed = {q["n"]: q for q in questions
             if q["type"] == "mcq" and q["answer"]}
    for n, t in expl_rows:
        q = keyed.get(n)
        if not q:
            continue
        o = q["options"].get(q["answer"])
        if o and mnorm(t) == mnorm(norm(o)):
            hard.append(
                f"{rel}: QI-19 answer-key explanation for question "
                f"{n} restates the keyed option verbatim: "
                f"'{t[:60]}' - the review UI teaches the same "
                f"sentence twice for one question (AS-11 vouches "
                f"presence, QI-18 the cross-question duplicate - "
                f"the mirror itself was read by nothing)")

    # QI-20: the explanation cell that merely restates the
    # question's own stem. AS-11 vouches presence, QI-18 the
    # cross-question duplicate, QI-19 the keyed-option mirror
    # and AS-17 the stem-to-keyed-option leak; the explanation-
    # to-stem mirror was read by nothing - the review UI shows
    # the question again, labeled as the explanation. Full
    # mnorm() mirror only - definition-shaped explanations
    # that share words with the stem (census tick-644: 82 of
    # 655 rows) and partial restatements stay out.
    stems = {q["n"]: q.get("text", "") for q in questions}
    for n, t in expl_rows:
        s = stems.get(n)
        if s and mnorm(t) == mnorm(norm(s)):
            hard.append(
                f"{rel}: QI-20 answer-key explanation for question "
                f"{n} restates the question stem verbatim: "
                f"'{t[:60]}' - the review UI renders the question "
                f"a second time as the explanation (AS-11 vouches "
                f"presence, QI-18 the cross-question duplicate, "
                f"QI-19 the keyed-option mirror - the stem mirror "
                f"was read by nothing)")

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

    # QI-16: option letters must be WRITTEN in A, B, C, D order
    # per question. AS-10 vouches the set, QI-04 the E+ drop and
    # QI-11 the join, but the written order is read by nothing -
    # a bank authored C ... A ... renders scrambled radio buttons
    # while the key still joins. The full-4-letter guard keeps
    # broken-set questions in AS-10's class (one mutation, one
    # finding fleet-wide).
    qn = None
    seqs: dict[int, list[str]] = {}
    for line, fence in fence_aware(lines):
        if fence:
            continue
        m = QUESTION_BOLD.match(line) or QUESTION_H3.match(line)
        if m:
            qn = int(m.group(1))
            continue
        m = OPTION.match(line)
        if m and qn is not None:
            seqs.setdefault(qn, []).append(m.group(1))
    for n, seq in sorted(seqs.items()):
        if len(seq) == 4 and sorted(set(seq)) == ["A", "B", "C", "D"] \
                and seq != ["A", "B", "C", "D"]:
            hard.append(
                f"{rel}: QI-16 question {n} options are written "
                f"{''.join(seq)}, expected ABCD - the full A-D set "
                f"renders out of letter order (scrambled radio "
                f"buttons, key still joins)")

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

    # QI-14: checkpoint-quiz items duplicating a bank stem. The
    # phase CHECKPOINT.md files carry a 3-item **Checkpoint Quiz:**
    # per module; a verbatim item re-asks a stem the bank already
    # asks, so the learner meets the identical question twice in
    # one module flow. quiz_export never sees checkpoint files and
    # QI-06 only pairs QUIZ.md against QUIZ.md - this reuses the
    # stem map QI-06 just built.
    CP_HEAD = re.compile(r"^\*\*Checkpoint Quiz:\*\*\s*$")
    CP_ITEM = re.compile(r"^\s*(\d+)[\.\)]\s+(\S.*)$")
    for cp in sorted((args.root / MODULES_ROOT).glob("phase*/CHECKPOINT.md")):
        rel = cp.relative_to(args.root).as_posix()
        raw = cp.read_text(encoding="utf-8", errors="replace")
        raw = raw.replace("\r\n", "\n").split("\n")
        in_q = False
        for line, fence in fence_aware(raw):
            if fence:
                continue
            if CP_HEAD.match(line):
                in_q = True
                continue
            if in_q:
                if (line.startswith("### ") or line.startswith("## ")
                        or line.strip() == "---" or line.startswith("**")):
                    in_q = False
                    continue
                m = CP_ITEM.match(line)
                if m:
                    stem = norm(m.group(2))
                    if stem in seen:
                        hard.append(
                            f"{rel}: QI-14 checkpoint-quiz item "
                            f"{m.group(1)} '{m.group(2)[:50]}' duplicates "
                            f"bank stem {seen[stem][0]} q{seen[stem][1]}")
        MG = re.compile(r"^###\s+Module\s+(\d{4}):")
        cur_gid = None
        in_q = False
        cnums: list[int] = []

        def close_segment():
            # QI-17: the written item-number run per
            # Checkpoint Quiz segment. CK-04 reads only the
            # item COUNT (exactly 3) and QI-14 only the stems,
            # so a gap, duplicate or restart inside the count
            # rendered the module self-test as a broken
            # sequence unread. Partition: a count != 3 stays
            # CK-04's (it exists here), the numbering inside
            # the count is ours - one mutation, one finding
            # fleet-wide. Shape-agnostic 1..K; K = 3 is the
            # corpus shape CK-04 vouches.
            if cnums and cnums != list(range(1, len(cnums) + 1)):
                hard.append(
                    f"{rel}: QI-17 module {cur_gid} checkpoint quiz "
                    f"items are numbered "
                    f"{', '.join(str(x) for x in cnums)}, "
                    f"expected 1..{len(cnums)} - the module "
                    f"self-test renders a broken sequence (item "
                    f"count vouched by CK-04)")
            cnums.clear()

        for line, fence in fence_aware(raw):
            if fence:
                continue
            mm = MG.match(line)
            if mm:
                cur_gid = mm.group(1)
            if CP_HEAD.match(line):
                if in_q:
                    close_segment()
                in_q = True
                continue
            if in_q:
                if (line.startswith("### ") or line.startswith("## ")
                        or line.strip() == "---" or line.startswith("**")):
                    in_q = False
                    close_segment()
                    continue
                m = CP_ITEM.match(line)
                if m:
                    cnums.append(int(m.group(1)))
                    stem = norm(m.group(2))
                    if stem in seen:
                        hard.append(
                            f"{rel}: QI-14 checkpoint-quiz item "
                            f"{m.group(1)} '{m.group(2)[:50]}' duplicates "
                            f"bank stem {seen[stem][0]} q{seen[stem][1]}")
        if in_q:
            close_segment()

    # QI-15: phase-quiz items duplicating a bank or phase-quiz stem.
    # The seven phase quizzes quiz across a whole phase's modules, so
    # a verbatim stem re-asked from one of those banks - or from a
    # sibling phase quiz - serves the identical question twice in one
    # learning path. Reuses the QI-06 stem map like QI-14; born
    # census tick-567 caught 4 such dups, all phase5-quiz vs its own
    # phase's banks, drained to distinct stems the same tick.
    PQ_HEAD = re.compile(r"^###\s+(\d+)\.\s+(.+?)\s*$")
    PQ_OPT = re.compile(r"^\s*([a-e])\)\s+")
    seen_phase: dict[str, tuple[str, int]] = {}
    for pq in sorted((args.root / "docs" / "00-META" / "assessment")
                     .glob("phase*-quiz.md")):
        prel = pq.relative_to(args.root).as_posix()
        prow = (pq.read_text(encoding="utf-8", errors="replace")
                .replace("\r\n", "\n").split("\n"))
        for line, fence in fence_aware(prow):
            if fence:
                continue
            m = PQ_HEAD.match(line)
            if not m:
                continue
            stem = norm(m.group(2))
            if stem in seen:
                hard.append(
                    f"{prel}: QI-15 phase-quiz item {m.group(1)} "
                    f"'{m.group(2)[:50]}' duplicates bank stem "
                    f"{seen[stem][0]} q{seen[stem][1]}")
            elif stem in seen_phase:
                hard.append(
                    f"{prel}: QI-15 phase-quiz item {m.group(1)} "
                    f"'{m.group(2)[:50]}' duplicates phase-quiz item "
                    f"{seen_phase[stem][0]} q{seen_phase[stem][1]}")
            else:
                seen_phase[stem] = (prel, int(m.group(1)))

        # QI-16 phase surface: the written option-letter run
        # per question. assessment_lint collects phase-quiz
        # options into a letter-keyed dict - duplicate letters
        # collapse at capture and the written order is
        # destroyed - so this surface vouches nothing about the
        # option block and the rule owns both sub-classes here:
        # a complete A-D set in any other order is the
        # scrambled-radio-buttons branch; a broken set (letter
        # missing, duplicated, beyond D, or no option rows at
        # all) is the broken-set branch. AS-16 compares texts
        # across distinct letters only, AS-15 reads texts and
        # AS-09 counts key letters bank-wide, so none of them
        # fires here - one mutation, one finding fleet-wide.
        pnums: set[int] = set()
        pseqs: dict[int, list[str]] = {}
        pqn = None
        for line, fence in fence_aware(prow):
            if fence:
                continue
            m = PQ_HEAD.match(line)
            if m:
                pqn = int(m.group(1))
                pnums.add(pqn)
                continue
            m = PQ_OPT.match(line)
            if m and pqn is not None:
                pseqs.setdefault(pqn, []).append(
                    m.group(1).lower())
        for n in sorted(pnums):
            seq = pseqs.get(n)
            if seq == ["a", "b", "c", "d"]:
                continue
            if seq and len(seq) == 4 \
                    and sorted(set(seq)) == ["a", "b", "c", "d"]:
                hard.append(
                    f"{prel}: QI-16 question {n} options are "
                    f"written {''.join(seq).upper()}, expected "
                    f"ABCD - the full A-D set renders out of "
                    f"letter order (scrambled radio buttons, "
                    f"key still joins)")
            elif seq:
                hard.append(
                    f"{prel}: QI-16 question {n} options are "
                    f"written {''.join(seq).upper()}, expected "
                    f"ABCD - the phase bank's four-option set "
                    f"is broken (letter missing, duplicated or "
                    f"beyond D)")
            else:
                hard.append(
                    f"{prel}: QI-16 question {n} carries no "
                    f"option rows, expected ABCD - the phase "
                    f"bank's four-option set is broken")

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
          f"option row or <2-option mcq / QI-12 ungradeable "
          f"question / QI-13 unparseable key row / QI-14 "
          f"checkpoint-quiz item duplicating a bank stem / QI-15 "
          f"phase-quiz item duplicating a bank or phase-quiz stem / "
          f"QI-16 option letters written out of ABCD order - module banks and phase quizzes; QI-17 checkpoint quiz item numbering broken inside the count; QI-18 within-bank duplicate answer-key explanation text; QI-19 answer-key explanation restating the keyed option verbatim; QI-20 answer-key explanation restating the question stem verbatim), "
          f"QI-06 {len(cross_dups)} "
          f"cross-module stem dups (hard since tick-345; drained "
          f"tick-343), QI-07 "
          f"{len(skew)} skewed answer keys (report census; "
          f"superseded tick-566 by AS-09's ceil(N/4) ceiling), "
          f"QI-10 {len(lenbias)} "
          f"length-bias modules (correct-option-longest queue; born "
          f"tick-290) across {n_modules} quizzes")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
