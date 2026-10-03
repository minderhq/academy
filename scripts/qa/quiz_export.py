#!/usr/bin/env python3
"""Quiz JSON exporter for the PROJECT-OMEGA curriculum corpus.

Reads every module's assessment/QUIZ.md (docs/phases/*/<NNNN>-*/) and
exports a machine-readable quiz bank - the content-as-data layer for the
future platform. Doubles as a structural gate: a quiz that cannot be
parsed into complete question records is a defect, so the run exits 1
on any finding (same CI-style contract as assessment_lint).

Understood corpus forms (format-tolerant):
  - bold-numbered questions "**1. ...?**" answered by an "## Answer Key"
    table (2-col "| # | Answer |" or 3-col "| Question | Answer | ... |",
    or bold rows "**1. B**")
  - "### Question N: Title" headings answered inline via "**Answer:** X"
  - self-graded coding questions ("**Score:** __/2", answer=null)
  - option rows / key letters outside the A-D grammar are findings, not
    silent drops (tick-616)
  - the Instructions "N questions" claim must match the parsed count,
    and every key row must have its question (tick-617)
  - the passing-score parenthetical must match the parsed count, carry
    a paired percentage, and the percent must be the fraction's
    arithmetic (tick-618)
  - a duplicated option row or duplicated key row is a finding, not a
    silent overwrite of the earlier entry (tick-619)
  - question numbers must run 1..N contiguously - a numbering gap is a
    finding even when the count still matches (tick-620)

Usage:
    python scripts/qa/quiz_export.py [--root REPO_ROOT] [--out FILE]

Exit codes: 0 = all quizzes exported clean, 1 = findings.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

QUESTION_BOLD = re.compile(r"^\*\*(\d+)\.\s*(.*?)\s*:?\*\*\s*$")
QUESTION_BOLD_TRAILER = re.compile(r"^\*\*(\d+)\.\s*\*\*\s+(.+?)\s*$")
QUESTION_H3 = re.compile(r"^###\s+Question\s+(\d+)\s*[:.]\s*(.*?)\s*$")
OPTION = re.compile(r"^[-*]?\s*\*{0,2}([A-D])[\).]\s+(.+?)\*{0,2}\s*$")
INLINE_ANSWER = re.compile(r"\*\*Answer:\*\*\s*([A-D])\b", re.IGNORECASE)
SCORE = re.compile(r"\*\*Score:\*\*\s*__\s*/\s*(\d+)")
AK_HEADING = re.compile(r"^#{1,3}\s+Answer\s+Key\b", re.IGNORECASE)
AK_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([A-D])\b")
AK_BOLD = re.compile(r"^\*\*(\d+)\.\s*\**\s*([A-D])\s*\**\s*$")
AK_ROW_BEYOND = re.compile(r"^\|\s*(\d+)\s*\|\s*([E-Z])\b")
AK_BOLD_BEYOND = re.compile(r"^\*\*(\d+)\.\s*\**\s*([E-Z])\s*\**\s*$")
OPT_BEYOND = re.compile(r"^\s*[-*]?\s*\*{0,2}([E-Z])[\).]")
CLAIM = re.compile(r"(\d+)\s+questions?\b")
PCT_PAREN = re.compile(r"\((\d+)/(\d+)\s+correct\)")
PCT_PAIR = re.compile(r"(\d+)%\s*\*{0,2}\s*\((\d+)/(\d+)\s+correct\)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FM_LINE = re.compile(r"^([A-Za-z][A-Za-z ]*):\s*(.*?)\s*$")
MODULE_DIR = re.compile(r"^\d{4}-")


def fence_aware(lines):
    """Yield (line, in_fence); a ``` line toggles for subsequent lines."""
    fence = False
    for line in lines:
        yield line, fence
        if line.strip().startswith("```"):
            fence = not fence


def parse_frontmatter(lines):
    fm = {}
    if not lines or lines[0].strip() != "---":
        return fm
    for l in lines[1:]:
        if l.strip() == "---":
            break
        m = FM_LINE.match(l)
        if m:
            fm[m.group(1)] = m.group(2).strip(" \"'")
    return fm


def capture_claim(lines):
    """The Instructions region's "N questions" claim; None when absent.

    tick-617: the claim is platform metadata - tracked as its own pass
    so the key and question passes keep their single purposes.
    """
    in_instr = False
    for l, fence in fence_aware(lines):
        if fence:
            continue
        if HEADING.match(l):
            in_instr = "instruction" in l.lower()
            continue
        if in_instr:
            m = CLAIM.search(l)
            if m:
                return int(m.group(1))
    return None


