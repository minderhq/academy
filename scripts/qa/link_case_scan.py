#!/usr/bin/env python3
"""Link case-sensitivity portability (LC-01, HARD) for PROJECT-OMEGA.

linkcheck and anchor_check resolve internal link targets with
os.path.exists, which is CASE-INSENSITIVE on the Windows machine
this repo is authored on - but the hosting platform (Linux) is
CASE-SENSITIVE. A link written as `./Guide-Career.md` against file
`GUIDE-CAREER.md` is invisible to every local gate and breaks only
when the platform serves it. This gate resolves every internal
link path segment-exactly against real directory entries, so
casing must match byte-for-byte.

LC-01  every internal markdown link target (outside fences,
       inline code scrubbed) must resolve with exact casing, one
       path segment at a time. Fragments are exempt (GitHub
       sluggers lowercase anchors); %20 is decoded before
       resolution, matching linkcheck.

Born tick-463 at 0: birth census over 3015 docs/ links (3325
repo-wide) found zero case-mismatches - the hypothesis that
Windows-tolerant casing had crept in died at measurement. The
gate locks the property so a future file rename (e.g. Guide-X ->
GUIDE-X) cannot silently strand links that stay green on the
authoring machine.

Run over the whole corpus:
    python scripts/qa/link_case_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INLINE_CODE = re.compile(r"`[^`]+`")
FENCE = re.compile(r"^\s*(```|~~~)")
FM_CLOSE = re.compile(r"^---\s*$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def body_lines(text: str) -> list[str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return lines
    for i, ln in enumerate(lines[1:40], 1):
        if FM_CLOSE.match(ln):
            return lines[i + 1:]
    return lines


def case_mismatch(src: Path, target: str) -> str | None:
    """Return the actual-cased first offending segment, or None."""
    pp = target.split("#", 1)[0].replace("%20", " ")
    if not pp:
        return None
    cur = src.parent
    for seg in pp.split("/"):
        if seg in (".", ""):
            continue
        if seg == "..":
            cur = cur.parent
            continue
        try:
            entries = os.listdir(cur)
        except OSError:
            return None  # unresolvable target is linkcheck's finding
        if seg not in entries:
            for e in entries:
                if e.lower() == seg.lower():
                    return e  # resolves only case-insensitively
            return None
        cur = cur / seg
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_links = n_docs = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(args.root).as_posix()
        infence = False
        for i, ln in enumerate(body_lines(text), 1):
            if FENCE.match(ln.strip()):
                infence = not infence
                continue
            if infence:
                continue
            for m in MD_LINK.finditer(INLINE_CODE.sub("", ln)):
                target = m.group(1)
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                n_links += 1
                alt = case_mismatch(path, target)
                if alt:
                    findings.append(
                        "LC-01 %s:%d `%s` (actual: `%s`)"
                        % (rel, i, target, alt))
        n_docs += 1
    for f in findings:
        print("  " + esc(f))
    print("link_case_scan: %d internal links in %d docs scanned; "
          "%d LC findings - all hard (segment-exact casing, "
          "platform-portable; born tick-463 at 0 across 3015 links)"
          % (n_links, n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
