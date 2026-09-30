#!/usr/bin/env python3
"""Front-matter presence + standard fields (FS-01/02, all HARD).

Closes the coverage gates' blind spot: tags_coverage_check skips a
doc entirely when fm_tags() finds no FM block (None -> continue), so
a future doc committed WITHOUT front matter would be invisible to
TG/TS/TV - the gates cannot see what has no front matter. This gate
makes presence itself the contract.

FS-01  every docs/**/*.md must open with `---` on line 0 and close
       the block within the first 40 lines.
FS-02  the block must carry all six standard fields (Document ID,
       Title, Last Updated, Status, Difficulty, Tags) - the
       STYLE-GUIDE / ORGANIZATION-GUIDE Front Matter Standard set,
       each already value-gated elsewhere (lesson_id / title_h1 /
       last_updated / status_vocab / difficulty_census / TG+TV).
       Field-NAME variants pass the value gates of the canonical
       name and die here.

Born tick-457 at zero: the birth census measured 408/408 docs with
a closed FM block carrying all six fields - the hypothesis that
gaps existed was falsified (third measure-before-repair: V7 label
rot, cohort legacy markers, FM fields). Hard from birth, KW-03
pattern: the gate locks a clean state against future drift.

Run over the whole corpus:
    python scripts/qa/front_matter_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
FIELD_NAME = re.compile(r"^([A-Za-z][A-Za-z -]*):")
STANDARD_FIELDS = ("Document ID", "Title", "Last Updated", "Status",
                   "Difficulty", "Tags")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = n_ok = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        rel = path.relative_to(args.root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        n_docs += 1
        if not lines or not FM_OPEN.match(lines[0]):
            findings.append("FS-01 %s: no front matter block" % rel)
            continue
        close = None
        for i in range(1, min(len(lines), 40)):
            if FM_CLOSE.match(lines[i]):
                close = i
                break
        if close is None:
            findings.append("FS-01 %s: FM not closed in first 40 lines"
                            % rel)
            continue
        have = set()
        for ln in lines[1:close]:
            m = FIELD_NAME.match(ln)
            if m:
                have.add(m.group(1).strip())
        missing = [f for f in STANDARD_FIELDS if f not in have]
        if missing:
            findings.append("FS-02 %s: FM missing standard field(s): %s"
                            % (rel, ", ".join(missing)))
        else:
            n_ok += 1

    for f in findings:
        print("  " + esc(f))
    print("front_matter_scan: %d/%d docs have closed FM with all six "
          "standard fields; %d FS findings - all hard (FS-01 presence, "
          "FS-02 field set; born tick-457 at 408/408, closes the "
          "FM-less-doc blind spot the coverage gates skip on)"
          % (n_ok, n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
