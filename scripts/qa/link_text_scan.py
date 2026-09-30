#!/usr/bin/env python3
"""Link text quality (LT-01, HARD) for PROJECT-OMEGA.

The platform renders nav links verbatim; an intra-doc link's text
should match the plain-text canon its target heading already obeys
(HS-04/HS-05):

LT-01  no emoji in intra-doc link text - internal targets are
       corpus headings, which are emoji-free, so an emoji link
       label is by construction a mismatch with what the reader
       finds at the anchor (screen readers read the glyph name
       aloud; the platform TOC generator copies labels verbatim).

Scope notes, so the gate stays narrow and honest:
- external links are OUT: a brand glyph in `[hugging-face-emoji
  Hugging Face](https://...)` is legitimate labeling, and external
  targets carry no corpus canon to mismatch against
- vague link text (here/click here/link) is OUT, triaged ACCEPT at
  whitespace_scan's birth census: every weak-text site in the
  corpus is a deliberate `INCORRECT:`/`Bad:` teaching example
  inside a fence or inline code in the style guides (STYLE-GUIDE,
  NAVIGATION-TEMPLATE, CROSS-REFERENCE-GUIDELINES) - gating it
  would fence off the very lessons that teach the rule
- link target resolution is anchor_check's contract; this scan
  only reads the text between the brackets

Scan is fence-aware and starts after the front-matter block.

Born tick-488, born-at-zero after the 12-link drain (LEARNING-PATH
x7, VOLUME-6 x2, VOLUME-7 x3 - nav rows whose emoji prefix
survived tick-486 because that drain only stripped link text when
the target carried the leading-hyphen emoji-slug form).

Run over the whole corpus:
    python scripts/qa/link_text_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(```|~~~)")
FM_CLOSE = re.compile(r"^---\s*$")
INTRA = re.compile(r"\[([^\]]+)\]\(#[^)\s]*\)")
# Same class as heading_scan's HS-04/HS-05: U+2100-2BFF symbols,
# VS16/ZWJ joiners, SMP block. Typographic arrows are prose.
EMOJI = re.compile(r"[\u2100-\u2BFF\uFE0F\u200d\U0001F000-\U0001FAFF]")
TYPO_ARROWS = "".join(chr(c) for c in range(0x2190, 0x2196))


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
    n_links = 0
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
            for m in INTRA.finditer(ln):
                n_links += 1
                label = m.group(1)
                probe = "".join(ch for ch in label
                                if ch not in TYPO_ARROWS)
                if EMOJI.search(probe):
                    findings.append(
                        "LT-01 %s: emoji in intra-doc link text "
                        "`%s` - nav labels are plain text like "
                        "their targets (HS-04/05 canon)"
                        % (rel, esc(label[:50])))
    for f in findings:
        print("  " + f)
    print("link_text_scan: %d docs scanned, %d intra-doc links; "
          "%d LT findings - hard (LT-01 no emoji in intra-doc link "
          "text; born tick-488 born-at-zero after the 12-link "
          "drain; vague link text triaged ACCEPT - teaching "
          "examples, see docstring)"
          % (n_docs, n_links, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
