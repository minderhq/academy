#!/usr/bin/env python3
"""Render hygiene (RH-01..04) for Minder Academy.

The platform renders every doc's markdown; four constructs render
poorly or not at all outside GitHub, and all four are deterministic:

RH-01 (hard): raw HTML tags outside code spans and fences. HTML in
markdown is sanitized or escaped by most platform renderers - what
GitHub shows as a collapsible <details> block renders as literal
"<details>" text elsewhere. The corpus standard is markdown-native
structure only.
RH-02 (hard): heading-level skips (h2 -> h4 with no h3). Platform
TOC trees are built from heading hierarchy; a skip produces a
dangling tree node. The first heading of a doc may be any level.
RH-03 (hard): bare URLs outside markdown links, autolinks, and code
spans. Unwrapped URLs render as plain text - not clickable, no
visited/active styling, inconsistent line breaking.
RH-04 (hard): images with empty alt text. Accessibility requirement
and screen-reader correctness (corpus currently carries zero images;
the gate protects the invariant against the first one).

Birth census (2026-09-30): 12 raw-HTML tags = 3 <details>/<summary>
Solution blocks in TUTORIAL-000 (drained to bold "**Solution:**"
labels same tick), 46 bare URLs across 16 docs (drained to
[url](url) self-links same tick), 0 heading skips, 0 images / 0
empty alts - all four hard from birth (KW-03).

Fence tracking (fixed tick-677): the toggle used to flip on every
3+-run marker line, so a nested 3-backtick inner fence inside a
4-backtick outer flipped parity mid-doc and the gate scanned the
inner fence's interior as prose - the tick-675 ML-01 drain left
UC-002's nested OAuth example carrying plain urls exactly there,
3 RH-03 findings at HEAD (masked in the tick-675/676 battery
batches because the loop captured tail's rc, not python's). The
tracker now follows the CommonMark fence lengths: a closer must
repeat the opener's character in a run at least as long, and a
different fence character never closes a backtick fence.

Run over the whole corpus:
    python scripts/qa/render_hygiene_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
FM = re.compile(r"^---\s*$")
HEADING = re.compile(r"^(#{1,6}) (.+?)\s*$")
CODE_SPAN = re.compile(r"`[^`]*`")
MD_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")
AUTO_LINK = re.compile(r"<https?://[^>]+>")
BARE_URL = re.compile(r"\bhttps?://[^\s)>\"'\]]+")
HTML_TAG = re.compile(r"<(/?[a-zA-Z][a-zA-Z0-9]*)(?:\s[^>]*)?>")
EMPTY_ALT = re.compile(r"!\[\s*\]\(")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    n_docs = 0
    findings: list[str] = []

    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(args.root).as_posix()
        n_docs += 1
        in_f = False
        f_char = f_len = 0
        in_fm = text.startswith("---")
        fm_n = 0
        prev_level = 0
        for i, ln in enumerate(text.split("\n"), 1):
            if in_fm:
                if FM.match(ln):
                    fm_n += 1
                    in_fm = fm_n != 2
                continue
            fm = FENCE.match(ln)
            if fm:
                run = fm.group(1)
                ch, n = run[0], len(run)
                if not in_f:
                    in_f, f_char, f_len = True, ch, n
                elif ch == f_char and n >= f_len:
                    in_f = False
                continue
            if in_f:
                continue
            clean = AUTO_LINK.sub("", MD_LINK.sub(
                "", CODE_SPAN.sub("", ln)))
            for m in HTML_TAG.finditer(clean):
                findings.append("RH-01 raw HTML <%s> %s:%d"
                                % (m.group(1), rel, i))
            if EMPTY_ALT.search(ln):
                findings.append("RH-04 empty image alt text %s:%d"
                                % (rel, i))
            for m in BARE_URL.finditer(clean):
                findings.append("RH-03 bare URL %s... %s:%d"
                                % (m.group(0)[:30], rel, i))
            m = HEADING.match(ln)
            if m:
                lvl = len(m.group(1))
                if prev_level and lvl > prev_level + 1:
                    findings.append("RH-02 heading skip h%d->h%d %s:%d"
                                    % (prev_level, lvl, rel, i))
                prev_level = lvl

    print("render_hygiene_check: %d docs scanned" % n_docs)
    for f in findings:
        print("  " + esc(f))
    print("render_hygiene_check: %d RH-01..04 findings - hard gate, "
          "born at zero (census 2026-09-30: 12 raw-HTML tags + 46 bare "
          "URLs drained, skips/alts born zero)" % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
