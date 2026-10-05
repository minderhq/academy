#!/usr/bin/env python3
"""fence-label gate for the Minder Academy corpus.

FL-01  an open fence's info-string carries an uppercase letter
       (``Python``, ``BASH``): the code gates (codeblock_syntax_scan,
       typing_legacy_scan, deprecated_scan, kwarg_lint,
       version_alignment_scan, langchain_census) key on the exact
       lowercase label, so a case variant is code that every gate
       silently skips - an audit hole, not a style nit.

FL-02  an open fence carries no label at all: the corpus convention
       is that every fence carries an honest label (``text`` is
       always legitimate for prose dumps and transcripts); an
       unlabeled fence is invisible to the same gate family.

Born from the tick-280 census: 4243 open fences across docs/, 21
distinct labels, every one already lowercase and labeled (python x1859,
text x1130, bash x725, yaml x289, then highlight-language labels down
to c x1) - zero case clashes, zero unlabeled opens. The census also
found the corpus's only blockquote-prefixed fence (notebooks/README.md
``> ```python``), which is why this gate uses the blockquote-aware
family model below rather than structure_lint's bare one.

Fence model: the shared family idiom (unfinished_marker_scan /
empty_section_scan / emoji_shortcode_scan) - length-aware ticks, ">"
blockquote prefix, frontmatter skipped. tick-689 lands the tick-678
CommonMark canon on top: tilde openers join, the state carries
(fence char, run) so a different fence character never closes, and
the closer rule stays CommonMark (same character, run at least as
long, empty info string) - a labeled marker inside an open fence is
fence content, never a toggle. Interior fence lookalikes inside
4-backtick super-fences are invisible by design.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-280).

Run over the whole corpus:
    python scripts/qa/fence_label_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Shared family idiom: length-aware ticks + blockquote prefix.
# tick-689 lands the tick-678 CommonMark canon: tilde openers join,
# the state carries (fence char, run) instead of a bare run, and a
# true closer repeats the opener CHARACTER in a run at least as long
# (a different fence character never closes); the blockquote prefix
# and the CommonMark empty-label closer rule are kept.
FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")


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

    state: tuple[str, int] | None = None  # (fence char, run), None = none
    for ln, raw in enumerate(lines[start:], start + 1):
        m = FENCE_RE.match(raw)
        if not m:
            continue
        marker, label = m.group(1), m.group(2)
        ch, run = marker[0], len(marker)
        if state:
            # true closer: same character, run at least as long, and an
            # empty info string (CommonMark closing fences carry no
            # label - the gate's own canon since tick-280); a labeled
            # marker inside a fence is fence content, never a toggle.
            if ch == state[0] and run >= state[1] and not label:
                state = None
        else:
            state = (ch, run)
            if not label:
                findings.append(
                    f"{rel}:{ln}: FL-02 unlabeled code fence; "
                    f"every fence carries an honest label "
                    f"('text' is always legitimate)")
            elif any(c.isupper() for c in label):
                findings.append(
                    f"{rel}:{ln}: FL-01 uppercase in fence label "
                    f"'{label}'; code gates key on the exact "
                    f"lowercase label - use '{label.lower()}'")


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
    print(f"fence_label_scan: {len(findings)} findings "
          f"(FL-01 uppercase fence label / FL-02 unlabeled fence; every "
          f"open fence carries a lowercase honest label) in "
          f"{len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
