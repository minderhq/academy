#!/usr/bin/env python3
"""legacy typing-idiom gate for the PROJECT-OMEGA curriculum.

Flags typing-module legacy spellings inside ```python fences - the same
surface the PEP 585/604 modernization epic drained (typing epic /1-/3).
A finding means the lesson teaches a deprecated import-based generic or
Optional/Union instead of the builtin-generic / PEP 604 union idiom that
has been standard since Python 3.9/3.10.

TL-01  legacy typing spelling in a ```python fence
       (Optional[ | Union[ | List[ | Dict[ | Tuple[ | Set[ |
       FrozenSet[ | Type[)

TL-02  legacy typing IMPORT line - `from typing import Dict` (or any
       of the same names) inside a python fence. TL-01's bracket
       pattern never saw the import itself, so a fence could teach
       the deprecated import while the gate stayed green - found in
       tick-376 while draining 7102, whose fences mixed modern
       `list[str]` with a bare `-> Dict`. Census: 139 import lines
       in 59 files; the typing epic /1-/3 fixed 62 files in phases
       1-3, and these live mostly in phase4-7 lessons, labs and
       practice assessments. Report queue: drain per batch, then
       promote to hard (the census->drain->gate pattern).

TL-03  bare/positional legacy generic - the same legacy names used
       WITHOUT a type parameter: `-> Dict`, `: Dict`, `list[Dict]`,
       `dict[str, Dict]`, optionally via `typing.Dict`. Equally
       invisible to TL-01's bracket pattern. Census: 426 in 63
       files. Report queue alongside TL-02. Import lines are
       checked first (TL-02) so a multi-name import is not
       double-counted as a positional use.

Blind spots (out of gate scope, matching the fixer's design): string and
comment tokens are NOT exempted here - a legacy spelling inside a
docstring or comment also teaches the old idiom, so it is a finding.
Content inside 4-backtick super-fences is invisible to the line-based
fence model (deliberate: it is teaching material about the syntax
itself, e.g. 2301).

Hard gate on ALL of TL-01/02/03 (exit 1). TL-01 baseline 0 since
the PEP 585/604 modernization epic drained (typing /1-/3). TL-02
and TL-03 were report inventory at birth (tick-376: 139 import
lines / 426 bare uses corpus-wide), drained per batch under the
census->drain->gate pattern, and promoted to hard at tick-397
once the final 7-file sweep (tick-396, 19776b6) took both queues
to zero. Any regression now fails the gate. Run over the whole
corpus:
    python scripts/qa/typing_legacy_scan.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")
LEGACY_RE = re.compile(r"\b(Optional|Union|List|Dict|Tuple|Set|FrozenSet|Type)\[")
TYPE_NAMES = r"(?:Optional|Union|List|Dict|Tuple|Set|FrozenSet|Type)"
IMPORT_RE = re.compile(rf"^\s*from\s+typing\s+import\s+.*\b{TYPE_NAMES}\b")
BARE_RE = re.compile(
    rf"(->\s*(?:typing\.)?{TYPE_NAMES}\b"
    rf"|:\s*(?:typing\.)?{TYPE_NAMES}\b"
    rf"|[(,]\s*(?:typing\.)?{TYPE_NAMES}\b"
    rf"|\[\s*(?:typing\.)?{TYPE_NAMES}\b"
    rf"|,\s*(?:typing\.)?{TYPE_NAMES}\b)")


def lint_file(root: Path, path: Path, findings: list[str], total: list[int]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")
    in_fence = False
    lang = ""
    for i, raw in enumerate(lines):
        m = FENCE_RE.match(raw)
        if m:
            in_fence = not in_fence
            lang = "" if not in_fence else m.group(2).lower()
            continue
        if lang != "python":
            continue
        if IMPORT_RE.search(raw):
            total[1] += 1
            findings.append(
                f"{rel}:{i + 1}: TL-02 legacy typing import - {raw.strip()[:100]}"
            )
            continue
        if LEGACY_RE.search(raw):
            total[0] += 1
            findings.append(
                f"{rel}:{i + 1}: TL-01 legacy typing spelling - {raw.strip()[:100]}"
            )
            continue
        if BARE_RE.search(raw):
            total[2] += 1
            findings.append(
                f"{rel}:{i + 1}: TL-03 bare legacy generic - {raw.strip()[:100]}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    total = [0, 0, 0]
    for path in sorted(docs.rglob("*.md")):
        try:
            lint_file(args.root, path, findings, total)
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    n_files = len({f.split(":", 1)[0] for f in findings})
    n01, n02, n03 = total
    print(f"typing_legacy_scan: {n01} TL-01, {n02} TL-02 and {n03} "
          f"TL-03 hard findings (exit 1; TL-02/03 promoted from report "
          f"queues at tick-397) in {n_files} files across docs/ "
          f"({sum(total)} python-fence lines matched)")
    return 1 if (n01 or n02 or n03) else 0


if __name__ == "__main__":
    sys.exit(main())
