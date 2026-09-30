#!/usr/bin/env python3
"""Tags coverage + syntax (TG-01..03, TS-01; all HARD) for PROJECT-OMEGA.

tag_vocabulary_census (TV-01..03) locks WHAT tags say; this gate
locks WHO carries them and in what shape. The platform's tag filter
and related-content navigation only see docs that carry Tags - a doc
without tags is invisible to both, and a mixed tag syntax renders
the filter's value chips inconsistently.

TG-01  numbered in-phase lesson docs outside guides/ must carry a
       Tags field. Born 2026-09-30 at 6 missing (5103, 5203, 5204,
       6203, 7302, 7403 - all 5-key-minimum docs), drained same day
       with their modules' own sibling tag pools; hard since.

TG-02  guides/ docs must carry Tags. Born report-only at 9/21; the
       12 gaps were drained 2026-09-30 (sibling-pool tags, 336fc6d).

TG-03  module/phase meta docs (README / PREREQUISITES / CHECKPOINT /
       phase README + everything else in docs/phases that is not a
       lesson or a guide) must carry Tags. Born report-only at
       10/146 (all phase2 revamp zone). The pending standard was
       decided 2026-09-30: nav nodes are platform PAGES - the entry
       points tag search should surface - so each module README /
       PREREQUISITES carries its sibling lessons' top-2 pool tags
       under a genre tag (module / prerequisites), each phase
       README / CHECKPOINT the phase's top-3 pool tags (phase /
       checkpoint). 72 docs drained, 146/146 since; hard.

TS-01  Tags must be written in the canonical syntax:
       Tags: ['tag-one', 'tag-two'] - bracketed, comma-space
       separated, each token single-quoted, non-empty, unique.
       Born 2026-09-30: a corpus census showed 242 quoted vs 13
       unquoted FM Tags lines (phase1 lessons' original style); the
       unquoted style leaked into the same-day nav-node drain via
       verbatim sibling-pool pulls. 89 docs normalized to quoted -
       79 in the first pass, plus 10 phase2 lines that were not just
       unquoted but BRACKETLESS (`Tags: a, b, c`): the first
       normalizer only parsed bracketed values, so TS-01's first run
       itself surfaced them ("empty token" - its TAG_LINE saw no
       brackets and read the value as empty). Drained same day,
       hard since.

HARD on all four - exit 1 if any finding.

Run over the whole corpus:
    python scripts/qa/tags_coverage_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
TG_FIELD = re.compile(r"^Tags:")
TAG_LINE = re.compile(r"^Tags:\s*\[(.*)\]\s*$")
CANON_TOKEN = re.compile(r"^'[^']+'$")
LESSON_NUM = re.compile(r"^\d{4}-")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def fm_tags(lines: list[str]) -> tuple[bool, str] | None:
    """Return (has_field, raw_value_or_blank) from the FM, else None."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for r in lines[1:i]:
                if TG_FIELD.match(r):
                    m = TAG_LINE.match(r)
                    return True, m.group(1) if m else ""
            return False, ""
    return None


def syntax_problems(raw: str) -> str | None:
    """Return a reason string if raw value is not canonical."""
    tokens = [t.strip() for t in raw.split(",")] if raw.strip() else []
    if not tokens or any(not t for t in tokens):
        return "empty or dangling-comma token"
    if any(not CANON_TOKEN.match(t) for t in tokens):
        return "non-quoted token"
    unquoted = {t[1:-1] for t in tokens}
    if len(unquoted) != len(tokens):
        return "duplicate token"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    n_lesson = n_lesson_ok = 0
    findings: list[str] = []
    n_guides = n_guides_ok = 0
    n_meta = n_meta_ok = 0
    n_ts = 0
    for path in sorted((args.root / "docs" / "phases").rglob("*.md")):
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        got = fm_tags(lines)
        if got is None:
            continue
        tagged, raw = got
        rel = path.relative_to(args.root).as_posix()
        in_guides = "guides" in path.parts
        if LESSON_NUM.match(path.name) and not in_guides:
            n_lesson += 1
            if tagged:
                n_lesson_ok += 1
            else:
                findings.append("TG-01 lesson without Tags: %s" % rel)
        elif in_guides:
            n_guides += 1
            if tagged:
                n_guides_ok += 1
            else:
                findings.append("TG-02 guide without Tags: %s" % rel)
        else:
            n_meta += 1
            if tagged:
                n_meta_ok += 1
            else:
                findings.append("TG-03 meta doc without Tags: %s" % rel)
        if tagged:
            problem = syntax_problems(raw)
            if problem:
                n_ts += 1
                findings.append("TS-01 %s Tags syntax (%s): %s"
                                % (rel, problem,
                                   ("[" + raw + "]")[:70]))

    print("tags_coverage_check: %d/%d lessons, %d/%d guides, %d/%d "
          "meta docs carry Tags; %d TS-01 syntax findings"
          % (n_lesson_ok, n_lesson, n_guides_ok, n_guides,
             n_meta_ok, n_meta, n_ts))
    for f in findings:
        print("  " + esc(f))
    print("tags_coverage_check: %d TG/TS findings - all hard; "
          "coverage and canonical quoted syntax (born 2026-09-30: "
          "6+12+72 coverage gaps drained, 89 docs normalized)"
          % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
