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
CC-06  The card's FM Estimated Time exists and equals ceil(sum of lesson FM
       Estimated Time minutes / 60) - the LI-05-proven parts-sum arithmetic
       lifted to course scope. The platform catalog reads one time budget
       per course card, so a card with no FM ET fires (presence clause),
       an unparseable value fires, and a value disagreeing with the
       arithmetic fires. The equality is computed only when every lesson
       carries a parseable FM ET; a lesson-less parse gap is not reported
       here twice.
CC-07  Every lesson carries a parseable FM Estimated Time ('N hours' or
       'N minutes') - the invariant that makes CC-06's equality
       precondition unconditional instead of silently skippable: a
       lesson-side parse gap silently disabled the course-sum check,
       so the gap itself is now the finding, listed per module in the
       CC-04/CC-05 list style.
CC-08  Every module directory is linked from its phase README (any link
       form, fence-aware) - the CC-04 invariant one level up: phase
       pages are the platform's course browse list, so a module that is
       visible from its own module index (CC-04) but absent from its
       phase page is invisible above the cards.
CC-09  A phase README's module links must first appear in ascending
       curriculum order - the browse list order is the unlock order
       (fence-aware; a link with no module-dir component is a lesson
       link and does not enter the order).
CC-10  Every module's PREREQUISITES.md carries at least one internal
       course link (a target ending .md) - the entry page a platform
       renders must offer the learner a clickable way into the
       course, not prose alone.
CC-11  A module README's lesson links must first appear in ascending
       order - the course card's lesson order is the unlock order,
       the CC-09 invariant one level down (fence-aware; non-lesson
       targets never enter the order).

The gate is order-agnostic about table columns (3500-multimodal renders Time
before Difficulty and both orders pass). Dead row targets are skipped here -
linkcheck owns them. Born tick-576 after a 35-finding drain (22 FM cards, 2
body badges that mirrored the drifted FM, 10 star cells, 2 time cells, 1
missing table row); the drain obeys the 11-of-33 modules that already satisfy
CC-01 - the contract is the curated majority's convention, not an invention.
CC-06 born tick-578: the census found 29 of 33 cards carrying no FM Estimated
Time at all and the 4 boilerplate carriers (12/18/28/37 hours, born 775f898)
overshooting every computable source; the drain wrote the ceil lesson sum
into all 33 cards (29 insertions, 4 corrections - every sum whole hours) and
the lock freezes the arithmetic. CC-07 born tick-579 as a zero-drain lock in
the PQ-06 shape: the lesson-level census read 93/93 module lessons clean, so
the precondition CC-06 leans on is frozen as its own invariant. CC-08 born
tick-580 as the second zero-drain lock in the same shape: the census read
all 7 phase READMEs covering all 33 module dirs (the house convention links
lessons inside each module dir from the phase page), so the browse spine
above the cards is frozen too. CC-09 born tick-581 at zero (7/7 phase pages
first-appear ascending); CC-10 born tick-581 after a one-line drain -
3500-multimodal's entry page was the lone PREREQUISITES.md of 33 with no
clickable way into the course (32 siblings linked their first lesson; the
drain wrote the house 'If YES: Start with [3501: ...]' form). CC-11 born
tick-582 at zero - the third zero-drain lock in the PQ-06/CC-08/CC-09
shape: all 93 lesson links across the 33 module READMEs first appear in
ascending order, so the course card's lesson order froze as the unlock
order.

