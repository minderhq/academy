#!/usr/bin/env python3
"""title-uniqueness gate for the PROJECT-OMEGA corpus.

TU-01  the display-title space is global, like the Document ID space:
       no two markdown files under docs/ or experiments/ may carry the
       same FM Title, compared after trimming and case-folding (the
       catalog renders one row per doc keyed by Document ID with the
       Title as its display name - doc_id_check locks ID uniqueness so
       two files can never answer to one row; this locks the display
       side so two rows can never be indistinguishable to a learner
       searching or listing by name).

Scope notes:
  - Title PRESENCE is frontmatter_lint FM-03's duty and Title-vs-H1 is
    FM-09's - a file with no Title key is counted untitled here but
    never TU-01 (absence is never double-reported; the tick-609 HZ-03
    lesson).
  - experiments/TEMPLATE.md carries no exemption: EC-02's lesson was
    that TEMPLATE's exemption is name-keyed to EC-01 alone, and a
    template title copied onto a real file is exactly the duplicate a
    platform must not render.

Born from the tick-610 census: 456 FM carriers across docs/ (408) and
experiments/ (48), 456 distinct case-folded titles, 0 duplicate groups
- the corpus was born clean, the class froze at the rule, zero-drain.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
TITLE_FIELD = re.compile(r"^Title:\s*(.*)$")

TREES = ("docs", "experiments")


def read_fm_title(path: Path) -> str | None:
    """Return the file's FM Title, or None when absent/unparseable."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    except OSError:
        return None
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for line in lines[1:40]:
        if FM_CLOSE.match(line):
            return None
        m = TITLE_FIELD.match(line)
        if m:
            return m.group(1).strip()
    return None


def title_key(title: str) -> str:
    """Normalize a Title for the uniqueness comparison."""
    return re.sub(r"\s+", " ", title).casefold()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    findings: list[str] = []
    scanned = 0
    titled = 0
    groups: dict[str, list[str]] = {}
    for tree in TREES:
        base = root / tree
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            scanned += 1
            title = read_fm_title(path)
            if title is None:
                continue
            titled += 1
            groups.setdefault(title_key(title), []).append(
                path.relative_to(root).as_posix())

    # TU-01: one finding per extra file in a duplicate group.
    for key, rels in sorted(groups.items()):
        if len(rels) > 1:
            for rel in rels[1:]:
                findings.append(
                    f"TU-01  {rel}  duplicate display title "
                    f"(case-insensitive) shared with {rels[0]}: "
                    f"{[r for r in rels]}")

    distinct = len(groups)
    n = len(findings)
    for line in findings:
        print(line)
    print(
        f"title_uniqueness_scan: scanned={scanned} titled={titled} "
        f"distinct={distinct} TU-01={n} "
        "(hard gate; the display-title space is global like the "
        "Document ID space - doc_id_check locks ID uniqueness, this "
        "locks the catalog's display identity; Title presence is "
        "frontmatter_lint FM-03's duty, never double-reported here; "
        "experiments/TEMPLATE.md carries no uniqueness exemption "
        "(EC-02's lesson); born tick-610 at zero)")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
