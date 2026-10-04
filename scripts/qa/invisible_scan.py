#!/usr/bin/env python3
"""Invisible-character hygiene (IV-01, HARD) for Minder Academy.

Copy-paste is the classic silent-corruption vector: zero-width
characters and control characters pasted from web pages or rich
editors render as nothing, but they break exact-match search,
heading slug generation, copy-out of code samples, and diff
review. This scan makes them loud:

IV-01  no invisible/hazard character outside fences - zero-width
       space / non-joiner / word joiner, soft hyphen, no-break
       space (plain and narrow), BOM/zero-width no-break space
       anywhere, bidirectional controls, and stray control
       characters. Replace with a plain space or hyphen.

Exclusions, so the gate stays narrow and honest:
- ZWJ (U+200D) and VS16 (U+FE0F) are OUT of the hazard class:
  they are legal emoji composition per the tick-486 emoji canon
- in-fence content is OUT: code may legitimately discuss or embed
  such characters in a lesson about unicode pitfalls
- CRLF (U+000D) is OUT here: line-ending policy is a different
  class, and this repo is LF-normalized
- front matter is skipped, per the shared scan convention
- tab (U+0009) is legal indentation

Character classes are built with chr() so this source file stays
pure ASCII (the tick-488 lesson: literal non-ASCII in a source
file invites encoding drift).

Scan is fence-aware and starts after the front-matter block.

Born tick-489, born-at-zero: the birth census measured all 408
docs clean (zero invisible/hazard characters, fence-in or
fence-out) - the gate is prophylactic, KW-03 pattern, for the
platform era where contributors paste from the web.

Run over the whole corpus:
    python scripts/qa/invisible_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(```|~~~)")
FM_CLOSE = re.compile(r"^---\s*$")

# (label, character) pairs; labels name the codepoint so findings
# are actionable without printing the invisible character itself.
HAZARDS = [
    ("U+200B zero-width space", chr(0x200B)),
    ("U+200C zero-width non-joiner", chr(0x200C)),
    ("U+2060 word joiner", chr(0x2060)),
    ("U+00AD soft hyphen", chr(0x00AD)),
    ("U+00A0 no-break space", chr(0x00A0)),
    ("U+202F narrow no-break space", chr(0x202F)),
    ("U+FEFF BOM / zero-width no-break space", chr(0xFEFF)),
]
HAZARDS += [("U+%04X bidi control" % c, chr(c))
            for c in range(0x202A, 0x202F)]
HAZARDS += [("U+%04X bidi control" % c, chr(c))
            for c in range(0x2066, 0x206A)]
HAZARDS += [("U+%04X control character" % c, chr(c))
            for c in list(range(0x00, 0x09)) + [0x0B, 0x0C]
            + list(range(0x0E, 0x20)) + [0x7F]]


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    n_lines = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(args.root).as_posix()
        n_docs += 1
        infence = False
        for ln in body_lines(text):
            if FENCE.match(ln):
                infence = not infence
                continue
            if infence:
                continue
            n_lines += 1
            hits = [label for label, ch in HAZARDS if ch in ln]
            if hits:
                findings.append(
                    "IV-01 %s: invisible/hazard character(s) %s - "
                    "paste-in zero-width or control characters break "
                    "search, slugs and copy-out; use a plain space "
                    "or hyphen (see docstring)"
                    % (rel, esc(", ".join(hits[:4]))))
    for f in findings:
        print("  " + f)
    print("invisible_scan: %d docs scanned, %d body lines; "
          "%d IV findings - hard (IV-01 no invisible/hazard "
          "characters outside fences; born tick-489 born-at-zero - "
          "birth census measured all 408 docs clean; ZWJ/VS16 emoji "
          "joiners legal per the tick-486 class; in-fence is code "
          "content, out of scope; see docstring)"
          % (n_docs, n_lines, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