Exit 1 on any finding; prints one line per finding.
"""
from __future__ import annotations

import argparse
import math
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
        letm: dict[str, float] = {}
        lgap: list[str] = []
        for p in lessons:
            f = fm_fields(p)
            if f and f.get("diff") in TIER_STARS:
                ltiers[p.name] = TIER_STARS[f["diff"]]
            lm = fm_minutes(f.get("et")) if f else None
            if lm is not None:
                letm[p.name] = lm
            else:
                lgap.append(p.name)

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

        # CC-06: card FM Estimated Time present and == ceil(lesson ET sum)
        card_et = (rfm or {}).get("et")
        if card_et is None:
            findings.append(
                f"{rel} CC-06 course card carries no FM Estimated Time "
                f"(the platform catalog reads a time budget per course)"
            )
        else:
            card_m = fm_minutes(card_et)
            if card_m is None:
                findings.append(
                    f"{rel} CC-06 course card FM Estimated Time "
                    f"'{card_et}' is not a parseable hour/minute budget "
                    f"(want 'N hours')"
                )
            elif lessons and len(letm) == len(lessons):
                want_h = math.ceil(sum(letm.values()) / 60)
                if card_m != want_h * 60:
                    findings.append(
                        f"{rel} CC-06 course card FM Estimated Time "
                        f"'{card_et}' != ceil lesson sum "
                        f"({sum(letm.values()):g}min -> {want_h}h)"
                    )

        # CC-07: every lesson carries a parseable FM Estimated Time - the
        # invariant that keeps CC-06's equality precondition unconditional
        if lgap:
            findings.append(
                f"{rel} CC-07 lessons carrying no parseable FM Estimated "
                f"Time (want 'N hours' or 'N minutes' - the budget the "
                f"platform renders per lesson): {lgap}"
            )

        # CC-10: PREREQUISITES.md must offer the learner a way into the
        # course - the entry page a platform renders needs at least one
        # internal course link, not prose alone
        prm = mod / "PREREQUISITES.md"
        if prm.exists():
            pblob = "\n".join(unfenced_lines(prm.read_text(encoding="utf-8")))
            exits = [
                m.group(1)
                for m in LINK.finditer(pblob)
                if m.group(1).endswith(".md")
                and not m.group(1).startswith(
                    ("http://", "https://", "mailto:")
                )
            ]
            if not exits:
                findings.append(
                    f"{prm.relative_to(root).as_posix()} CC-10 "
                    f"PREREQUISITES.md carries no internal course link "
                    f"(the entry page must offer the learner a clickable "
                    f"way into the course)"
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

        # CC-11: lesson links must first appear in ascending order -
        # the course card's lesson order is the unlock order (the
        # CC-09 invariant one level down)
        lorder: list[str] = []
        for m in LINK.finditer("\n".join(lines)):
            tgt = m.group(1).split("#")[0]
            if tgt.startswith(("http://", "https://", "mailto:")):
                continue
            base = PurePosixPath(tgt).name.removesuffix(".md")
            hit = next(
                (p.name for p in lessons if p.stem == base), None
            )
            if hit and hit not in lorder:
                lorder.append(hit)
        lnums = [int(n[:4]) for n in lorder]
        if lnums != sorted(lnums):
            findings.append(
                f"{rel} CC-11 module README lesson links first appear "
                f"out of unlock order - {lorder}"
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

    # CC-08: every module is linked from its phase README - the CC-04
    # invariant one level up: a module invisible from its phase page is
    # invisible from the platform's course browse list
    for ph in sorted(p for p in phases.glob("phase*") if p.is_dir()):
        prm = ph / "README.md"
        if not prm.exists():
            continue
        prel = prm.relative_to(root).as_posix()
        blob = "\n".join(unfenced_lines(prm.read_text(encoding="utf-8")))
        targets = [
            m.group(1).split("#")[0]
            for m in LINK.finditer(blob)
            if not m.group(1).startswith(("http://", "https://"))
        ]
        here = sorted(d.name for d in ph.iterdir() if d.is_dir())
        ghost = [mn for mn in here if not any(mn in t for t in targets)]
        if ghost:
            findings.append(
                f"{prel} CC-08 modules on disk but linked nowhere in "
                f"the phase index (the CC-04 invariant one level up - "
                f"this page is the platform's course browse list): "
                f"{ghost}"
            )

        # CC-09: the phase page's module links must first appear in
        # ascending curriculum order - the browse list order is the
        # unlock order (a link with no module-dir component is a
        # lesson link and does not enter the order)
        order: list[int] = []
        for t in targets:
            dm = re.search(r"(?<!\d)(\d{4})-[a-z0-9-]+(?:/|$)", t)
            if dm:
                n = int(dm.group(1))
                if n not in order:
                    order.append(n)
        if order != sorted(order):
            findings.append(
                f"{prel} CC-09 phase page browse order is not the "
                f"unlock order - module links first appear as {order}, "
                f"want ascending {sorted(order)}"
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
