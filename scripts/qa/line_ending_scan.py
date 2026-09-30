#!/usr/bin/env python3
"""Line-ending + final-newline hygiene (LE-01/02, HARD).

This is the one byte-level gate in the fleet, and it has to be:
every other scan reads with universal newlines, which silently
translates CRLF to LF - the entire fleet is structurally blind to
line-ending drift. Reading raw bytes restores the sight:

LE-01  no carriage-return byte anywhere in docs/**/*.md - no
       CRLF endings, no lone CR. CR bytes break POSIX text
       tooling, pollute diffs (phantom whole-file rewrites),
       and leak into slug/search pipelines on byte-level
       platform ingestion.

LE-02  every non-empty docs/**/*.md ends with a newline -
       POSIX hygiene; its absence produces the "No newline
       at end of file" diff noise and concat hazards.

Whole file, byte-level, by design - fences and front matter are
irrelevant to line endings: a CR inside a code fence is still a
CR. This gate does not re-implement text analysis; it watches the
one axis the text-mode fleet cannot see.

Scope notes, so the gate stays narrow and honest:
- the COMMITTED content is already protected: .gitattributes
  `* text=auto eol=lf` normalizes every text file at add time,
  so this gate guards the WORKTREE corpus that all other gates
  and the platform ingestion actually read
- notebooks (.ipynb) and conda .yml files under docs/ were
  renormalized in the same tick's drain (worktree-only, sha-
  neutral) but stay out of gate scope: the corpus convention of
  this fleet is docs/**/*.md
- trailing blank lines (a file ending \n\n) are a whitespace
  concern, not a line-ending one - not checked here

Born tick-490, born-at-zero after the drain: 120 stale-CRLF .md
worktree copies renormalized (published HEAD content measured
100% LF byte-exact - the CRLF was a local checkout artifact
predating the eol=lf policy), 24 notebook/yml worktree copies
renormalized, and 2 README blobs missing their final newline
fixed in content (phase5 5400/5500 READMEs).

Run over the whole corpus:
    python scripts/qa/line_ending_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CR = chr(13).encode("ascii")
NL = chr(10).encode("ascii")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    n_crlf = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            data = path.read_bytes()
        except OSError:
            continue
        rel = path.relative_to(args.root).as_posix()
        n_docs += 1
        if not data:
            continue
        n_cr = data.count(CR)
        if n_cr:
            n_crlf += 1
            findings.append(
                "LE-01 %s: %d carriage-return byte(s) - CRLF or lone "
                "CR in a markdown doc breaks POSIX tooling and "
                "pollutes diffs; the repo policy is LF "
                "(.gitattributes eol=lf)" % (rel, n_cr))
        if not data.endswith(NL):
            findings.append(
                "LE-02 %s: missing final newline - every non-empty "
                "doc ends with a newline (POSIX hygiene, avoids "
                "\"No newline at end of file\" diff noise)" % rel)
    for f in findings:
        print("  " + f)
    print("line_ending_scan: %d docs scanned byte-level; %d docs "
          "carry CR; %d LE findings - hard (LE-01 no carriage-return "
          "byte, LE-02 final newline; born tick-490 born-at-zero "
          "after the 120-file worktree renorm + 2 final-newline "
          "fixes; committed content already 100%% LF via "
          ".gitattributes; byte-level by design - the text-mode "
          "fleet is structurally blind to this axis; see docstring)"
          % (n_docs, n_crlf, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
