#!/usr/bin/env python3
"""QA-script source hygiene (SH-01/02, HARD) - the fleet watches
its own tree.

Every other gate scans docs/; this one scans scripts/ - the
automation layer itself. Two rules, both born from real
incidents in this repo:

SH-01  every .py under scripts/ is pure ASCII. tick-488: the
       Write tool inserted literal emoji into link_text_scan.py's
       emoji class and the corruption was found only by a
       byte-level check. Escaped sources (\\uXXXX) cannot rot,
       survive any editor/toolchain, and are diff-stable on
       every platform.

SH-02  every .py compiles clean with SyntaxWarning-as-error.
       tick-490: quality_report.py carried a bare invalid escape
       (a docstring backslash) that warned on every run and
       becomes a hard SyntaxError in a future Python. Compile-
       time warnings are latent breakage - this gate refuses
       them today.

Scope: all *.py under scripts/, recursive (105 files at birth).
Docs are out - corpus text conventions are the other gates'
domain. Notebooks are out (JSON, different class).

Scan is whole-file byte-level (ASCII check) plus in-process
compile (warning check) - no subprocesses, no imports executed:
compile() never runs the module, so this gate cannot trigger
side effects of the scripts it inspects.

Born tick-491, born-at-zero after the drain: 26 replacements
across 10 files (literal emoji/box chars -> \\uXXXX escapes in
strings and one raw regex, docstring arrows/ellipses -> ASCII,
accented letters -> \\uXXXX, one doubled backslash in
quality_report.py), every runtime value proven unchanged.

Run over the whole tree:
    python scripts/qa/script_hygiene_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_scripts = 0
    for path in sorted((args.root / "scripts").rglob("*.py")):
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        rel = path.relative_to(args.root).as_posix()
        n_scripts += 1
        try:
            raw.decode("ascii")
        except UnicodeDecodeError as exc:
            findings.append(
                "SH-01 %s: non-ASCII byte in source at offset %d - "
                "keep sources pure ASCII, spell the character with a "
                "\\uXXXX escape (tick-488 lesson, see docstring)"
                % (rel, exc.start))
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("error", SyntaxWarning)
            try:
                compile(raw, rel, "exec")
            except SyntaxWarning as exc:
                findings.append(
                    "SH-02 %s: SyntaxWarning at compile - %s; fix the "
                    "escape/sequence now, it becomes a hard error in "
                    "a future Python (tick-490 lesson, see docstring)"
                    % (rel, exc))
            except SyntaxError as exc:
                findings.append(
                    "SH-02 %s: SyntaxError at compile - %s" % (rel, exc))
    for f in findings:
        print("  " + esc(f))
    print("script_hygiene_scan: %d scripts inspected; %d SH findings "
          "- hard (SH-01 pure-ASCII sources, SH-02 SyntaxWarning-free "
          "compile; born tick-491 born-at-zero after the 26-"
          "replacement drain across 10 files; the fleet watches its "
          "own tree; see docstring)"
          % (n_scripts, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
