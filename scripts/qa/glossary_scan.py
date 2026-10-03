#!/usr/bin/env python3
"""Glossary integrity (GS-01..03, HARD) for PROJECT-OMEGA.

GLOSSARY.md is the platform's terminology backbone - lookup UIs,
tooltips and search will be generated from its tables. Three
defect classes found at the tick-464 census:

GS-01  a Correct/Incorrect-usage row must not list its own
       canonical term in the Incorrect Usage cell (case-exact
       variant match) - LLMOps did (`| LLM Ops, LLMOps, llmops |`
       taught the correct spelling as wrong), drained same tick
GS-02  every table term must be used somewhere in the corpus
       outside GLOSSARY.md (case-insensitive, word-boundary,
       plural-tolerant) - a term the learner never encounters is
       a dead entry; 01.AI (vendor + Yi-34B/6B used nowhere) was
       removed same tick
GS-03  a term must have exactly one row corpus-wide - Parameters
       had two entries with different definitions (Core AI vs
       Model Metrics), merged same tick (unit folded into the
       canonical definition)

Column schemas vary across tables (Definition/Related Terms,
Correct/Incorrect, Definition/Unit, Notable Models) - GS-01
applies only to tables whose header carries an Incorrect Usage
column; GS-02/03 apply to every bolded first-cell term.

Run over the whole corpus:
    python scripts/qa/glossary_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path

GLOSSARY = "GLOSSARY.md"
TERM_ROW = re.compile(r"^\| \*\*(.+?)\*\* \|(.*?)\|\s*$")
HDR_CELL = re.compile(r"^\|\s*([^|]+?)\s*(?:\|.+)*\|\s*$")
FENCE = re.compile(r"^ {0,3}(```|~~~)")  # CommonMark: <=3 leading spaces
FM_CLOSE = re.compile(r"^---\s*$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def body_lines(text: str) -> list[str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return lines
    for i, ln in enumerate(lines[1:40], 1):
        if FM_CLOSE.match(ln):
            return lines[i + 1:]
    return lines


def cells(ln: str) -> list[str]:
    return [c.strip() for c in ln.strip().strip("|").split("|")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    gpath = args.root / "docs" / "00-META" / GLOSSARY
    if not gpath.exists():
        print("glossary_scan: SKIP - docs/00-META/GLOSSARY.md not found, nothing to check")
        return 0
    text = gpath.read_text(encoding="utf-8", errors="replace")
    lines = body_lines(text)

    findings: list[str] = []
    terms: list[str] = []          # canonical term per table row
    inc_terms: list[str] = []      # rows under an Incorrect Usage header
    header: list[str] = []
    SEP = re.compile(r"^\|[\s:\-|]+\|\s*$")
    for ln in lines:
        if FENCE.match(ln):
            continue
        cs = cells(ln)
        if ln.strip().startswith("|") and cs and cs[0] == "Term":
            header = cs
            continue
        m = TERM_ROW.match(ln.strip())
        if not m:
            if not (ln.strip().startswith("|") and SEP.match(ln.strip())):
                header = []  # separator keeps the pending header
            continue
        term = m.group(1).strip()
        terms.append(term)
        if len(header) >= 2 and "Incorrect Usage" in header:
            inc_terms.append((term, cells(ln.strip())[header.index("Incorrect Usage")]
                              if len(cs) > header.index("Incorrect Usage") else ""))

    # GS-01: canonical term listed as its own incorrect variant
    for term, inc in inc_terms:
        variants = [v.strip() for v in inc.split(",")]
        if term in variants:
            findings.append("GS-01 %s: correct term listed in its own "
                            "Incorrect Usage cell (`%s`)" % (term, inc))

    # GS-03: duplicate terms across tables
    for term, n in Counter(t.lower() for t in terms).items():
        if n > 1:
            findings.append("GS-03 `%s` has %d rows across tables "
                            "(lookup wants exactly one)" % (term, n))

    # GS-02: dead entries - term never used in the corpus
    corpus: list[str] = []
    for path in sorted((args.root / "docs").rglob("*.md")):
        if path.name == GLOSSARY:
            continue
        try:
            corpus.append(path.read_text(encoding="utf-8",
                                         errors="replace"))
        except (UnicodeDecodeError, OSError):
            continue
    blob = "\n".join(corpus)
    for term in sorted(set(terms)):
        core = term.split("(")[0].strip()
        if not core:
            continue
        pat = (r"(?<![A-Za-z0-9])" + re.escape(core) +
               r"(?:s|es)?(?![A-Za-z0-9])")
        if not re.search(pat, blob, re.I):
            findings.append("GS-02 `%s` is a dead entry - used "
                            "nowhere outside the glossary" % term)

    for f in findings:
        print("  " + esc(f))
    print("glossary_scan: %d terms; %d GS findings - all hard "
          "(no self-referencing incorrect-usage rows, no dead "
          "entries, one row per term; born tick-464 after LLMOps "
          "self-reference, 01.AI dead entry, Parameters duplicate "
          "drains)" % (len(terms), len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
