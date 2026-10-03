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


def export_quiz(rel, lines, findings):
    fm = parse_frontmatter(lines)

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
                key[int(m.group(1))] = m.group(2)

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
            qs[last]["options"][m.group(1)] = m.group(2).strip()
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
