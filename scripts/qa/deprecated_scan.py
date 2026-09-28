#!/usr/bin/env python3
"""deprecated-API gate for the PROJECT-OMEGA corpus.

DA-01  a ```python fence must not call ``datetime.utcnow()`` or
       ``datetime.utcfromtimestamp()``. Both are deprecated since
       Python 3.12 (the corpus stack is 3.13) and return naive
       datetimes - the modern idiom is the timezone-aware
       ``datetime.now(timezone.utc)``. Naive ``utcnow().timestamp()``
       is worse than deprecated: it silently interprets the value in
       the local timezone. The drained corpus also shows why the naive
       pattern hurts pedagogy: ``isoformat() + "Z"`` produced a
       double suffix once the aware form carries its own ``+00:00``.

Comment-only mentions (a fence teaching that utcnow is deprecated,
like the 2303 API-design lesson) are not findings: the check looks
for the call position before any ``#`` on the line.

Hard gate (exit 1 on findings): baseline 0 after the tick-227 drain
(13 call sites across 7 files moved to ``datetime.now(timezone.utc)``).

Run over the whole corpus:
    python scripts/qa/deprecated_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")
CALL_RE = re.compile(
    r"\bdatetime\.utcnow\b|\bdatetime\.utcfromtimestamp\b")


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    in_fence = False
    lang = ""
    start = 0
    for ln, raw in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            lang = "" if not in_fence else FENCE_RE.match(raw).group(2).lower()
            start = ln if in_fence else 0
            continue
        if in_fence and lang == "python":
            code = raw.split("#", 1)[0]
            if CALL_RE.search(code):
                findings.append(
                    f"{rel}:{ln}: DA-01 deprecated datetime API "
                    f"(since Python 3.12) - use "
                    f"datetime.now(timezone.utc); opened at line {start}")


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
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"deprecated_scan: {len(findings)} findings "
          f"(DA-01 datetime.utcnow/utcfromtimestamp) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
