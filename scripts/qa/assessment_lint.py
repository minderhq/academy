#!/usr/bin/env python3
"""Assessment quality linter for the PROJECT-OMEGA curriculum corpus.

Every module directory (docs/phases/*/<NNNN>-*/) carries assessment/QUIZ.md
and assessment/PRACTICE.md. The corpus standard these files already meet:

  AS-01  assessment/QUIZ.md exists
  AS-02  QUIZ holds >= 20 questions (bold-N "**1." or "### Question N:"
         headings both count)
  AS-03  question numbers are contiguous 1..N (no gaps)
  AS-04  every question has a discoverable answer: an "## Answer Key"
         table row (any header wording, e.g. "| # | Answer |" or
         "| Question | Answer | Explanation |"), an inline
         "**Answer:** X" per question, or a self-graded "**Score:** __"
         blank (coding questions)
  AS-08  where both exist, Answer Key and inline answers agree
  AS-09  answer key is not degenerate: no single letter on >= 70% of
         the answered questions (all-B authoring lets learners ace a
         quiz by pattern-matching instead of reading). Report-mode
         while the option-shuffle queue drains; flip to hard when empty
  AS-10  a question that carries options carries exactly the four
         A-D - the platform renders options as radio buttons, so a
         3/5-option outlier or a duplicated letter breaks the shape
         (census tick-498: 655/655 mcq are four-option, uniform;
         born-at-zero)
  AS-11  every Answer Key row carries a filled explanation cell -
         the platform renders it as the per-question review text,
         and a bare | N | X | row grades without teaching
         (born tick-514 at zero: the tick-505..513 explanation
         drain left 33/33 banks explained, so hard gate from birth)
  AS-12  where a quiz carries a "Need to Review?" map, the cited
         question numbers must all exist in the bank and must cover
         every question, so no wrong answer strands a learner
         without a pointer to the lesson that teaches it. Applied
         only where the section exists; banks without a map join
         coverage as the review-map drain lands them
  AS-05  assessment/PRACTICE.md exists
  AS-06  PRACTICE holds >= 3 exercises ("## / ### Exercise N")
  AS-07  each exercise carries a solution marker (Expected Output,
         Success Criteria, Solution, **Answer)

Format-tolerant by design: richer variants (inline-answer quizzes,
self-graded coding questions, 3-column answer keys) pass as long as
coverage is complete and consistent. CI-style exit code; ASCII-safe
output for cp1254 consoles.

Usage:
    python scripts/qa/assessment_lint.py [--root REPO_ROOT]

Exit codes: 0 = no findings, 1 = findings (CI-style gate).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

DEGENERATE_RATIO = 0.7

QUESTION_BOLD = re.compile(r"^\*\*(\d+)\.")
QUESTION_H3 = re.compile(r"^###\s+Question\s+(\d+)\s*[:.]")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
EXERCISE_TITLE = re.compile(r"^Exercise\s+(\d+)\b")
AK_SECTION = re.compile(r"^##\s+Answer\s+Key\s*$", re.IGNORECASE)
REV_SECTION = re.compile(r"^##\s+Need to Review\??\s*$", re.IGNORECASE)
REV_ITEM = re.compile(r"^\s*-\s+\*\*Questions?\s+([\d,\s\-]+):\*\*")
AK_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([A-D])\b")
INLINE_ANSWER = re.compile(r"\*\*Answer:\*\*\s*([A-D])\b")
SCORE_MARKER = re.compile(r"\*\*Score:\*\*\s*__")
OPT_LINE = re.compile(r"^\s*([A-E])\) ")
ANSWER_MARKER = re.compile(
    r"expected\s+\w+|solution|success criteria|\*\*answer", re.IGNORECASE)
MODULE_DIR = re.compile(r"^\d{4}-")


def fence_aware(lines):
    """Yield (line, in_fence); a ``` line toggles for subsequent lines."""
    fence = False
    for line in lines:
        yield line, fence
        if line.strip().startswith("```"):
            fence = not fence