def capture_pcts(lines):
    """Passing-score parentheticals "(X/Y correct)" with their paired
    percent; pct is None when the percent pairing is absent.

    tick-618: the parenthetical is the platform's passing contract -
    captured as its own pass beside capture_claim.
    """
    out = []
    for l, fence in fence_aware(lines):
        if fence:
            continue
        for m in PCT_PAREN.finditer(l):
            mp = PCT_PAIR.search(l)
            out.append((int(mp.group(1)) if mp else None,
                        int(m.group(1)), int(m.group(2))))
    return out


def export_quiz(rel, lines, findings):
    fm = parse_frontmatter(lines)
    claim = capture_claim(lines)
    pcts = capture_pcts(lines)

    key = {}
    in_ak = False
    for l, fence in fence_aware(lines):
        if fence:
            continue
        if AK_HEADING.match(l):
            in_ak = True
            continue
        if in_ak:
            if HEADING.match(l):
                in_ak = False
                continue
            m = AK_ROW.match(l) or AK_BOLD.match(l)
            if m:
                if int(m.group(1)) in key:
                    # tick-619: the key dict assignment silently
                    # overwrites the earlier row - a duplicated key
                    # row kept the table complete-looking while the
                    # first answer was lost, and when the duplicate
                    # letter differs the served answer silently
                    # flips (born census: 0 across 33 modules).
                    findings.append("%s: answer key row %d duplicated "
                                    "(letter %s overwrites %s)"
                                    % (rel, int(m.group(1)), m.group(2),
                                       key[int(m.group(1))]))
                key[int(m.group(1))] = m.group(2)
            m = AK_ROW_BEYOND.match(l) or AK_BOLD_BEYOND.match(l)
            if m:
                # tick-616: AK_ROW/AK_BOLD capture A-D only, so a key row
                # whose letter fell outside the grammar dropped silently -
                # an inline-answered question kept a complete-looking
                # record with the key entry lost (born census: 0 across
                # 660 questions; without an inline answer the missing-
                # answer clause fires instead, this is the silent path).
                findings.append("%s: answer key row %d letter %s outside "
                                "A-D (dropped from the key)"
                                % (rel, int(m.group(1)), m.group(2)))

    qs = {}
    order = []
    last = None
    for l, fence in fence_aware(lines):
        m = (QUESTION_BOLD.match(l) or QUESTION_BOLD_TRAILER.match(l)
             or QUESTION_H3.match(l))
        if m and not fence:
            n = int(m.group(1))
            text = (m.group(2) or "").strip()
            if n in qs:
                findings.append("%s: duplicate question number %d" % (rel, n))
            qs[n] = {"n": n, "text": text, "type": "open",
                     "options": {}, "answer": None, "points": None}
            if n not in order:
                order.append(n)
            last = n
            continue
        if fence:
            continue
        m = OPTION.match(l)
        if m and last is not None:
            if m.group(1) in qs[last]["options"]:
                # tick-619: the options dict assignment silently
                # overwrites the earlier row - a duplicated option
                # letter kept the record complete-looking (A-D full,
                # answer intact) while the first option's text was
                # lost (born census: 0 across 660 questions).
                findings.append("%s: question %d duplicate option row %s "
                                "(the earlier text is overwritten)"
                                % (rel, last, m.group(1)))
            qs[last]["options"][m.group(1)] = m.group(2).strip()
            continue
        m = OPT_BEYOND.match(l)
        if m and last is not None:
            # tick-616: OPTION captures A-D only, so an option row whose
            # letter fell outside the grammar dropped silently while the
            # record stayed complete-looking (A-D full, answer intact) -
            # the same rendered-complete shape as the blank-stem class
            # (born census: 0 across 660 questions; a bare A-D letter row
            # is the missing-options clause's, not this one's).
            findings.append("%s: question %d option row %s outside the "
                            "A-D grammar (dropped from the record)"
                            % (rel, last, m.group(1)))
            continue
        m = INLINE_ANSWER.search(l)
        if m and last is not None and qs[last]["answer"] is None:
            qs[last]["answer"] = m.group(1)
            continue
        m = SCORE.search(l)
        if m and last is not None:
            qs[last]["points"] = int(m.group(1))

    for n in order:
        q = qs[n]
        if q["answer"] is None and n in key:
            q["answer"] = key[n]
        if n in key and q["answer"] != key[n]:
            findings.append("%s: question %d answer conflict key=%s inline=%s"
                            % (rel, n, key[n], q["answer"]))
        if q["options"]:
            q["type"] = "mcq"
            if q["answer"] is None:
                findings.append("%s: question %d has options but no answer"
                                % (rel, n))
            missing = sorted(set("ABCD") - set(q["options"]))
            if missing:
                findings.append("%s: question %d missing options %s"
                                % (rel, n, "".join(missing)))
        elif q["points"] is not None:
            q["type"] = "coding"
        if not q["text"]:
            # tick-615: the stem check sat in the open-type elif chain,
            # so an mcq or coding question whose stem line lost its
            # text ("**5.**" with options or a Score line intact)
            # parsed clean into a rendered-blank record - the blank-
            # stem class now fires for every type, one clause owning
            # the whole class (born census: 0 across 660 questions;
            # the gradeable-but-open cousin is QI-12's clause, this is
            # the blank stem itself).
            findings.append("%s: question %d has no stem text (blank "
                            "stem parses clean otherwise)"
                            % (rel, n))
    if claim is not None and claim != len(order):
        # tick-617: the Instructions "N questions" claim is platform
        # metadata - a count drifted from the parsed bank lies to the
        # learner while the bank loads fine (born census: 0 mismatches
        # across 33 modules; no claim, no comparison - 2300's points-
        # based form carries none).
        findings.append("%s: instructions claim %d questions but %d "
                        "parsed" % (rel, claim, len(order)))
    for n in sorted(key):
        if n not in qs:
            # tick-617: a key row whose question no longer exists is a
            # dangling entry, the dual of the missing-answer class -
            # the per-question loop never visits key-only numbers, so
            # nothing else fires (born census: 0 across 33 modules;
            # 2300's self-graded coding questions carry no key rows,
            # the reverse direction, untouched here).
            findings.append("%s: answer key row %d has no matching "
                            "question" % (rel, n))
    nums = sorted(order)
    if nums != list(range(1, len(nums) + 1)):
        # tick-620: a numbering gap means a question was renumbered or
        # dropped - the count-claim and parenthetical clauses stay
        # silent when the total still matches, so the numbering itself
        # is the contract (born census: 0 gaps across 33 modules; the
        # feed's question records must be 1..N).
        bad = next(n for n, w in zip(nums, range(1, len(nums) + 1))
                   if n != w)
        findings.append("%s: question numbering not 1..%d contiguous "
                        "(first mismatch %d)" % (rel, len(nums), bad))
    for pct, x, y in pcts:
        if y != len(order):
            # tick-618: the passing-score parenthetical is the count a
            # learner is graded against - a denominator drifted from
            # the parsed bank lies while the bank loads fine (born
            # census: 0 across the 32 modules carrying the form; 2300's
            # points-based form carries none).
            findings.append("%s: passing-score parenthetical %d/%d but %d "
                            "questions parsed" % (rel, x, y, len(order)))
        if pct is None:
            # tick-618: the parenthetical pairs with an "N%" prefix in
            # every canonical form - a bare parenthetical means the
            # percent contract is malformed (born census: 0 across the
            # 32 modules carrying the form).
            findings.append("%s: passing-score parenthetical %d/%d has no "
                            "paired percentage" % (rel, x, y))
        elif round(x / y * 100) != pct:
            # tick-618: the stated percent must be the fraction's
            # arithmetic (born census: 0 across the 32 modules).
            findings.append("%s: passing score %d%% but %d/%d computes "
                            "%d%%" % (rel, pct, x, y, round(x / y * 100)))
    return fm, [qs[n] for n in sorted(order)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    parser.add_argument("--out", type=Path, default=None,
                        help="write combined JSON bank to this file")
    args = parser.parse_args()

    findings = []
    modules = []
    phases = args.root / "docs" / "phases"
    for mod in sorted(p for p in phases.glob("*/*")
                      if p.is_dir() and MODULE_DIR.match(p.name)):
        quiz = mod / "assessment" / "QUIZ.md"
        if not quiz.exists():
            findings.append("%s: no assessment/QUIZ.md" % mod.name)
            continue
        rel = quiz.relative_to(args.root).as_posix()
        lines = quiz.read_text(encoding="utf-8").split("\n")
        fm, questions = export_quiz(rel, lines, findings)
        if not questions:
            findings.append("%s: zero questions parsed" % mod.name)
        counts = {"mcq": 0, "coding": 0, "open": 0}
        for q in questions:
            counts[q["type"]] += 1
        print("%s: %d questions (%d mcq, %d coding)"
              % (mod.name, len(questions), counts["mcq"], counts["coding"]))
        modules.append({
            "module": mod.name,
            "doc_id": fm.get("Document ID", ""),
            "title": fm.get("Title", ""),
            "file": rel,
            "question_count": len(questions),
            "counts": counts,
            "questions": questions,
        })

    totals = {t: sum(m["counts"][t] for m in modules)
              for t in ("mcq", "coding", "open")}
    print("quiz_export: %d modules, %d questions (%d mcq, %d coding, "
          "%d open), %d findings"
          % (len(modules), sum(m["question_count"] for m in modules),
             totals["mcq"], totals["coding"], totals["open"], len(findings)))
    for f in findings:
        print("FINDING " + f.encode("ascii", "backslashreplace").decode())

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        bank = {"generated": date.today().isoformat(), "tool": "quiz_export.py",
                "totals": totals, "modules": modules}
        args.out.write_text(json.dumps(bank, indent=2, ensure_ascii=True),
                            encoding="utf-8")
        print("wrote %s" % args.out)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
