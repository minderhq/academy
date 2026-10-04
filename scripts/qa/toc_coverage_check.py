#!/usr/bin/env python3
"""TOC completeness (TC-01) for Minder Academy.

A doc's Table of Contents becomes the platform's in-doc nav pane: a
real content section absent from the TOC is invisible in the doc's
own navigation, however prominent on the page. anchor_check proves
that listed anchors resolve; TC-01 proves nothing real is unlisted.

TC-01 (hard): every H2 heading outside frontmatter and code fences,
except the closing trio (Summary, References, Next Steps - the house
style keeps the trio's navigation tail out of the TOC), must appear
as a TOC bullet in the doc's "## Table of Contents" section. A
section counts as listed when a bullet's display text matches the
H2 text (whitespace-normalized) OR the bullet's href slug equals the
H2's GitHub slug - the nav pane needs the LINK to exist and resolve;
a "Part 1:" prefix or a stripped emoji in the display label is house
style, not a navigation hole (IND-00x "Part N" bullets and VOLUME
emoji-stripped bullets both resolve correctly).

Scope: every TOC-carrying doc under docs/ - the gate is
self-selecting; docs without a TOC are not its subject. Carrying a
TOC is opting into the completeness standard, genre regardless.

Birth census (2026-09-30): a NAIVE census (no fence tracking) found
2 "missing" H2s in 2301 - both turned out to be literal text inside
a ````python example block, i.e. not headings at all; anchor_check's
fence tracking was right. The fence-aware census measured 0 real
findings across the 93 TOC-carrying lessons: lessons born clean.
The first whole-corpus run listed 45 rows: 24 label mismatches
(industry "Part N" prefixes, volume emoji prefixes - resolved by the
slug-matching rule above, zero doc edits) + 21 genuine gaps (19
phase-README tail sections, 2 guide Abstracts) - all drained at
birth, hard since.

Run over the whole corpus:
    python scripts/qa/toc_coverage_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from anchor_check import gh_slug  # corpus-trusted slugger

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
FM = re.compile(r"^---\s*$")
HEADING = re.compile(r"^## (.+?)\s*$")
TOC_HEAD = re.compile(r"^## Table of Contents\s*$", re.I)
TOC_BULLET = re.compile(r"^- \[([^\]]+)\]\(#([^)]*)\)")
CLOSING = {"summary", "references", "next steps"}


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def collect(text: str):
    """Yield (is_toc_head, is_h2, line, inside_fence) line facts."""
    in_f, f_char, f_len = False, "", 0
    in_fm = text.startswith("---")
    fm_n = 0
    facts = []
    for ln in text.split("\n"):
        if in_fm:
            if FM.match(ln):
                fm_n += 1
                in_fm = fm_n != 2
            facts.append((False, False, "", in_f))
            continue
        m = FENCE.match(ln)
        if m:
            ch, n = m.group(1)[0], len(m.group(1))
            if in_f:
                if ch == f_char and n >= f_len:
                    in_f = False
            else:
                in_f = True
                f_char, f_len = ch, n
            facts.append((False, False, "", True))
            continue
        facts.append((bool(TOC_HEAD.match(ln)), not in_f and bool(
            HEADING.match(ln)), ln, in_f))
    return facts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    n_docs = 0
    n_h2 = 0
    findings: list[str] = []

    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        facts = collect(text)
        toc_idx = [i for i, (t, _, _, f) in enumerate(facts)
                   if t and not f]
        if not toc_idx:
            continue  # docs without a TOC are not this gate's subject
        toc_end = next((i for i in range(toc_idx[0] + 1, len(facts))
                        if facts[i][1] and not facts[i][3]), len(facts))
        texts: set[str] = set()
        hrefs: set[str] = set()
        for i in range(toc_idx[0] + 1, toc_end):
            m = TOC_BULLET.match(facts[i][2])
            if m:
                texts.add(norm(m.group(1)))
                hrefs.add(m.group(2).strip().lower())
        # deduped slugs of the doc's own H2s, in document order -
        # GitHub suffixes repeats with -1, -2; mirror that so a
        # repeated section's TOC bullet matches the right heading
        paired: list[tuple[str, str]] = []
        used: Counter[str] = Counter()
        for i in range(toc_end, len(facts)):
            _, is_h2, ln, in_f = facts[i]
            if not (is_h2 and not in_f):
                continue
            h = re.sub(r"\s+", " ",
                       HEADING.match(ln).group(1)).strip()
            if h.lower() in CLOSING:
                continue
            s = gh_slug(h)
            used[s] += 1
            paired.append((h, s if used[s] == 1
                           else f"{s}-{used[s] - 1}"))
        n_docs += 1
        n_h2 += len(paired)
        for h, s in paired:
            if norm(h) in texts or s in hrefs:
                continue
            rel = path.relative_to(args.root).as_posix()
            findings.append("TC-01 H2 %r not in TOC of %s" % (h, rel))

    print("toc_coverage_check: %d TOC-carrying docs, %d content H2 "
          "checked" % (n_docs, n_h2))
    for f in findings:
        print("  " + esc(f))
    print("toc_coverage_check: %d TC-01 findings - hard gate, whole "
          "corpus, born drained (census 2026-09-30: 45 rows = 24 label "
          "mismatches + 21 gaps, all resolved at birth)" % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