class Linter:
    def __init__(self) -> None:
        self.findings: list[str] = []
        self.queued: list[str] = []

    def report(self, rel: str, rule: str, detail: str) -> None:
        self.findings.append("%s: %s" % (rel, rule))
        print("%s: %s - %s" % (rel, rule,
              detail.encode("ascii", "backslashreplace").decode("ascii")))

    def report_queued(self, rel: str, rule: str, detail: str) -> None:
        self.queued.append("%s: %s" % (rel, rule))
        print("%s: %s - %s" % (rel, rule,
              detail.encode("ascii", "backslashreplace").decode("ascii")))

    def lint_quiz(self, module: str, quiz: Path) -> None:
        rel = "%s assessment/QUIZ.md" % module
        lines = quiz.read_text(encoding="utf-8").split("\n")
        nf = [(i, l) for i, (l, f) in enumerate(fence_aware(lines)) if not f]

        qnums = set()
        for _, l in nf:
            m = QUESTION_BOLD.match(l) or QUESTION_H3.match(l)
            if m:
                qnums.add(int(m.group(1)))
        if len(qnums) < 20:
            self.report(rel, "AS-02",
                        "only %d questions found (>= 20 required)" % len(qnums))
        gaps = sorted(set(range(1, max(qnums) + 1)) - qnums)
        if gaps:
            self.report(rel, "AS-03",
                        "question numbering gaps: %s" % gaps)

        # AS-10: option uniformity. Coding questions carry no option
        # lines and stay out; any question with option lines must have
        # exactly the set A-D (a duplicated letter shrinks the set, a
        # 3rd/5th option grows it past A-D or falls short).
        opts: dict = {}
        q = None
        for _, l in nf:
            m = QUESTION_BOLD.match(l) or QUESTION_H3.match(l)
            if m:
                q = int(m.group(1))
                continue
            m = OPT_LINE.match(l)
            if m and q is not None:
                opts.setdefault(q, set()).add(m.group(1))
        bad = sorted(n for n, s in opts.items() if s != set("ABCD"))
        if bad:
            self.report(rel, "AS-10",
                        "questions %s do not carry exactly the four "
                        "options A-D" % bad)

        # Answer Key table: rows | N | X | ... until the next H2.
        ak_idx = next((i for i, l in nf if AK_SECTION.match(l)), None)
        key, inline = {}, {}
        if ak_idx is not None:
            for i, l in nf:
                if i <= ak_idx:
                    continue
                h = HEADING.match(l)
                if h and len(h.group(1)) <= 2:
                    break
                m = AK_ROW.match(l)
                if m:
                    key[int(m.group(1))] = m.group(2)
                    # AS-11: the row must carry a filled explanation
                    # cell (| N | X | text |) - bare two-cell rows or
                    # an empty third cell grade without teaching.
                    cells = [c.strip()
                             for c in l.strip().strip("|").split("|")]
                    if len(cells) < 3 or not cells[2]:
                        self.report(rel, "AS-11",
                                    "question %d answer-key row has no "
                                    "explanation cell" % int(m.group(1)))

        # Inline answers / self-graded coding questions: first
        # **Answer:** X (or **Score:** __) after each question number.
        last = None
        scored = set()
        for _, l in nf:
            m = QUESTION_BOLD.match(l) or QUESTION_H3.match(l)
            if m:
                last = int(m.group(1))
                continue
            m = INLINE_ANSWER.search(l)
            if m and last is not None and last not in inline:
                inline[last] = m.group(1)
            elif SCORE_MARKER.search(l) and last is not None:
                scored.add(last)

        # A question counts as answered by an AK row, an inline letter,
        # or a self-graded score blank - all three are corpus forms.
        uncovered = sorted(qnums - (set(key) | set(inline) | scored))
        if uncovered:
            why = ("Answer Key rows, inline answers, or score blanks "
                   "missing for questions %s" % uncovered)
            if ak_idx is None:
                why += " (file has no ## Answer Key)"
            self.report(rel, "AS-04", why)
        for n in sorted(set(key) & set(inline)):
            if key[n] != inline[n]:
                self.report(rel, "AS-08",
                            "question %d: key=%s inline=%s"
                            % (n, key[n], inline[n]))

        # AS-12: review-map consistency. Where a quiz carries a
        # "Need to Review?" map, the cited question numbers must
        # (a) all exist in the bank (a stale citation points at
        # nothing) and (b) cover every question, so a wrong answer
        # never strands a learner without a lesson pointer.
        rev_idx = next((i for i, l in nf
                        if REV_SECTION.match(l)), None)
        if rev_idx is not None:
            refs: set = set()
            for i, l in nf:
                if i <= rev_idx:
                    continue
                h = HEADING.match(l)
                if h and len(h.group(1)) <= 2:
                    break
                m = REV_ITEM.match(l)
                if m:
                    for part in m.group(1).split(","):
                        part = part.strip()
                        if "-" in part:
                            a, b = part.split("-", 1)
                            refs.update(range(int(a), int(b) + 1))
                        elif part:
                            refs.add(int(part))
            stale_ref = sorted(refs - qnums)
            missing_ref = sorted(qnums - refs)
            if stale_ref:
                self.report(rel, "AS-12",
                            "review map cites nonexistent questions %s"
                            % stale_ref)
            if missing_ref:
                self.report(rel, "AS-12",
                            "questions %s missing from review map"
                            % missing_ref)

        # AS-09: degenerate answer distribution. One letter dominating
        # the key (all-B authoring) leaks the answer; queued for a
        # position-shuffle pass, report-mode until that queue drains.
        letters = [key[n] for n in sorted(set(key) & qnums)]
        letters += [inline[n] for n in sorted(set(inline) & qnums)
                    if n not in key]
        if len(letters) >= 10:
            top, count = Counter(letters).most_common(1)[0]
            if count >= DEGENERATE_RATIO * len(letters):
                self.report_queued(
                    rel, "AS-09",
                    "answer key degenerate: '%s' on %d/%d questions "
                    "(shuffle option positions)" % (top, count, len(letters)))

    def lint_practice(self, module: str, prac: Path) -> None:
        rel = "%s assessment/PRACTICE.md" % module
        lines = prac.read_text(encoding="utf-8").split("\n")
        nf = [(i, l) for i, (l, f) in enumerate(fence_aware(lines)) if not f]

        heads = [(i, len(m.group(1)), m.group(2))
                 for i, l in nf if (m := HEADING.match(l))]
        exercises = [(i, lvl, int(EXERCISE_TITLE.match(t).group(1)))
                     for i, lvl, t in heads if EXERCISE_TITLE.match(t)]
        if not exercises:
            self.report(rel, "AS-06", "no Exercise headings found")
            return
        if len(exercises) < 3:
            self.report(rel, "AS-06",
                        "only %d exercises (>= 3 required)" % len(exercises))

        for i, lvl, num in exercises:
            stop = next((h[0] for h in heads if h[0] > i and h[1] <= lvl),
                        len(lines))
            # Raw slice: solution markers may live inside code fences.
            body = "\n".join(lines[i + 1:stop])
            if not ANSWER_MARKER.search(body):
                self.report(rel, "AS-07",
                            "Exercise %d has no solution/answer marker" % num)

    def lint_module(self, root: Path, mod: Path) -> None:
        module = mod.name
        assessment = mod / "assessment"
        quiz = assessment / "QUIZ.md"
        prac = assessment / "PRACTICE.md"
        if not quiz.exists():
            self.report("%s assessment/QUIZ.md" % module, "AS-01",
                        "file missing")
        else:
            self.lint_quiz(module, quiz)
        if not prac.exists():
            self.report("%s assessment/PRACTICE.md" % module, "AS-05",
                        "file missing")
        else:
            self.lint_practice(module, prac)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    args = parser.parse_args()

    linter = Linter()
    phases = args.root / "docs" / "phases"
    for mod in sorted(p for p in phases.glob("*/*")
                      if p.is_dir() and MODULE_DIR.match(p.name)):
        linter.lint_module(args.root, mod)

    mods = [p for p in phases.glob("*/*")
            if p.is_dir() and MODULE_DIR.match(p.name)]
    print("assessment_lint: %d findings + %d queued across %d module "
          "assessments" % (len(linter.findings), len(linter.queued),
                           len(mods)))
    # Report-mode contract: queued items (AS-09 shuffle queue) do not
    # fail the gate until the queue drains, mirroring objectives_lint.
    return 1 if linter.findings else 0


if __name__ == "__main__":
    sys.exit(main())
