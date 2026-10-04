#!/usr/bin/env python3
"""Prerequisite ordering census (PO-01/PO-02) for Minder Academy.

prereq_census (PQ-01..03) locks that every machine-parseable
prerequisite token resolves to exactly one file in canonical
bracketed form. What it deliberately does not look at is WHERE the
target sits on the learning path. On the platform a lesson whose
prerequisite is a LATER lesson is an unlock deadlock: the student
is told to finish something first that itself requires them.

The corpus numbering is monotonic along the curriculum - phases are
1xxx..7xxx, modules and lessons increase inside a phase - so "earlier
on the path" is exactly "smaller 4-digit number". That makes the
check deterministic, zero-heuristic:

PO-01  forward reference: a 4-digit prereq token with a number
       STRICTLY GREATER than the referring doc's own number.
PO-02  self reference: a 4-digit prereq token EQUAL to the
       referring doc's own number.

LAB-/TUTORIAL- tokens carry no position on the phase spine and are
out of scope (they are cross-cutting resources, checked for
resolution by PQ-01/02). Free-text values ("See module README")
carry no tokens and are skipped the same way prereq_census does.

HARD GATE - exit 1 on any finding, born at zero (KW-03 pattern):
the predicate is a numeric comparison, there is no false-positive
class to accept, and the birth census (2026-09-30) measured the
whole machine-parseable surface - 95 numbered docs with the field,
4 4-digit tokens (1102->[1101], 1103->[1101, 1102], 1202->[1201]),
every one strictly earlier than its referrer. 12 of the 13
non-numbered docs carry free-text values and one carries
[TUTORIAL-001], a resource token outside the ordering scope - so
the census surface is complete, not a silent subset.

Run over the whole corpus:
    python scripts/qa/prereq_ordering_scan.py --root .

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
TOKEN = re.compile(r"\b\d{4}\b")
SELF_NUM = re.compile(r"^(\d{4})-")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def pq_field(lines: list[str]) -> str | None:
    """Top-level Prerequisites value of one doc, or None. Same
    extraction as prereq_census for parity."""
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    paths = sorted((args.root / "docs").rglob("*.md"))

    n_docs = 0
    n_tokens = 0
    n_nonnumbered = 0
    nonnumbered: list[str] = []
    findings: list[str] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        val = pq_field(lines)
        if val is None:
            continue
        rel = path.relative_to(args.root).as_posix()
        self_m = SELF_NUM.match(path.name)
        if not self_m:
            # Non-numbered docs (guides, phase indexes, checkpoints)
            # carry no path position - never silently dropped.
            n_nonnumbered += 1
            nonnumbered.append(rel)
            continue
        self_n = int(self_m.group(1))
        n_docs += 1
        for tok in TOKEN.findall(val):
            n_tokens += 1
            n = int(tok)
            if n > self_n:
                findings.append(
                    "PO-01 forward-ref: %s Prerequisites %s (later lesson)"
                    % (rel, tok))
            elif n == self_n:
                findings.append(
                    "PO-02 self-ref: %s Prerequisites %s (own number)"
                    % (rel, tok))

    print("prereq_ordering_scan: %d docs with Prerequisites field, "
          "%d 4-digit tokens checked" % (n_docs, n_tokens))
    if n_nonnumbered:
        print("  skipped, no path position (%d docs):" % n_nonnumbered)
        for rel in nonnumbered:
            print("    " + esc(rel))
    if findings:
        for f in findings:
            print("  " + esc(f))
    print("prereq_ordering_scan: %d findings (PO-01 forward, PO-02 self)"
          " - hard gate" % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
