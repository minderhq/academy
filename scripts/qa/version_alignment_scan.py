#!/usr/bin/env python3
"""python-version-alignment gate for the Minder Academy corpus.

The corpus standard is Python 3.13 (00-META/ENVIRONMENT-SETUP.md; the
installed stack runs 3.13). The tick-257 census proved the drift class
is real: one production Dockerfile inside a 4400-PRACTICE print-string
still shipped apt python3.10 on a CUDA 22.04 base after the 3.13 epic
was declared done - the epic's prose sweep never looked at code-side
artifacts. This gate locks that seam: code-side version references
inside ANY fence (bash, dockerfile, python print-strings, text, yaml -
drift lives exactly where the language label says "not Python") must
match the corpus standard.

  VA-01  ``FROM python:X.Y`` image tags
  VA-02  ``python3.X`` interpreter binaries
  VA-03  ``--python X.Y`` installer flags (uv venv / uv pip install)
  VA-04  ``uv python install|pin X.Y``

Anything other than 3.13 on these forms is a finding. Factual
version prose ("Python 3.5+", "deprecated since 3.12") stays legal:
it is prose outside fences, or two-word "Python X.Y" spelling that
none of these code forms match - the tick-257 census measured 0
such fence hits, so no allowlist is needed (an allowlist added
before the first finding would be speculation, not policy).

Hard gate (exit 1 on findings): baseline 0 after the tick-257 fix
(4400-PRACTICE deploy Dockerfile -> python:3.13-slim).

Run over the whole corpus:
    python scripts/qa/version_alignment_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")

STANDARD = "3.13"

# (code, pattern) - census-parity with the tick-257 measurement; the
# four code forms are where a runnable artifact pins an interpreter.
RULES = [
    (re.compile(r"\bFROM\s+python:(\d+\.\d+)", re.IGNORECASE), "VA-01"),
    # Capture the FULL version: a `python3\.(\d+)` shape grabs only the
    # minor digit, so the correct spelling `python3.13` would compare as
    # "13" != "3.13" - a false positive the probe control caught before
    # commit (same trap as the tick-257 throwaway census).
    (re.compile(r"\bpython(3\.\d+)\b"), "VA-02"),
    (re.compile(r"--python\s+(\d+\.\d+)\b"), "VA-03"),
    (re.compile(r"\buv\s+python\s+(?:install|pin)\s+(\d+\.\d+)"), "VA-04"),
]


def scan_file(root: Path, path: Path, findings: list[str], fences: list[int]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")
    in_fence, f_char, f_len = False, "", 0
    start = 0
    for ln, raw in enumerate(lines, 1):
        m = FENCE_RE.match(raw)
        if m:
            ch, n = m.group(1)[0], len(m.group(1))
            if in_fence and ch == f_char and n >= f_len:
                in_fence = False
                continue
            if not in_fence:
                in_fence = True
                f_char, f_len = ch, n
                start = ln
                fences[0] += 1
                continue
            # inner marker of a longer outer fence: fence CONTENT, falls
            # through to the rule scan below (tick-678 semantic)
        if not in_fence:
            continue
        for pat, code in RULES:
            for ver in pat.findall(raw):
                if ver != STANDARD:
                    findings.append(
                        f"{rel}:{ln}: {code} python-version drift: {ver} where "
                        f"the corpus standard is {STANDARD} "
                        f"(policy: 00-META/ENVIRONMENT-SETUP.md); "
                        f"fence opened at line {start}")
                    break


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    n_files: set[str] = set()
    fences = [0]
    for path in sorted(docs.rglob("*.md")):
        try:
            before = len(findings)
            scan_file(args.root, path, findings, fences)
            if len(findings) > before:
                n_files.add(path.relative_to(args.root).as_posix())
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"version_alignment_scan: {len(findings)} findings "
          f"in {len(n_files)} files, {fences[0]} fences scanned across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
