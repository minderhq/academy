#!/usr/bin/env python3
"""Prerequisites free-text vocabulary closure (PQ-04) for PROJECT-OMEGA.

prereq_census (PQ-01..03) locks the machine-parseable face of the
Prerequisites field - bracketed 4-digit tokens resolving to exactly
one file each - and prereq_ordering_scan (PO-01/02) locks that the
tokens point backwards on the path. The FREE-TEXT face was unmeasured
vocabulary: any authoring pointer a document writes there passes.

The birth census (2026-09-30) measured all 108 docs carrying the
field and the free-text class splits by doc role into exactly two
canonical strings:

     95  "See module README"      lessons pointing up to their module
      4  "See PREREQUISITES.md"   module READMEs pointing at the
                                  module's dedicated prerequisite doc
      5  bracketed resource tokens ([TUTORIAL-007], [1101], ...)
                                  resolved by PQ-01..02, ordered by
                                  PO-01/02 - out of scope here

4 prose variants were born with the gate ("Basic networking
knowledge", three "Phase N completion (...)" statements) and were
drained the same tick to "See module README": phase position already
encodes phase-order sequencing structurally (phase 3 lessons follow
phase 2 by spine position), so the prose was redundant - and all
four module READMEs carry a prerequisites section for the pointer
to land on. The closed vocabulary from then on: any value that is
not a 4-digit token, a pure bracket-token list, or one of the two
canonical strings is a finding - "See module README first",
"requires X", an empty field, a typo - prose the platform nav
generator cannot classify.

HARD GATE - exit 1 on any finding; born at 4, drained to zero the
same tick, hard since (the drain-then-harden cycle).

Run over the whole corpus:
    python scripts/qa/prereq_free_text_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
PQ_FIELD = re.compile(r"^Prerequisites:(.*)$")
FOUR_DIGIT = re.compile(r"\b\d{4}\b")
BRACKET_TOKEN = re.compile(r"\[[^\]]+\]")

CANONICAL = ("See module README", "See PREREQUISITES.md")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def pq_value(lines: list[str]) -> str | None:
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = PQ_FIELD.match(raw)
                if m:
                    return m.group(1).strip()
            return None
    return None


def legal(val: str) -> bool:
    if val in CANONICAL:
        return True
    if FOUR_DIGIT.search(val):
        return True  # machine-parseable: PQ-01..03 territory
    if BRACKET_TOKEN.fullmatch(val.replace(" ", "").replace(",", "|")):
        return True  # pure resource-token list: PQ-01..02 territory
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    n_docs = 0
    n_canonical = 0
    n_token = 0
    findings: list[str] = []
    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        val = pq_value(lines)
        if val is None:
            continue
        n_docs += 1
        if legal(val):
            if val in CANONICAL:
                n_canonical += 1
            else:
                n_token += 1
            continue
        rel = path.relative_to(args.root).as_posix()
        findings.append("PQ-04 non-canonical free-text Prerequisites: "
                        "%r in %s" % (val, rel))

    print("prereq_free_text_check: %d docs with Prerequisites field "
          "(%d canonical free-text, %d token forms)" % (n_docs, n_canonical,
                                                        n_token))
    for f in findings:
        print("  " + esc(f))
    print("prereq_free_text_check: %d PQ-04 findings - hard gate, "
          "born at zero (canonical: %s)"
          % (len(findings), " / ".join(CANONICAL)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
