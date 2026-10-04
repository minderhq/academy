#!/usr/bin/env python3
"""Heading skeleton soundness (HS-01..05, HARD) for Minder Academy.

The platform renders a TOC and anchor deep-links from heading
structure, so the skeleton every doc carries must be sound:

HS-01  no level skip: a heading may nest at most one level under
       its parent (H2 -> H4 breaks TOC trees and a11y outlines;
       the first heading of a doc is exempt - title/H1 parity is
       title_h1_parity_scan's contract)
HS-02  no empty heading text (`## ` with nothing to render)
HS-03  every doc carries at least one H2 - a flat body has no TOC
       tree at all
HS-04  no emoji-led heading - structure headings are plain text
       (tick-482 canon; labs drained tick-485, the rest of the
       corpus tick-486). Typographic arrows (left/right/up/down
       arrows) are prose, not emoji, and stay legal anywhere in a
       heading.
HS-05  no emoji anywhere inside a heading (positions after the
       lead). The tick-487 census measured the non-LED surface at
       exactly 2 headers - a trailing `* NEW` badge on the
       LEARNING-PATH Phase 0 row (with its double-hyphen ToC
       anchor, rewritten in the same drain) and a brand glyph in
       3202's `Using * Datasets`, renamed to spell the brand out.
       Emoji inside a fence (diagram boxes, code comments) is body
       texture, not heading structure, and stays out of scope.

Scan is fence-aware and starts after the front-matter block
(FS-01 guarantees it closes within 40 lines).

Born tick-459 at 0/0/0 across 408 docs (KW-03 pattern - prophylactic,
no drain). The birth census also measured 245 duplicate heading
texts across 30 docs (Task/Requirements/Pros/Cons template repeats
under per-item parents: exercises, database columns, case studies).
That class is triaged ACCEPT, deliberately not gated: the repeats
are hierarchical-correct (each sits under its own item parent),
anchor slugs dedup deterministically, and every internal link that
targets one is verified by the anchor gate - renaming would be
churn against a legitimate pattern.
HS-04 born tick-486, born-at-zero after the 558-header drain
(554 in the first pass, 4 in the patch pass after the v1 emoji
class missed the U+2100-2BFF symbols: keyboard, undo-arrow,
down-arrow, star; their 40 `#-` anchor links were rewritten in the
same drain - anchor_check's slugger removes emoji, so `## e Title`
anchors as `#-title` pre-drain and `#title` post-drain).

Run over the whole corpus:
    python scripts/qa/heading_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(```|~~~)")  # CommonMark: <=3 leading spaces
HEADING = re.compile(r"^(#{1,6})(?:\s+(.*))?$")
FM_CLOSE = re.compile(r"^---\s*$")

# HS-04: emoji-led headings are banned (tick-482 canon, corpus
# drain tick-486). Class spans U+2100-2BFF (the tick-486 v1 drain
# missed U+2328 keyboard, U+21A9 undo, U+2B07 down-arrow, U+2B50
# star), VS16/ZWJ joiners, and U+1F000-1FAFF; U+2600-27BF is
# subsumed by 2100-2BFF. Typographic arrows U+2190-2195 are prose
# and stay legal - excluded at the check, not in the class.
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
    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(args.root).as_posix()
        n_docs += 1
        infence = False
        prev = 0
        n_h2 = 0
        for ln in body_lines(text):
            if FENCE.match(ln):
                infence = not infence
                continue
            if infence:
                continue
            m = HEADING.match(ln)
            if not m:
                continue
            lvl = len(m.group(1))
            txt = (m.group(2) or "").strip().rstrip("#").strip()
            if not txt:
                findings.append("HS-02 %s: empty heading (`%s`)"
                                % (rel, ln.strip()))
                continue
            hs04 = txt[0] not in TYPO_ARROWS and bool(EMOJI.match(txt))
            if hs04:
                findings.append("HS-04 %s: emoji-led heading `%s` - "
                                "structure headings are plain text "
                                "(tick-482 canon)" % (rel, esc(txt[:40])))
            elif EMOJI.search("".join(ch for ch in txt[1:]
                                      if ch not in TYPO_ARROWS)):
                findings.append("HS-05 %s: emoji inside heading `%s` - "
                                "structure headings are plain text "
                                "(tick-482 canon, drained tick-487)"
                                % (rel, esc(txt[:40])))
            if prev and lvl > prev + 1:
                findings.append(
                    "HS-01 %s: level skip H%d -> H%d after %r"
                    % (rel, prev, lvl, txt[:40]))
            if lvl == 2:
                n_h2 += 1
            prev = lvl
        if n_h2 == 0:
            findings.append("HS-03 %s: no H2 in body (flat doc)" % rel)
    for f in findings:
        print("  " + esc(f))
    print("heading_scan: %d docs scanned; %d HS findings - all hard "
          "(skeleton soundness: no level skip, no empty heading, "
          "no flat body, no emoji in heading; born tick-459 at "
          "0/0/0, KW-03; HS-04 tick-486 after the 558-header drain; "
          "HS-05 tick-487 after the 2-header drain; "
          "duplicate-heading template repeats triaged ACCEPT - see "
          "docstring)"
          % (n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
