#!/usr/bin/env python3
"""Whitespace and invisible-character hygiene gate for the corpus.

UW-01  an invisible or control character (zero-width space/joiner/
       non-joiner, word joiner, figure/narrow no-break space,
       non-breaking space, mid-file BOM, line/paragraph separator,
       or any C0 control other than tab/CR/LF) anywhere in a
       docs/*.md file. These arrive by copy-paste from rich editors,
       are invisible in every viewer, and in code fences they become
       runtime bugs (an NBSP inside a Python string compiles fine
       and then poisons the learner's output).
UW-02  real trailing whitespace on a non-empty line (CR-normalized).
       Markdown's one legit use - exactly two trailing spaces as a
       hard break - is not used by this corpus (verified at gate
       birth), so every hit is debris. Trailing whitespace inside
       code fences also leaks into copied examples.
UW-03  mixed line endings inside one file (both CRLF and bare LF).
       Windows working copies hold many pure-CRLF files (git
       normalizes on commit), which is fine; MIXED endings mean the
       file was edited with inconsistent tooling and will churn in
       diffs forever.

Born from the tick-371 census: 408 files scanned - invisible chars
0, mixed EOL 0, real trailing whitespace exactly 1 line (a space
after a JSON fence line in 5204; fixed in the same tick). Baseline
0 at birth; the gate keeps the corpus on this side of clean.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-371).

Run over the whole corpus:
    python scripts/qa/unicode_ws_hygiene_scan.py --root .
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

INVISIBLE: dict[int, str] = {
    0x200B: "ZWSP",
    0x200C: "ZWNJ",
    0x200D: "ZWJ",
    0x2060: "WJ",
    0x00A0: "NBSP",
    0x2007: "FIGSP",
    0x202F: "NNBSP",
    0x2028: "LSEP",
    0x2029: "PSEP",
    0xFEFF: "BOM",
}


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    raw = path.read_bytes()
    crlf = raw.count(b"\r\n")
    bare_lf = raw.count(b"\n") - crlf
    if crlf and bare_lf:
        findings.append(
            f"{rel}:0: UW-03 mixed line endings (crlf={crlf}, "
            f"bare lf={bare_lf}) - pick one and normalize the file"
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return
    for pos, ch in enumerate(text):
        cp = ord(ch)
        named = INVISIBLE.get(cp)
        if named and not (cp == 0xFEFF and pos == 0):
            findings.append(
                f"{rel}:{text.count(chr(10), 0, pos) + 1}: UW-01 "
                f"invisible character {named} (U+{cp:04X}) - remove "
                f"it or encode the intent visibly"
            )
        elif cp < 0x20 and cp not in (0x09, 0x0A, 0x0D):
            findings.append(
                f"{rel}:{text.count(chr(10), 0, pos) + 1}: UW-01 "
                f"control character U+{cp:04X} - remove it"
            )
    for ln, line in enumerate(text.split("\n"), 1):
        line = line.rstrip("\r")
        if line != line.rstrip() and line.strip():
            findings.append(
                f"{rel}:{ln}: UW-02 trailing whitespace - strip it "
                f"(the corpus uses no hard-break double spaces)"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    n_files: set[str] = set()
    for path in sorted(docs.rglob("*.md")):
        try:
            before = len(findings)
            scan_file(args.root, path, findings)
            if len(findings) > before:
                n_files.add(path.relative_to(args.root).as_posix())
        except OSError:
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"unicode_ws_hygiene_scan: {len(findings)} findings "
          f"(UW-01 invisible/control char, UW-02 trailing "
          f"whitespace, UW-03 mixed line endings) in {len(n_files)} "
          f"files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
