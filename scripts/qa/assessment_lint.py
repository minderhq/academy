#!/usr/bin/env python3
"""Assessment quality linter for the PROJECT-OMEGA curriculum corpus.

Every module directory (docs/phases/*/<NNNN>-*/) carries assessment/QUIZ.md
and assessment/PRACTICE.md. The corpus standard these files already meet
(the seven phase quizzes in docs/00-META/assessment/ are linted under
the same AS-04/AS-08/AS-09 standards in their own "### N." shape):

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
  AS-09  answer-key letter balance: no single letter exceeds
         ceil(N/4) of the bank's answered questions (all-D authoring
         lets learners ace a quiz by pattern-matching instead of
         reading). Hard over the 33 module banks and the 7 phase
         quizzes alike; graduated tick-566 from the queued 70%
         tripwire - the birth census caught all seven phase banks
         skewed (phase 2 answering D on 70% of its questions,
         phase 5 B on 56.7%), the option positions were permuted
         and the keys remapped to quarter shares before the
         ceiling locked
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
  AS-13  the MASTER-INDEX "Phase Practice Files" / "Phase Quiz
         Files" tables are claims a learner plans from: each row's
         exercise/question count must equal the real count in the
         linked phase-level file (practice rows count "Exercise N"
         headings exactly like AS-06 but only outside the
         "Appendix: Complete Reference Implementations" section -
         phases 6-7 carry one whose per-exercise reference builds
         are solutions, not new exercises, and any other H1/H2 ends
         the appendix; quiz rows count the numbered "### N."
         question headings this phase-quiz fleet uses; joined
         tick-562 - the birth census found the quiz column 7/7
         true but the exercise column drifted on 5 of 7 phases, MI
         promising 42 exercises against a disk of 34, and the
         column was drained to disk truth before the lock
         tightened)

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

# AS-13: the MASTER-INDEX phase tables. The MI file lives in
# docs/00-META, so its "assessment/phaseN-*.md" links resolve from
# there; the quiz fleet in docs/00-META/assessment numbers its
# questions as "### N." headings (a different shape from the module
# banks' "**N." / "### Question N:" forms AS-02 already parses).
PHASE_PRACTICE_ROW = re.compile(
    r"^\|\s*\*\*(\d+)\*\*\s*\|\s*\[[^\]]+\]\(([^)]+)\)\s*\|"
    r"\s*(\d+)\s+exercises\s*\|\s*$")
PHASE_QUIZ_ROW = re.compile(
    r"^\|\s*\*\*(\d+)\*\*\s*\|\s*\[[^\]]+\]\(([^)]+)\)\s*\|"
    r"\s*(\d+)\s+questions\s*\|\s*$")
PHASE_Q = re.compile(r"^###\s+(\d+)\.\s")
# phase quizzes answer inline in lowercase and summarize in an Answer
# Key block ("1\. c, 2. b, ...", escaped dots); both tolerate a-d.
PHASE_INLINE = re.compile(r"\*\*Answer:\*\*\s*([A-Da-d])\b")
PHASE_KEY_PAIR = re.compile(r"(?<!\d)(\d+)\\?\. ([A-Da-d])\b")


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

    def report(self, rel: str, rule: str, detail: str) -> None:
        self.findings.append("%s: %s" % (rel, rule))
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

        # AS-09: answer-key letter balance. One letter dominating the
        # key (all-B authoring) leaks the answer; the corpus convention
        # is quarter shares, so no letter may exceed ceil(N/4). Hard
        # since tick-566, when the seven phase banks skewed under the
        # old queued 70% tripwire drained to quarter shares.
        self.check_balance(rel, key, qnums, inline)

    def check_balance(self, rel: str, key: dict, qnums: set,
                      inline: dict) -> None:
        """AS-09 shared by both quiz shapes: no letter above
        ceil(N/4) of the bank's answered questions."""
        letters = [key[n] for n in sorted(set(key) & qnums)]
        letters += [inline[n].upper() for n in sorted(set(inline) & qnums)
                    if n not in key]
        if not letters:
            return
        top, count = Counter(letters).most_common(1)[0]
        ceiling = (len(letters) + 3) // 4
        if count > ceiling:
            self.report(rel, "AS-09",
                        "answer key unbalanced: '%s' on %d/%d questions "
                        "(ceiling %d - permute option positions and "
                        "remap the key)" % (top, count, len(letters),
                                            ceiling))

    def lint_phase_quiz(self, root: Path, quiz: Path) -> None:
        """The seven phase quizzes (docs/00-META/assessment/phaseN-quiz.md)
        under the same AS-04/AS-08/AS-09 standards as the module banks,
        in their own shape: "### N." headings, lowercase a)-d) options,
        an inline answer per question plus an Answer Key block that
        mirrors them."""
        rel = quiz.relative_to(root).as_posix()
        lines = quiz.read_text(encoding="utf-8").split("\n")
        nf = [(i, l) for i, (l, f) in enumerate(fence_aware(lines)) if not f]

        qnums: set = set()
        last = None
        inline: dict = {}
        for _, l in nf:
            m = PHASE_Q.match(l)
            if m:
                qnums.add(int(m.group(1)))
                last = int(m.group(1))
                continue
            m = PHASE_INLINE.search(l)
            if m and last is not None and last not in inline:
                inline[last] = m.group(1).upper()
        if qnums != set(range(1, len(qnums) + 1)):
            self.report(rel, "AS-03",
                        "question numbering not contiguous 1..%d"
                        % len(qnums))
        uncovered = sorted(qnums - set(inline))
        if uncovered:
            self.report(rel, "AS-04",
                        "questions %s carry no inline answer" % uncovered)

        # The Answer Key block mirrors the inline answers: where it
        # exists it must cite only real questions and agree with them.
        key: dict = {}
        ak_idx = next((i for i, l in nf if AK_SECTION.match(l)), None)
        if ak_idx is None:
            self.report(rel, "AS-04", "no ## Answer Key section")
        else:
            body = "\n".join(l for i, l in nf if i > ak_idx)
            key = {int(n): L.upper()
                   for n, L in PHASE_KEY_PAIR.findall(body)}
            stale = sorted(set(key) - qnums)
            if stale:
                self.report(rel, "AS-08",
                            "answer-key block cites nonexistent "
                            "questions %s" % stale)
            for n in sorted(set(key) & set(inline)):
                if key[n] != inline[n]:
                    self.report(rel, "AS-08",
                                "question %d: key=%s inline=%s"
                                % (n, key[n], inline[n]))

        self.check_balance(rel, key, qnums, inline)

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

    def lint_index_tables(self, root: Path) -> int:
        """AS-13: MI phase-practice/quiz count columns vs disk truth.

        Returns the number of claims actually checked (for the
        summary line). Every phase 1..7 must have a row; each row's
        count must equal the linked file's real count.
        """
        mi = root / "docs" / "00-META" / "MASTER-INDEX.md"
        rel = "MASTER-INDEX phase tables"
        lines = mi.read_text(encoding="utf-8").split("\n")
        nf = [(i, l) for i, (l, f) in enumerate(fence_aware(lines))
              if not f]
        n_claims = 0
        tables = (
            ("practice", PHASE_PRACTICE_ROW, "exercises",
             "phase%d-practice.md"),
            ("quiz", PHASE_QUIZ_ROW, "questions", "phase%d-quiz.md"),
        )
        for kind, row_re, count_word, fname in tables:
            idx = next((i for i, l in nf if re.match(
                r"^###\s+Phase %s Files" % kind.title(), l)), None)
            if idx is None:
                self.report(rel, "AS-13",
                            "no 'Phase %s Files' section" % kind.title())
                continue
            stop = next((i for i, l in nf if i > idx
                         and re.match(r"^###\s", l)), len(lines))
            rows: dict = {}
            for i, l in nf:
                if idx < i < stop:
                    m = row_re.match(l)
                    if m:
                        rows[int(m.group(1))] = (m.group(2),
                                                 int(m.group(3)))
            for phase in range(1, 8):
                if phase not in rows:
                    self.report(rel, "AS-13",
                                "no row for phase %d in the Phase %s "
                                "Files table" % (phase, kind.title()))
                    continue
                link, claimed = rows[phase]
                path = (mi.parent / link).resolve()
                if not path.exists():
                    self.report(rel, "AS-13",
                                "row for phase %d links %s which does "
                                "not exist" % (phase, link))
                    continue
                plines = path.read_text(encoding="utf-8").split("\n")
                pnf = [l for l, f in fence_aware(plines) if not f]
                if kind == "practice":
                    # Count Exercise headings OUTSIDE the Appendix:
                    # phases 6-7 carry an "Appendix: Complete
                    # Reference Implementations" whose per-exercise
                    # reference builds are solutions, not new
                    # exercises; any other H1/H2 ends the appendix.
                    actual = 0
                    in_appendix = False
                    for l in pnf:
                        hm = HEADING.match(l)
                        if hm:
                            lvl = len(hm.group(1))
                            if lvl <= 2:
                                in_appendix = hm.group(2).lower(
                                    ).startswith("appendix")
                        if in_appendix:
                            continue
                        if hm and EXERCISE_TITLE.match(hm.group(2)):
                            actual += 1
                else:
                    actual = sum(1 for l in pnf if PHASE_Q.match(l))
                n_claims += 1
                if claimed != actual:
                    self.report(rel, "AS-13",
                                "phase %d row claims %d %s, %s holds %d"
                                % (phase, claimed, count_word,
                                   fname % phase, actual))
        return n_claims


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    args = parser.parse_args()

    linter = Linter()
    phases = args.root / "docs" / "phases"
    mods = sorted(p for p in phases.glob("*/*")
                  if p.is_dir() and MODULE_DIR.match(p.name))
    for mod in mods:
        linter.lint_module(args.root, mod)
    phase_quizzes = sorted((args.root / "docs" / "00-META" / "assessment")
                           .glob("phase*-quiz.md"))
    for pq in phase_quizzes:
        linter.lint_phase_quiz(args.root, pq)
    n_claims = linter.lint_index_tables(args.root)

    print("assessment_lint: %d findings across %d module assessments, "
          "%d phase quizzes and %d MI phase-table claims"
          % (len(linter.findings), len(mods), len(phase_quizzes),
             n_claims))
    return 1 if linter.findings else 0


if __name__ == "__main__":
    sys.exit(main())
