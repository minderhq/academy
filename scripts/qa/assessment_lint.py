#!/usr/bin/env python3
"""Assessment quality linter for the Minder Academy curriculum corpus.

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
         drain left 33/33 banks explained, so hard gate from birth;
         joined tick-781 by the seven phase quizzes' table-form
         Answer Keys - born 180/180 rows explained)
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
  AS-14  a phase quiz's "**Passing: N/M (80%)**" line is a contract
         the platform surfaces verbatim: M must equal the quiz's
         question count, N must equal ceil(P/100 * M) for the
         stated P, and P must stay the corpus's 80% convention
         (the module banks grade at 80% too). Joined tick-567 -
         born census-proven at zero across all seven quizzes
         (12/15, 16/20, 20/25 and 24/30 at exact 80% multiples);
         the line previously had no reader, so a question-count
         edit could silently strand the threshold a learner is
         told to hit
  AS-15  answer-length cue: the correct option is longest-or-tied
         (in words AND characters, QI-10's exact metric) in >= 50%
         of the quiz's >= 4-option answered questions (min 10),
         because a learner who always picks the longest option
         passes without reading - the quiz then measures length,
         not knowledge. The corpus line is quiz_integrity_scan's
         own QI-10 report threshold (tick-290), applied hard to
         both quiz shapes. Joined tick-568 - born census caught
         exactly the seven phase quizzes (the module banks had
         drained to a 2.4% corpus rate under the report queue:
         66.7%..93.3% tied per phase quiz, a longest-picker
         scoring ~83% against the 80% passing line the AS-14
         locks); the flagged distractors were lengthened with
         false-anchoring qualifiers before the ceiling locked
  AS-16  within-question option hygiene, two rules about what one
         question shows the learner: (1) no two options carry the
         same text (casefold + whitespace-collapse exact; punctuation
         preserved, so "d_model / num_heads" vs "d_model + num_heads"
         stays distinct - the census false positive that fixed the
         normalization), since a repeated option makes the key
         ambiguous for any learner who picks it; (2) no deferred or
         compound option ("All of the above", "None of these", bare
         letter-lists), since it hides multi-answer logic in a
         single-answer bank - it corrupts the letter balance AS-09
         locks and rewards a learner who reads only the meta-option.
         Joined tick-569 - born census caught exactly 35 deferred
         options across 16 module banks, every one on letter B/C/D
         ("All/None of the above" and "Both A and C" forms alike),
         22 with the key ON the deferred option (a "pick two"
         question graded as one), zero true duplicates under the
         honest normalization; the 22 keyed ones became concrete
         summaries of their combined options and the 13 distractors
         became concrete false options before the lock tightened
  AS-17  stem-echo lock, two rules about what the question stem
         shows the learner: (1) no keyed option appears verbatim in
         its own stem (casefold + whitespace-collapse under the
         number-prefix-stripped stem normalization - the naive norm
         matched keyed option "1" against the question number
         "**10.", the census false positive that added the strip);
         (2) no two-or-more informative tokens (len >= 3, not
         function words, exact forms - "channel" and "channels" stay
         distinct) shared by the stem and the keyed option but by no
         distractor, since a learner matching words picks the key
         without reading. The corpus line is measured, tick-570:
         single-token echoes are 63/835 (7.5%) normal vocabulary
         overlap and stay legal, two-token echoes were exactly 7,
         three never occur. Joined tick-570 - born census caught
         exactly those 7 phrase echoes across 7 module banks (the
         "learning rate" / "vision+language" / "adapters+model" /
         "calling+llm" class), every one drained same tick by
         rewording the keyed option off its echoed tokens
  AS-18  the phase quiz's learner-facing count claim - the header
         line "**N Questions | Passing Score: 80% | Time: ...**"
         must carry a number equal to the quiz's actual question
         count, and the header must exist: a drifted header
         promises a different bank than the one below it while
         every per-question check stays clean, and an absent
         header leaves the platform's count claim unvouched. The
         claim is read from the first 30 lines outside fences
         (the header's only home in the shape). Scoped to the
         seven phase quizzes - the passing line's own total
         contract is AS-14's (a drifted header with the passing
         line intact fires here and only here). Joined tick-626 -
         born census 7/7 headers present, 0 drift across 180
         questions (15/20/25/30/30/30/30)
  AS-19  the phase-practice exercise numbering - inside each of the
         seven phase practice files the "Exercise N" headings must
         run 1..K with no gap, repeat or wrong start, checked per
         segment: the main body and (phases 6-7) the appendix
         reference implementations each restart at 1, the same
         appendix boundary AS-13 counts across. A deleted section
         or a fat-fingered renumber serves the learner a broken
         sequence while the heading COUNT stays intact - AS-13's MI
         rows compare counts, not numbers, so the drift is
         invisible there. Covers both surfaces: the seven phase
         practice files per segment (main body and phases 6-7
         appendix each restart at 1) and the 33 module PRACTICE.md
         files as one sequence (no module carries an appendix
         section, so the whole file is a single 1..K run). Module
         surface joined tick-628 - born census 33/33
         single-segment contiguous, 184 exercises (169 H3 +
         15 H2 headings; the H2 shape lives in 2300/4300/4400)
  AS-20  the phase quiz's answer-key written numbering - the
         comma-pair entries (or, since tick-781, the table rows)
         after "## Answer Key" must run exactly
         1..N (N = the quiz's question count), no gap, repeat or
         broken order: the key dict collapses duplicates at
         capture time and AS-08 compares only the intersection,
         so a key missing an entry served the learner a review key
         they cannot look the question up in while every check
         stayed clean. Partition (the tick-631 shape): a citation
         outside the question set is a misdirected key and AS-08's
         stale branch names it - inside the set the written
         sequence is AS-20's; the module banks' key-table rows are
         RM-00's (review_map_check). Scoped to the seven phase
         quizzes. Joined tick-635 - born census 7/7 keys write
         exact 1..N (15/20/25/30/30/30/30, 180 entries),
         born-at-zero; migrated to the module table canon
         tick-781 (the escaped comma blobs rendered as one
         paragraph - the OL-01 tick-468 escape only stopped the
         broken-list rendering), the capture now reads both
         surfaces in document order
  AS-21  the phase README's learner-facing quiz claim - the
         Assessment bullet "- **[Phase N Quiz](...)** - Test
         your understanding (NN questions, PP% to pass)" must
         exist exactly once per phase README, its question
         count must equal the phase quiz's actual question
         count (the same "### N." headings AS-03/AS-18 vouch
         inside the quiz) and its passing pct must state the
         corpus 80% convention (AS-14's on the quiz side). A
         drifted count promised a different bank than the one
         behind the link while every check stayed clean, and
         the claim was vouched by nothing - feed_parity_check
         totals the corpus aggregates and course_card_check
         walks the module READMEs, so the seven phase READMEs
         sat outside both. Partition: the quiz file's own
         header claim is AS-18's, its passing line AS-14's,
         the MI rows AS-13's, a broken link linkcheck's - the
         claim line's values are AS-21's alone. Scoped to
         docs/phases/phase*/README.md. Joined tick-636 - born
         census 7/7 carry the line, 1/7 (phase 3) wrote the
         true count, 6 drained same tick - born-at-zero
  AS-22  the informative-option floor over both quiz shapes - no
         option may be a bare "Both", "Neither", "All", "None"
         or "Either" (whole-option text, whitespace-collapse +
         casefold exact, an optional trailing period tolerated,
         the \b keeping "nonempty" and friends out): the bare
         word carries no content a learner can be right or wrong
         about, so a testwise learner keys it from position
         priors instead of knowing the material. The compound
         form ("All of the above", "None of these", bare
         letter-lists) is AS-16's deferred class - AS-22 owns
         the disjoint bare single-word remainder. Joined
         tick-641 - born census 29 rows across 9 module banks
         (19 on the D slot, 8 on C, 1 on B, 1 on A; at 4 of
         them the generic was itself the key), phase quizzes
         born clean, drained same tick - born-at-zero

Fence model: the tick-678 CommonMark canon state machine in
fence_aware() - tick-689 replaced the bare startswith('```') bool
toggle, which never modeled run length (a 4-run super-fence opened
and its first inner marker closed it, exposing the inner template
pair to the question/option model) and never saw a tilde fence.

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
# Options render as list items since tick-783 ("- A) text") - the
# optional "- " marker is tolerated like quiz_export's OPTION.
OPT_LINE = re.compile(r"^\s*[-*]?\s*\*{0,2}([A-E])\) ")
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
# the learner-facing pass contract: "**Passing: 12/15 (80%)**"
PASS_LINE = re.compile(r"\*\*Passing:\s*(\d+)/(\d+)\s*\((\d+)%\)\*\*")
# AS-18: the phase quiz's learner-facing count claim, the header line
# "**15 Questions | Passing Score: 80% | Time: 30 minutes**"
HEADER_QUESTIONS = re.compile(r"\*\*(\d+)\s+Questions?\b")
# AS-21: the phase README's learner-facing quiz claim, the
# Assessment-section bullet
# "- **[Phase N Quiz](...)** - Test your understanding
# (NN questions, PP% to pass)".
README_QUIZ_CLAIM = re.compile(
    r"^- \*\*\[Phase \d+ Quiz\]\([^)]+assessment/phase\d+-quiz\.md\)\*\*"
    r" - Test your understanding \((\d+) questions, (\d+)% to pass\)\s*$")
# AS-15: option text with its letter, both quiz shapes (module banks
# render "A) text", phase quizzes render lowercase "a) text"; both as
# "- " list items since tick-783).
OPT_TEXT = re.compile(r"^\s*[-*]?\s*\*{0,2}([A-Ea-e])\)\s+(.+?)\s*$")
# AS-15 shares QI-10's corpus line exactly (quiz_integrity_scan,
# tick-290): tied-or-longer on both axes in >= 50% of the bank's
# >= 4-option answered questions, banks under 10 mcq exempt.
LEN_BIAS_SHARE = 0.5
LEN_BIAS_MIN_MCQ = 10
# AS-16: deferred/compound options - a single-answer bank must not
# hide multi-answer logic in an option slot ("All of the above",
# "None of these", bare letter-lists like "A and B").
DEFERRED_OPT = re.compile(
    r"^(?:all|none)\s+of\s+the\s+(?:above|these|options|listed)\b|"
    r"^(?:all|none)\s+of\s+these\b|"
    r"^(?:both\s+)?[a-e](?:\s*(?:and|or|,|&)\s*[a-e])+$", re.I)
# AS-22: the bare generic word an option slot must never carry.
# AS-16's DEFERRED_OPT owns the compound form ("All of the above",
# letter-lists); this is the disjoint bare single-word remainder.
# The match runs on the AS-16 duplicate-rule normalization
# (whitespace-collapse + casefold) and tolerates one trailing
# period; the \b keeps "nonempty" and friends out.
GENERIC_OPT = re.compile(r"^(?:both|neither|all|none|either)\b\.?$")
# AS-17: the stem-echo corpus line, measured tick-570 over the 835-mcq
# corpus: a single echoed token is normal vocabulary overlap (63
# questions, 7.5%), two or more tokens echoed by the keyed option and
# by no distractor is the phrase-match tell a test-prep guide warns
# about (exactly 7, all drained same tick), three never occurs.
ECHO_MIN_TOKENS = 2
# Informative-token filter for the echo rule: len >= 3, not a function
# word. Exact tokens - no stemming, so "channel" and "channels" stay
# distinct (the AS-16 punctuation lesson applied to morphology).
ECHO_STOP = frozenset("""
a an the and or of in on for to with that this it its is are was were
be been being as by at from not no nor but if then than so such can
could will would should shall may might must do does did done have has
had using use used uses into over under between within about after
before during through each every some most more less least only also
very there their them they you your we our us i me my he she his her
which what when where who whom whose why how whether list following
above below question questions answer answers option options none all
any both either neither true false correct incorrect given shows shown
show describe describes describing best least called name named term
refers refer referring mean means meaning
""".split())
ECHO_TOK = re.compile(r"[a-z0-9_]+")
# the tick-678 CommonMark fence canon (landed tick-689): run-length
# openers, tilde fences included, a true closer repeats the opener
# character in a run at least as long, a different fence character
# never closes, a non-closer marker line is fence content.
FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")


def echo_tokens(text: str) -> set:
    """The informative tokens the AS-17 echo rule compares on."""
    return {w for w in ECHO_TOK.findall(text.casefold())
            if len(w) >= 3 and w not in ECHO_STOP}


def stem_text(line: str) -> str:
    """The stem body of a question heading line, number prefix and
    markdown bold stripped - the honest normalization the verbatim
    rule compares under (the naive norm matched the keyed option "1"
    against the question number "**10." - the census false positive
    that added the prefix strip)."""
    m = QUESTION_BOLD.match(line) or QUESTION_H3.match(line) \
        or PHASE_Q.match(line)
    body = line[m.end():] if m else line
    return body.strip().strip("*").strip()


def fence_aware(lines):
    """Yield (line, in_fence) under the tick-678 CommonMark canon; the
    marker line itself is yielded with the PRE-update state, the opener
    opens for subsequent lines, a true closer repeats the opener
    character in a run at least as long, a different fence character
    never closes, and a non-closer marker line is fence content (the
    old bare startswith('```') toggle opened a 4-run super-fence and
    let its first inner marker close it, exposing the inner template
    pair to the question/option model)."""
    fence: tuple[str, int] | None = None
    for line in lines:
        yield line, fence is not None
        m = FENCE_OPEN.match(line)
        if m:
            ch, run = m.group(1)[0], len(m.group(1))
            if fence:
                if ch == fence[0] and run >= fence[1]:
                    fence = None
            else:
                fence = (ch, run)


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
        stems = {}
        for _, l in nf:
            m = QUESTION_BOLD.match(l) or QUESTION_H3.match(l)
            if m:
                qnums.add(int(m.group(1)))
                stems[int(m.group(1))] = stem_text(l)
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
        qopts: dict = {}
        q = None
        for _, l in nf:
            m = QUESTION_BOLD.match(l) or QUESTION_H3.match(l)
            if m:
                q = int(m.group(1))
                continue
            m = OPT_LINE.match(l)
            if m and q is not None:
                opts.setdefault(q, set()).add(m.group(1))
            t = OPT_TEXT.match(l)
            if t and q is not None:
                qopts.setdefault(q, {})[t.group(1).upper()] = t.group(2)
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

        # AS-15: the length cue, QI-10's report metric as a hard
        # line over both quiz shapes. The module banks drained to a
        # 2.4% corpus rate under the report queue (tick-290), so this
        # is born-at-zero for them - the ceiling exists for the day
        # an edit re-skews a bank.
        answered = [{"num": n,
                     "answer": key.get(n) or inline.get(n),
                     "options": qopts[n],
                     "stem": stems.get(n, "")}
                    for n in sorted(qnums)
                    if (key.get(n) or inline.get(n)) and n in qopts]
        self.check_len_bias(rel, answered)
        # AS-16: within-question option hygiene, the two rules every
        # option set owes the learner. Born tick-569 catching the 35
        # deferred options across 16 module banks, drained same tick.
        self.check_option_sanity(rel, answered)
        # AS-22: the informative-option floor - no bare
        # both/neither/all/none word in a slot. Born tick-641
        # catching 29 across 9 module banks, drained same tick.
        self.check_generic_opts(rel, answered)
        # AS-17: the stem must not hand over the answer. Born tick-570
        # catching exactly 7 stem echoes across 7 module banks, drained
        # same tick.
        self.check_stem_echo(rel, answered)

    def check_len_bias(self, rel: str, answered: list) -> None:
        """AS-15 shared by both quiz shapes: quiz_integrity_scan's
        QI-10 report metric as a hard line - the correct option is
        longest-or-tied (words AND characters) in >= LEN_BIAS_SHARE
        of the quiz's >= 4-option answered questions (min
        LEN_BIAS_MIN_MCQ), so a learner who always picks the longest
        option passes without reading."""
        mcq = [q for q in answered if len(q["options"]) >= 4]
        if len(mcq) < LEN_BIAS_MIN_MCQ:
            return
        tied = 0
        for q in mcq:
            a = q["answer"]
            ow = [len(q["options"][k].split()) for k in q["options"]
                  if k != a]
            oc = [len(q["options"][k]) for k in q["options"] if k != a]
            if (len(q["options"][a].split()) >= max(ow)
                    and len(q["options"][a]) >= max(oc)):
                tied += 1
        if tied >= LEN_BIAS_SHARE * len(mcq):
            self.report(rel, "AS-15",
                        "length cue: the correct option is "
                        "longest-or-tied in %d/%d questions (corpus "
                        "line 50%% - a learner who always picks the "
                        "longest option passes without reading)"
                        % (tied, len(mcq)))

    def check_option_sanity(self, rel: str, answered: list) -> None:
        """AS-16 shared by both quiz shapes: within-question option
        hygiene, two rules about what one question shows the learner.
        (1) No two options carry the same text (casefold +
        whitespace-collapse exact - punctuation preserved, so
        "d_model / num_heads" vs "d_model + num_heads" stays distinct),
        since a repeated option makes the key ambiguous for any learner
        who picks it. (2) No deferred or compound option ("All of the
        above", "None of these", bare letter-lists), since it hides
        multi-answer logic in a single-answer bank: it corrupts the
        letter balance AS-09 locks and rewards a learner who reads only
        the meta-option."""
        for q in answered:
            n, opts = q["num"], q["options"]
            seen = {}
            for k in sorted(opts):
                t = " ".join(opts[k].split()).casefold()
                if t in seen:
                    self.report(rel, "AS-16",
                                "duplicate option texts in question %d: "
                                "%s) and %s) carry the same text - a "
                                "learner who picks either cannot be "
                                "graded on the key" % (n, seen[t], k))
                else:
                    seen[t] = k
            for k in sorted(opts):
                if DEFERRED_OPT.match(opts[k].strip()):
                    self.report(rel, "AS-16",
                                "deferred option in question %d: %s) "
                                "is an all/none-of-the-above-style "
                                "choice - single-answer grading cannot "
                                "key it" % (n, k))

    def check_generic_opts(self, rel: str, answered: list) -> None:
        """AS-22 shared by both quiz shapes: the informative-option
        floor. An option that is nothing but "Both", "Neither",
        "All", "None" or "Either" (an optional trailing period
        tolerated) carries no content the learner can be right or
        wrong about - a testwise learner keys it from position
        priors instead of knowing the material, and the pair it
        sits against ("Both" next to a split option set) is the
        giveaway. The compound form ("All of the above", bare
        letter-lists) is AS-16's deferred class; AS-22 owns the
        bare single-word remainder."""
        for q in answered:
            n, opts = q["num"], q["options"]
            for k in sorted(opts):
                t = " ".join(opts[k].split()).casefold()
                if GENERIC_OPT.match(t):
                    self.report(rel, "AS-22",
                                "generic option in question %d: %s) is "
                                "a bare both/neither/all/none word - a "
                                "non-informative choice a learner can "
                                "key without reading the material"
                                % (n, k))

    def check_stem_echo(self, rel: str, answered: list) -> None:
        """AS-17 shared by both quiz shapes: the stem must not hand
        over the answer. (1) Verbatim: the keyed option's normalized
        text appearing in the normalized stem is the question quoting
        its own answer. (2) Echo: ECHO_MIN_TOKENS or more informative
        tokens shared by the stem and the keyed option but by no
        distractor - a learner matching words picks the key without
        reading, the tell every test-prep guide warns about."""
        for q in answered:
            n, a, opts = q["num"], q["answer"], q["options"]
            stem = " ".join(q["stem"].split()).casefold()
            if stem and " ".join(opts[a].split()).casefold() in stem:
                self.report(rel, "AS-17",
                            "stem leak in question %d: the keyed option "
                            "%s) appears verbatim in the stem - the "
                            "question hands over the answer" % (n, a))
                continue
            st = echo_tokens(q["stem"])
            if not st:
                continue
            keyed = echo_tokens(opts[a])
            distr = set()
            for k in opts:
                if k != a:
                    distr |= echo_tokens(opts[k])
            echo = (st & keyed) - distr
            if len(echo) >= ECHO_MIN_TOKENS:
                self.report(rel, "AS-17",
                            "stem echo in question %d: %s appear in the "
                            "stem and in the keyed option %s) but in no "
                            "distractor - matching words picks the key "
                            "without reading"
                            % (n, ", ".join(sorted(echo)), a))

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
        stems: dict = {}
        last = None
        inline: dict = {}
        qopts: dict = {}
        for _, l in nf:
            m = PHASE_Q.match(l)
            if m:
                qnums.add(int(m.group(1)))
                stems[int(m.group(1))] = stem_text(l)
                last = int(m.group(1))
                continue
            m = PHASE_INLINE.search(l)
            if m and last is not None and last not in inline:
                inline[last] = m.group(1).upper()
                continue
            t = OPT_TEXT.match(l)
            if t and last is not None:
                qopts.setdefault(last, {})[t.group(1).upper()] = t.group(2)
        if qnums != set(range(1, len(qnums) + 1)):
            self.report(rel, "AS-03",
                        "question numbering not contiguous 1..%d"
                        % len(qnums))
        # AS-18: the learner-facing "**N Questions | ...**" header
        # claim must exist and equal the quiz's actual question
        # count - a drifted header promises a different bank than
        # the one below it while every per-question check stays
        # clean, and an absent header leaves the platform's count
        # claim unvouched. Read from the first 30 lines outside
        # fences (the header's only home in the shape). Scoped to
        # the phase shape - the passing line's own total contract
        # is AS-14's, so a passing-line drift fires there and not
        # here. Born tick-626: census 7/7 headers present, 0 drift
        # across 180 questions (15/20/25/30/30/30/30).
        claim = None
        for i, l in nf:
            if i >= 30:
                break
            m = HEADER_QUESTIONS.search(l)
            if m:
                claim = int(m.group(1))
                break
        if claim is None:
            self.report(rel, "AS-18",
                        "no **N Questions** header claim "
                        "(platform count claim absent)")
        elif claim != len(qnums):
            self.report(rel, "AS-18",
                        "header claims %d questions, quiz carries %d"
                        % (claim, len(qnums)))
        uncovered = sorted(qnums - set(inline))
        if uncovered:
            self.report(rel, "AS-04",
                        "questions %s carry no inline answer" % uncovered)

        # The Answer Key block mirrors the inline answers: where it
        # exists it must cite only real questions and agree with them.
        # Two written surfaces are captured in document order - the
        # comma-pair form the block carried until tick-781 and the
        # module-bank table canon (| N | X | explanation |) it joined
        # that tick, which also brings AS-11's explanation-cell
        # contract to the phase shape (born tick-781, 7/7 explained,
        # 180/180 rows).
        key: dict = {}
        ak_idx = next((i for i, l in nf if AK_SECTION.match(l)), None)
        if ak_idx is None:
            self.report(rel, "AS-04", "no ## Answer Key section")
        else:
            entries: list = []
            for i, l in nf:
                if i <= ak_idx:
                    continue
                h = HEADING.match(l)
                if h and len(h.group(1)) <= 2:
                    break
                mrow = AK_ROW.match(l)
                if mrow:
                    entries.append((int(mrow.group(1)),
                                    mrow.group(2)))
                    cells = [c.strip()
                             for c in l.strip().strip("|").split("|")]
                    # AS-11: the row must carry a filled explanation
                    # cell - the module banks' rule extended to the
                    # phase table surface.
                    if len(cells) < 3 or not cells[2]:
                        self.report(rel, "AS-11",
                                    "question %d answer-key row has "
                                    "no explanation cell"
                                    % int(mrow.group(1)))
                else:
                    entries.extend((int(n), L.upper()) for n, L
                                   in PHASE_KEY_PAIR.findall(l))
            key = dict(entries)
            stale = sorted(set(key) - qnums)
            if stale:
                self.report(rel, "AS-08",
                            "answer-key block cites nonexistent "
                            "questions %s" % stale)
            else:
                # AS-20: the key's WRITTEN numbering inside the
                # question set. The dict above collapses duplicates
                # at capture time and the AS-08 loop below compares
                # only the intersection, so a key whose entries ran
                # with a gap, a repeat or a broken order served the
                # learner a review key missing an entry while every
                # check stayed clean. Partition (tick-631 shape): a
                # citation outside the question set is a misdirected
                # key - AS-08's stale branch names it; inside the
                # set the written sequence must be exactly 1..N.
                # RM-00 owns the module banks' key-table rows; this
                # is the phase-quiz key surfaces' contract (both the
                # comma-pair form and, since tick-781, the table
                # form the module canon uses).
                written = [n for n, _ in entries]
                if written != list(range(1, len(qnums) + 1)):
                    self.report(rel, "AS-20",
                                "answer-key entries are numbered %s, "
                                "expected 1..%d"
                                % (", ".join(str(n) for n in written)
                                   or "nothing", len(qnums)))
            for n in sorted(set(key) & set(inline)):
                if key[n] != inline[n]:
                    self.report(rel, "AS-08",
                                "question %d: key=%s inline=%s"
                                % (n, key[n], inline[n]))

        # The "**Passing: N/M (80%)**" line is the contract the
        # platform surfaces verbatim: exactly one per quiz, its
        # total equal to the question count, and its threshold
        # the integer ceil of the stated percentage (the corpus
        # convention is 80%).
        plines = [(i, l) for i, l in nf if PASS_LINE.search(l)]
        if len(plines) == 0:
            self.report(rel, "AS-14",
                        "no '**Passing: N/M (80%)**' line")
        elif len(plines) > 1:
            self.report(rel, "AS-14",
                        "%d passing lines (expected 1)" % len(plines))
        else:
            need, total, pct = (int(g) for g
                                in PASS_LINE.search(plines[0][1]).groups())
            if total != len(qnums):
                self.report(rel, "AS-14",
                            "passing-line total %d != %d questions"
                            % (total, len(qnums)))
            if pct != 80:
                self.report(rel, "AS-14",
                            "passing-line pct %d != the 80%% convention"
                            % pct)
            want = (pct * total + 99) // 100
            if need != want:
                self.report(rel, "AS-14",
                            "passing threshold %d != ceil(%d%% of %d) = %d"
                            % (need, pct, total, want))

        self.check_balance(rel, key, qnums, inline)

        # AS-15: the length cue in the phase-quiz shape too - born
        # tick-568 catching exactly the seven phase quizzes (the
        # module banks were already drained), drained same tick.
        answered = [{"num": n,
                     "answer": key.get(n) or inline.get(n),
                     "options": qopts[n],
                     "stem": stems.get(n, "")}
                    for n in sorted(qnums)
                    if (key.get(n) or inline.get(n)) and n in qopts]
        self.check_len_bias(rel, answered)
        self.check_option_sanity(rel, answered)
        self.check_generic_opts(rel, answered)
        self.check_stem_echo(rel, answered)

    def lint_phase_readme_claims(self, root: Path) -> int:
        """AS-21: the phase README's learner-facing quiz claim.

        Each phase README's Assessment section carries the bullet
        "- **[Phase N Quiz](...)** - Test your understanding
        (NN questions, PP% to pass)" - the surface a learner
        reads before opening the quiz file itself. The bullet
        must exist exactly once, its question count must equal
        the phase quiz's actual question count (the same "### N."
        headings AS-03/AS-18 vouch inside the quiz), and its
        passing percentage must state the corpus 80% convention
        (AS-14's convention on the quiz side). A drifted count
        promised a different bank than the one behind the link
        while every check stayed clean, and the claim was
        vouched by nothing - feed_parity_check totals the corpus
        aggregates and course_card_check walks the module
        READMEs, so the seven phase READMEs sat outside both.
        Partition (the tick-631 shape): the quiz file's own
        header claim is AS-18's, its passing line is AS-14's,
        the MI phase-table rows are AS-13's, and a broken link
        is linkcheck's - the claim line's VALUES are AS-21's
        alone. Scoped to docs/phases/phase*/README.md. Born
        tick-636: census 7/7 carry the line, 1/7 (phase 3) wrote
        the true count, 6 drained same tick - born-at-zero.
        """
        n = 0
        for d in sorted((root / "docs" / "phases").glob("phase*")):
            if not d.is_dir():
                continue
            readme = d / "README.md"
            if not readme.is_file():
                continue
            n += 1
            rel = readme.relative_to(root).as_posix()
            mdir = re.match(r"^phase(\d+)-", d.name)
            quiz = (root / "docs" / "00-META" / "assessment"
                    / ("phase%s-quiz.md" % mdir.group(1)))
            lines = readme.read_text(encoding="utf-8").split("\n")
            hits = []
            for l, f in fence_aware(lines):
                if f:
                    continue
                m = README_QUIZ_CLAIM.match(l)
                if m:
                    hits.append(m)
            if len(hits) != 1:
                self.report(rel, "AS-21",
                            "%d quiz claim lines (expected 1)" % len(hits))
                continue
            if not quiz.is_file():
                continue  # broken links are linkcheck's lane
            qlines = quiz.read_text(encoding="utf-8").split("\n")
            actual = sum(1 for l, f in fence_aware(qlines)
                         if not f and PHASE_Q.match(l))
            count, pct = (int(g) for g in hits[0].groups())
            if count != actual:
                self.report(rel, "AS-21",
                            "claims %d questions, %s carries %d"
                            % (count, quiz.name, actual))
            if pct != 80:
                self.report(rel, "AS-21",
                            "claims %d%% to pass != the 80%% convention"
                            % pct)
        return n

    def lint_phase_practice(self, root: Path, pp: Path) -> None:
        """AS-19: phase-practice "Exercise N" numbering runs 1..K.

        Checked per segment - the main body and the appendix
        reference implementations (phases 6-7) each restart at 1,
        the same appendix boundary AS-13 counts across.
        """
        rel = pp.name
        lines = pp.read_text(encoding="utf-8").split("\n")
        pnf = [l for l, f in fence_aware(lines) if not f]
        segs: list = [[]]  # segment 0 = main body, then one per appendix
        for l in pnf:
            hm = HEADING.match(l)
            if hm:
                lvl = len(hm.group(1))
                if lvl <= 2 and hm.group(2).lower().startswith("appendix"):
                    segs.append([])  # solutions, not new exercises
                    continue
                em = EXERCISE_TITLE.match(hm.group(2))
                if em:
                    segs[-1].append(int(em.group(1)))
        for si, nums in enumerate(segs):
            if not nums:
                continue
            if nums != list(range(1, len(nums) + 1)):
                where = "appendix" if si else "main body"
                self.report(rel, "AS-19",
                            "exercise numbering in the %s runs %s, "
                            "expected 1..%d"
                            % (where, ", ".join(str(n) for n in nums),
                               len(nums)))

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

        # AS-19 (module surface): one 1..K run per file - the same
        # numbering contract the phase practice files vouch per segment.
        nums = [num for _, _, num in exercises]
        if nums != list(range(1, len(nums) + 1)):
            self.report(rel, "AS-19",
                        "exercise numbering runs %s, expected 1..%d"
                        % (", ".join(str(n) for n in nums), len(nums)))

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
        if not mi.exists():
            print("assessment_lint: SKIP - docs/00-META/MASTER-INDEX.md not found, nothing to check")
            return 0
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
    phase_practices = sorted((args.root / "docs" / "00-META"
                              / "assessment")
                             .glob("phase*-practice.md"))
    for pp in phase_practices:
        linter.lint_phase_practice(args.root, pp)
    n_readmes = linter.lint_phase_readme_claims(args.root)
    n_claims = linter.lint_index_tables(args.root)

    print("assessment_lint: %d findings across %d module assessments, "
          "%d phase quizzes, %d phase-README claims and "
          "%d MI phase-table claims"
          % (len(linter.findings), len(mods), len(phase_quizzes),
             n_readmes, n_claims))
    return 1 if linter.findings else 0


if __name__ == "__main__":
    sys.exit(main())
