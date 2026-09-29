#!/usr/bin/env python3
"""Lesson-id parity gate for the PROJECT-OMEGA corpus.

Every lesson document (``docs/phases/<phase>/<NNNN-module>/NNNN-*.md``,
114 files) carries its filename's own ``NNNN: `` id as the prefix of
both the frontmatter Title and the first ATX H1:

LI-01  the first H1 does not start with the filename's ``NNNN: `` id.
LI-02  the frontmatter Title does not start with the same id.

The id is the stable join key a platform needs: the manifest nav
label, quiz-bank membership and cross-references all key on it, and
a drifted prefix means the filename, the nav tree and the rendered
page quietly disagree about which lesson this is. tick-283 already
forced Title := H1 verbatim (title_h1_parity_scan), so the prefix
lives in both faces or neither - this gate locks the prefix itself
on top of that identity lock. resource_id_check is the same
discipline for the 43 family resources (LAB-000.., PROJECT-001..);
a missing H1 or Title altogether stays TH-02/TH-03's job.

Fence model: the shared family idiom (title_h1_parity_scan et al.);
frontmatter is the first ``---`` pair.

Born from the tick-287 census: 114/114 lesson docs carry the prefix
in both faces - locked at birth, baseline 0.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-287).

Run over the whole corpus:
    python scripts/qa/lesson_id_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Shared family idiom: length-aware ticks + blockquote prefix.
FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")
H1_RE = re.compile(r"^# (.+?)\s*$")
TITLE_RE = re.compile(r'^Title:\s*"?(.*?)"?\s*$')
PHASE_DIR = re.compile(r"^phase\d+-")
MODULE_DIR = re.compile(r"^\d{4}-")
LESSON_FILE = re.compile(r"^(\d{4})-.*\.md$")


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lid = LESSON_FILE.match(path.name).group(1)
    prefix = f"{lid}: "
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except (UnicodeDecodeError, OSError):
        return
    title = None
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
    h1 = None
    state = 0
    for raw in lines:
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
    if h1 is not None and not h1.startswith(prefix):
        findings.append(
            f"{rel}: LI-01 first H1 does not carry the filename id "
            f"'{prefix}' - nav tree, filename and rendered page "
            f"disagree about which lesson this is")
    if title is not None and not title.startswith(prefix):
        findings.append(
            f"{rel}: LI-02 frontmatter Title does not carry the "
            f"filename id '{prefix}' - manifest nav label loses the "
            f"lesson identity")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    phases = args.root / "docs" / "phases"
    findings: list[str] = []
    n_files: set[str] = set()
    n_lessons = 0
    for path in sorted(phases.glob(f"*/*")):
        if not (path.is_dir() and PHASE_DIR.match(path.parent.name)
                and MODULE_DIR.match(path.name)):
            continue
        for md in sorted(path.rglob("*.md")):
            if not LESSON_FILE.match(md.name):
                continue
            n_lessons += 1
            before = len(findings)
            scan_file(args.root, md, findings)
            if len(findings) > before:
                n_files.add(md.relative_to(args.root).as_posix())
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"lesson_id_scan: {len(findings)} findings "
          f"(LI-01 first H1 lacks the filename's NNNN id prefix / "
          f"LI-02 Title lacks it; the id is the stable platform join "
          f"key across filename, manifest nav and rendered page - "
          f"resource_id_check is the same discipline for the 43 "
          f"family resources) in {len(n_files)} of {n_lessons} "
          f"lesson docs across docs/phases/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
