#!/usr/bin/env python3
"""Title/H1 parity gate for the PROJECT-OMEGA corpus.

TH-01  frontmatter Title differs from the first ATX H1 (fence-aware).
       The two strings are one fact with two faces: manifest_export
       takes the platform nav label from the frontmatter Title, while
       the rendered page title is the first H1 - any drift means the
       nav tree shows a different name than the page that opens. The
       corpus idiom (tick-283 census): identical verbatim, 408 of 408
       after the fix.

TH-02  no H1 at all: the rendered page has no title for the nav tree
       to link to.

TH-03  no frontmatter (or no Title line): manifest_export has no nav
       label at all.

Fix direction is Title := H1 verbatim - the H1 is what the learner
sees, and in lesson docs the ``NNNN: `` id prefix then lives in both
faces instead of only one.

Fence model: the shared family idiom (setext_scan et al.) - the first
H1 search is fence-aware so a ``# `` line inside an example fence
never wins. Frontmatter is the first ``---`` pair.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-283).

Run over the whole corpus:
    python scripts/qa/title_h1_parity_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Shared family idiom: length-aware ticks + blockquote prefix.
FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")
TITLE_RE = re.compile(r'^Title:\s*"?(.*?)"?\s*$')
H1_RE = re.compile(r"^# (.+?)\s*$")


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except (UnicodeDecodeError, OSError):
        return
    title = None
    start = 0
    if lines and lines[0].strip() == "---":
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is not None:
            for raw in lines[1:end]:
                tm = TITLE_RE.match(raw)
                if tm and title is None:
                    title = tm.group(1).strip()
            start = end + 1
    if title is None:
        findings.append(
            f"{rel}:1: TH-03 no frontmatter Title - manifest_export "
            f"has no nav label for this document")
        return
    h1 = None
    state = 0  # backtick run length of the open fence, 0 = none
    for raw in lines[start:]:
        m = FENCE_RE.match(raw)
        if m:
            ticks, lang = len(m.group(1)), m.group(2)
            if state and not lang and ticks >= state:
                state = 0
            elif not state:
                state = ticks
            continue
        if state:
            continue
        hm = H1_RE.match(raw)
        if hm:
            h1 = hm.group(1).strip()
            break
    if h1 is None:
        findings.append(
            f"{rel}:1: TH-02 no ATX H1 - the rendered page has no "
            f"title for the platform nav tree to link to")
    elif title != h1:
        findings.append(
            f"{rel}:1: TH-01 Title '{title[:40]}' != first H1 "
            f"'{h1[:40]}' - nav label and rendered page title diverge; "
            f"the fix is Title := H1 verbatim")


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
    print(f"title_h1_parity_scan: {len(findings)} findings "
          f"(TH-01 Title != first H1 / TH-02 no H1 / TH-03 no "
          f"frontmatter Title; manifest nav label and rendered page "
          f"title are one fact - Title := H1 verbatim) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
