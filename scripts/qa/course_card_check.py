#!/usr/bin/env python3
"""course_card_check - the module README course card must not lie about its lessons.

Every module directory carries a README whose front matter Difficulty is the
course card the platform will read as catalog metadata, and six module READMEs
additionally render a "Module Documents" table whose star and time cells are
the per-lesson display layer. Neither surface was gated, so 22 of 33 course
cards floated free of the lessons they summarize - born at commit 775f898's
"universal frontmatter migration" boilerplate and never reconciled: a
3100-attention card reading Beginner while both of its lessons are Advanced
is the course-catalog lie this corpus's own unlock-order law (PQ-07) kills one
level down.

CC-01  README FM Difficulty equals the max tier of its lessons' FM Difficulty
       (Beginner=1 / Intermediate=2 / Advanced=3, the FF-02-proven star map).
       Lessons = module-dir *.md minus README.md minus PREREQUISITES.md (the
       PREREQUISITES doc states entry expectations, not lesson content).
       Skipped when the README carries no FM Difficulty or no lesson carries an
       in-vocabulary tier - FV-07 owns the enum, this gate never double-reports
       another gate's finding.
CC-02  In a Module Documents table row whose target carries an in-vocabulary FM
       Difficulty, the star cell (>=1 U+2B50) must carry exactly TIER_STARS of
       the target tier; a starless cell - including word-form "Advanced" text -
       fires. Out-of-vocabulary or FM-less targets are skipped (FV-07 again).
CC-03  The row's duration cell equals the target FM Estimated Time, compared
       minute-exact (hours*60). When the table header promises a Time column,
       a row with no duration token at all fires (the LI-05 class: a promised
       display column cannot go silently empty); when the target carries no
       parseable FM time, the comparison is skipped.
CC-04  Every lesson basename is linked somewhere in the README (any link form,
       fence-aware) - the CI-01 class: a lesson that exists on disk but is
       invisible from its own module index.
CC-05  Where a Module Documents table exists, every lesson has a row in it
       (extra rows pointing at guides are tolerated display richness; only
       missing lessons fire). Modules without such a table are CC-04 territory.

The gate is order-agnostic about table columns (3500-multimodal renders Time
before Difficulty and both orders pass). Dead row targets are skipped here -
linkcheck owns them. Born tick-576 after a 35-finding drain (22 FM cards, 2
body badges that mirrored the drifted FM, 10 star cells, 2 time cells, 1
missing table row); the drain obeys the 11-of-33 modules that already satisfy
CC-01 - the contract is the curated majority's convention, not an invention.

Exit 1 on any finding; prints one line per finding.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path, PurePosixPath

TIER_STARS = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
FM_DASH = re.compile(r"^---\s*$")
DIFF_FIELD = re.compile(r"^Difficulty:(.*)$")
ET_FIELD = re.compile(r"^Estimated Time:(.*)$")
DUR = re.compile(r"(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|m|min|mins|minutes?)\b")
LINK = re.compile(r"\]\(([^)]+)\)")
TABLE_HEAD = re.compile(r"^#{1,3} .*Module Documents")
STAR = "\u2b50"  # U+2B50 - SH-01 keeps sources pure ASCII  # U+2B50, the FF-02 house escape - SH-01 keeps sources pure ASCII


def fm_fields(path: Path) -> dict | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or not FM_DASH.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_DASH.match(lines[i]):
            d: dict = {}
            for raw in lines[1:i]:
                m = DIFF_FIELD.match(raw)
                if m:
                    d["diff"] = m.group(1).strip()
                m = ET_FIELD.match(raw)
                if m:
                    d["et"] = m.group(1).strip()
            return d
    return None


def fm_minutes(et: str | None) -> float | None:
    if not et:
        return None
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*hours?", et)
    if m:
        return float(m.group(1)) * 60
    m = re.fullmatch(r"(\d+)\s*minutes?", et)
    if m:
        return float(m.group(1))
    return None


def unfenced_lines(text: str) -> list[str]:
    out, fenced = [], False
    for ln in text.splitlines():
        if ln.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append(ln)
    return out


def table_rows(lines: list[str]) -> tuple[list[list[str]], bool]:
    """Rows of the Module Documents table plus whether the header has Time."""
    rows: list[list[str]] = []
    header: list[str] | None = None
    in_tbl = False
    for ln in lines:
        if TABLE_HEAD.match(ln):
            in_tbl = True
            header = None
            continue
        if not in_tbl:
            continue
        if re.match(r"^#{1,3} ", ln):
            in_tbl = False
            continue
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if len(cells) == len(header) and set("".join(cells)) <= set("-: "):
            continue  # separator
        if "Document" in " ".join(header) and cells and not cells[0]:
            continue
        rows.append(cells)
    has_time = header is not None and any(
        h.lower().strip() == "time" for h in (header or [])
    )
    return rows, has_time


def cell_minutes(cells: list[str]) -> float | None:
    for c in cells:
        m = DUR.search(c)
        if m:
            v = float(m.group(1))
            return v * 60 if m.group(2).startswith("h") else v
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    findings: list[str] = []

    phases = root / "docs" / "phases"
    for mod in sorted(p for p in phases.glob("phase*/*") if p.is_dir()):
        rm = mod / "README.md"
        if not rm.exists():
            continue
        rel = rm.relative_to(root).as_posix()
        rfm = fm_fields(rm)
        text = rm.read_text(encoding="utf-8")
        lines = unfenced_lines(text)

        lessons = [
            p
            for p in sorted(mod.glob("*.md"))
            if p.name not in ("README.md", "PREREQUISITES.md")
        ]
        ltiers = {}
        for p in lessons:
            f = fm_fields(p)
            if f and f.get("diff") in TIER_STARS:
                ltiers[p.name] = TIER_STARS[f["diff"]]

        # CC-01: card tier == max lesson tier
        if rfm and rfm.get("diff") in TIER_STARS and ltiers:
            want = max(ltiers.values())
            if TIER_STARS[rfm["diff"]] != want:
                findings.append(
                    f"{rel} CC-01 course card FM Difficulty "
                    f"'{rfm['diff']}' != max lesson tier "
                    f"'{[t for t, v in TIER_STARS.items() if v == want][0]}' "
                    f"(lessons: {sorted(ltiers)})"
                )

        # CC-04: every lesson linked somewhere in the README
        linked = {
            PurePosixPath(m.group(1).split("#")[0]).name
            for m in LINK.finditer("\n".join(lines))
            if not m.group(1).startswith(("http://", "https://"))
        }
        missing = sorted(p.name for p in lessons if p.name not in linked)
        if missing:
            findings.append(
                f"{rel} CC-04 lessons on disk but linked nowhere in the "
                f"README: {missing}"
            )

        # Module Documents table: CC-02/03 per row, CC-05 coverage
        rows, has_time = table_rows(lines)
        if not rows:
            continue
        row_targets: dict[str, list[str]] = {}
        for cells in rows:
            m = LINK.search(cells[0]) if cells else None
            base = PurePosixPath(m.group(1).split("#")[0]).name if m else None
            if base:
                row_targets.setdefault(base, []).append(" | ".join(cells))
            if not m:
                continue
            target = mod / m.group(1)
            if not target.exists():
                continue  # linkcheck's territory
            tfm = fm_fields(target)
            if not tfm:
                continue
            tier = tfm.get("diff")

            # CC-02: star cell count == TIER_STARS[target tier]
            if tier in TIER_STARS:
                star_i = next(
                    (c for c in cells if c.count(STAR) > 0), None
                )
                if star_i is None:
                    findings.append(
                        f"{rel} CC-02 table row for {base} shows no star "
                        f"cell (want {TIER_STARS[tier]} for {tier})"
                    )
                elif star_i.count(STAR) != TIER_STARS[tier]:
                    findings.append(
                        f"{rel} CC-02 table row for {base} shows "
                        f"{star_i.count(STAR)} stars, target FM tier "
                        f"'{tier}' wants {TIER_STARS[tier]}"
                    )

            # CC-03: duration cell == FM Estimated Time (minute-exact)
            fm_m = fm_minutes(tfm.get("et"))
            cell_m = cell_minutes(cells)
            if cell_m is None and has_time:
                findings.append(
                    f"{rel} CC-03 table row for {base} carries no duration "
                    f"but the table promises a Time column (FM ET="
                    f"{tfm.get('et')})"
                )
            elif cell_m is not None and fm_m is not None and cell_m != fm_m:
                findings.append(
                    f"{rel} CC-03 table row for {base} shows "
                    f"{cell_m:g}min, target FM Estimated Time is "
                    f"{tfm.get('et')} ({fm_m:g}min)"
                )

        # CC-05: every lesson has a row in the table
        tbl_miss = sorted(
            p.name
            for p in lessons
            if p.name not in {b for b in row_targets if b}
        )
        if tbl_miss:
            findings.append(
                f"{rel} CC-05 Module Documents table exists but misses "
                f"lessons: {tbl_miss}"
            )

    for f in findings:
        print(f)
    if findings:
        print(
            f"course_card_check: {len(findings)} finding(s)",
            file=sys.stderr,
        )
        return 1
    print("course_card_check: 0 findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
