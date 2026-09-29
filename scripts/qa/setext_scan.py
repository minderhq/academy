#!/usr/bin/env python3
"""setext/divider gate for the PROJECT-OMEGA corpus.

SE-01  a bare ``---``/``===`` run sits directly below a non-blank
       line. Under text that is a setext H2/H1 in every renderer -
       invisible to structure_lint (ATX-only H1 discipline) and
       empty_section_scan (HEAD_ALL), so the silently-created heading
       escapes the outline, TOC and platform nav tree. Under another
       divider it is the doubled-HR render glitch (two stacked
       horizontal rules). The corpus idiom: blank line above every
       divider, ATX (``# ``) for headings.

SE-02  a bare ``===`` run anywhere: it is not a thematic break (only
       ``***``/``---``/``___`` are), so it renders as literal text -
       and the setext reading is banned in favor of the ATX idiom.

SE-03  a thematic break in a non-``---`` form (``***``, ``___``, or
       the spaced ``- - -``/``* * *``): the tick-281 census measured
       the divider idiom as ``---`` exclusively (3008 of 3008),
       so the lock keeps one form corpus-wide.

Born from the tick-281 census: 3008 ``---`` dividers, 3001 with the
blank line above, 7 doubled (``---`` directly under ``---``) - every
one the same copy-paste artifact of the footer-nav template
("- Return to: Module README" block) across 7 files. Fixed by
deleting the duplicate line; 0 latent setext headings, 0 ``===``.

Fence model: the shared family idiom (unfinished_marker_scan /
empty_section_scan / emoji_shortcode_scan / fence_label_scan) -
length-aware ticks, ">" blockquote prefix, frontmatter skipped.
Table separator rows (leading ``|``) and single-dash list bullets
never match.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-281).

Run over the whole corpus:
    python scripts/qa/setext_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Shared family idiom: length-aware ticks + blockquote prefix.
FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")

# Bare underline runs (2+ so single-dash list bullets never match).
UNDERLINE_RE = re.compile(r"^\s*(?:>\s*)?(-{2,}|={2,})\s*$")
# Thematic breaks in a non-'---' form.
OTHER_HR_RE = re.compile(r"^\s*(?:>\s*)?(\*(?:\s*\*){2,}|_(?:\s*_){2,}|-(?:\s+-){2,})\s*$")


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except (UnicodeDecodeError, OSError):
        return
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break

    state = 0  # backtick run length of the open fence, 0 = none
    prev = ""  # previous line outside fences
    for ln, raw in enumerate(lines[start:], start + 1):
        m = FENCE_RE.match(raw)
        if m:
            ticks, lang = len(m.group(1)), m.group(2)
            if state and not lang and ticks >= state:
                state = 0
            elif not state:
                state = ticks
            prev = raw
            continue
        if state:
            prev = ""
            continue
        um = UNDERLINE_RE.match(raw)
        if um and um.group(1)[0] == "=":
            if prev.strip():
                findings.append(
                    f"{rel}:{ln}: SE-01 setext H1 underline under text "
                    f"'{prev.strip()[:40]}' renders as a heading the "
                    f"outline gates cannot see; use the ATX idiom")
            else:
                findings.append(
                    f"{rel}:{ln}: SE-02 bare '===' run is not a "
                    f"thematic break - it renders as literal text; "
                    f"use the '---' divider or the ATX idiom")
        elif um and prev.strip():
            findings.append(
                f"{rel}:{ln}: SE-01 '---' run directly below a "
                f"non-blank line (setext H2 or doubled divider); "
                f"put a blank line above every divider")
        elif OTHER_HR_RE.match(raw):
            findings.append(
                f"{rel}:{ln}: SE-03 thematic break in a non-'---' "
                f"form; the corpus divider idiom is '---' exclusively")
        prev = raw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []
    n_files: set[str] = set()
    for path in sorted((args.root / "docs").rglob("*.md")):
        before = len(findings)
        scan_file(args.root, path, findings)
        if len(findings) > before:
            n_files.add(path.relative_to(args.root).as_posix())
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"setext_scan: {len(findings)} findings "
          f"(SE-01 latent setext under non-blank line / SE-02 bare '===' "
          f"/ SE-03 non-'---' thematic break; blank line above every "
          f"divider, ATX for headings) in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
