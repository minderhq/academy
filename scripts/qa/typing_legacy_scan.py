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

Blind spots (out of gate scope, matching the fixer's design): string and
comment tokens are NOT exempted here - a legacy spelling inside a
docstring or comment also teaches the old idiom, so it is a finding.
Content inside 4-backtick super-fences is invisible to the line-based
fence model (deliberate: it is teaching material about the syntax
itself, e.g. 2301).

Exit 0 when zero findings; exit 1 otherwise. Run over the whole corpus:
    python scripts/qa/typing_legacy_scan.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")
LEGACY_RE = re.compile(r"\b(Optional|Union|List|Dict|Tuple|Set|FrozenSet|Type)\[")


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
        if lang != "python" or not LEGACY_RE.search(raw):
            continue
        total[0] += 1
        findings.append(
            f"{rel}:{i + 1}: TL-01 legacy typing spelling - {raw.strip()[:100]}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    total = [0]
    for path in sorted(docs.rglob("*.md")):
        try:
            lint_file(args.root, path, findings, total)
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    n_files = len({f.split(":", 1)[0] for f in findings})
    print(f"typing_legacy_scan: {len(findings)} legacy spellings in {n_files} files "
          f"across docs/ ({total[0]} python-fence lines matched)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
