#!/usr/bin/env python3
"""Difficulty field census (DI-01..DI-03) for Minder Academy.

Difficulty renders as a platform filter/sequence dimension, so
its vocabulary must be closed and its spelling exact. Tick-411
measured the corpus: 408 doc-id docs, all carrying the field,
name uniform, values 166 Advanced / 144 Intermediate / 93
Beginner / 5 Expert.

DI-01  Difficulty missing, empty, or a value outside the known
       vocabulary (canonical enum + drain list). HARD.
DI-02  field-name variant (canonical name is exactly
       "Difficulty:"; known alt names "Skill Level", "Level",
       "Complexity", "Difficulty Level" count as variants). HARD.
DI-03  value outside the canonical enum (Beginner/Intermediate/
       Advanced). HARD - drained tick-412: all 5 "Expert" sites
       (SOLUTION-LAB-011, 4401-GPTQ, 4402-AWQ, 4403-GGUF,
       4404-EXL2) canonicalized to Advanced, closing the
       vocabulary at exactly three levels.

HARD GATE - exit 1 on any finding. DI-01/DI-02 born at zero at
tick-411 (KW-03: 408/408 docs clean); DI-03 joined after the
tick-412 Expert drain (census -> drain -> gate cycle).

Run over the whole corpus:
    python scripts/qa/difficulty_census.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(?:---|\.\.\.)\s*$")
DIFF_FIELD = re.compile(r"^Difficulty:(.*)$")
ALT_NAME = re.compile(r"^(?:Skill[-_ ]Level|Level|Complexity|"
                      r"Difficulty[-_ ]Level):")
CANON = ("Beginner", "Intermediate", "Advanced")


def fm_block(lines: list[str]) -> list[str] | None:
    """Frontmatter block body (between the delimiters), or None."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            return lines[1:i]
    return lines[1:40]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    paths = sorted(docs.rglob("*.md"))

    findings: list[str] = []
    counts: Counter = Counter()
    values: Counter = Counter()
    n_docs = 0
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        block = fm_block(lines)
        if block is None:
            continue
        rel = path.relative_to(args.root).as_posix()
        n_docs += 1
        val = None
        for raw in block:
            m = DIFF_FIELD.match(raw)
            if m:
                val = m.group(1).strip()
                break
        if val is None:
            findings.append(f"{rel}: DI-01 Difficulty missing "
                            f"(every doc-id doc must carry it)")
            counts["DI-01"] += 1
        elif not val:
            findings.append(f"{rel}: DI-01 empty Difficulty value")
            counts["DI-01"] += 1
        elif val in CANON:
            values[val] += 1
        else:
            findings.append(f"{rel}: DI-03 non-canonical Difficulty "
                            f"{val!r} (canonical enum is Beginner/"
                            f"Intermediate/Advanced)")
            counts["DI-03"] += 1
            findings.append(f"{rel}: DI-01 unknown Difficulty value "
                            f"{val!r} (vocabulary is Beginner/"
                            f"Intermediate/Advanced)")
            counts["DI-01"] += 1
        for raw in block:
            m = ALT_NAME.match(raw)
            if m:
                findings.append(f"{rel}: DI-02 variant difficulty "
                                f"field name {m.group(0)!r} "
                                f"(canonical is Difficulty:)")
                counts["DI-02"] += 1

    di01 = counts["DI-01"]
    di02 = counts["DI-02"]
    di03 = counts["DI-03"]
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"difficulty_census: docs={n_docs} values={dict(values)} "
          f"DI-01={di01} DI-02={di02} DI-03={di03} "
          f"(hard gate; DI-03 drained tick-412, canonical enum "
          f"Beginner/Intermediate/Advanced)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
