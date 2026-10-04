#!/usr/bin/env python3
"""Status vocabulary (SV-01) for Minder Academy.

Every doc's frontmatter carries a Status field; the platform reads it
for the publication pipeline and progress display. A free-text status
degrades into arbitrary variants ("complete", "Done", "WIP") that
filter wrong or not at all - the same argument that closed the
Difficulty vocabulary.

SV-01 (hard): Status must be from the closed vocabulary
{"Complete"}. Extending the vocabulary is a deliberate edit to this
script, not a doc-level choice - a new state (Draft, Review) must
arrive with platform semantics for how it renders and filters.

Birth census (2026-09-30): 408/408 docs carry Status: Complete -
single value, zero variants; hard from birth (KW-03).

Run over the whole corpus:
    python scripts/qa/status_vocab_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FM = re.compile(r"^---\s*$")
STATUS = re.compile(r"^Status:\s*(.+?)\s*$")
VOCAB = {"Complete"}


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    n_docs = 0
    n_ok = 0
    findings: list[str] = []

    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        if not text.startswith("---"):
            continue  # docs without frontmatter are not this gate's
        rel = path.relative_to(args.root).as_posix()
        n_docs += 1
        fm_n = 0
        value = None
        for ln in text.split("\n"):
            if fm_n == 1:
                m = STATUS.match(ln)
                if m:
                    value = m.group(1)
            if FM.match(ln):
                fm_n += 1
                if fm_n == 3:
                    break
        if value is None:
            findings.append("SV-01 no Status field in %s" % rel)
        elif value not in VOCAB:
            findings.append("SV-01 Status %r not in vocab %s in %s"
                            % (value, sorted(VOCAB), rel))
        else:
            n_ok += 1

    print("status_vocab_check: %d/%d frontmatter docs with valid "
          "Status" % (n_ok, n_docs))
    for f in findings:
        print("  " + esc(f))
    print("status_vocab_check: %d SV-01 findings - hard gate, born at "
          "zero (census 2026-09-30: 408/408 'Complete')" % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
