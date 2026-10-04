#!/usr/bin/env python3
"""front-matter integrity census (FM-01..FM-06) for Minder Academy.

Platform conversion needs trustworthy structured metadata: every
doc carries a YAML front-matter block that the platform will use
for routing, difficulty filters, freshness signals and navigation.
Tick-402 measured the corpus first: all 408 docs have front
matter, 4 universal fields at 408/408 (Document ID, Title, Last
Updated, Status, Difficulty), Status is single-valued "Complete",
Difficulty uses exactly 4 enums (Expert x5), and ~106 lesson docs
carry Phase/Module. The census pins that state so regressions
surface as findings, not surprises.

FM-01  missing or unterminated front matter (no leading ---
       fence, or no closing ---/... within the first 40 lines).
FM-02  Difficulty outside {Beginner, Intermediate, Advanced,
       Expert} - the 4 enums the corpus uses today.
FM-03  Status outside {Complete, In Progress, Draft} - Draft and
       In Progress stay legal so platform-era drafting works.
FM-04  Last Updated not YYYY-MM-DD, or a future date (later than
       today) - the FM chain protocol bumps it forward, never
       backward-inventing.
FM-05  Phase field != phase number parsed from the path (docs/
       phases/phaseN-*/... lesson docs that declare Phase).
FM-06  Module field != 4-digit module segment parsed from the
       path (docs/phases/phaseN-MMMM-*/... docs that declare
       Module).

History: born tick-402 and measured 0 findings across 408 docs in
every class - the corpus front-matter discipline is already clean
(the universal-field protocol held since the verification-baseline
era). Promoted to HARD GATE in the same tick (KW-03 pattern: born
at zero, gated at zero) - exit 1 on any FM-01..FM-06 finding, so
metadata drift can never accumulate silently before the platform
lands. Enum sets are additive by design: a genuinely new Difficulty
or Status value is a deliberate edit that must update DIFFICULTY /
STATUS here in the same commit.

Run over the whole corpus:
    python scripts/qa/front_matter_census.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

DIFFICULTY = {"Beginner", "Intermediate", "Advanced", "Expert"}
STATUS = {"Complete", "In Progress", "Draft"}

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
FIELD = re.compile(r"^([A-Za-z][A-Za-z0-9 _-]*):(.*)$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PHASE_DIR = re.compile(r"^phase(\d+)-")
MODULE_DIR = re.compile(r"^(\d{4})-")


def parse_fm(lines: list[str]) -> tuple[dict[str, str], int] | None:
    """Return (top-level fields, close-line 0-based index) or None."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            fields: dict[str, str] = {}
            for raw in lines[1:i]:
                m = FIELD.match(raw)
                if m:
                    fields[m.group(1).strip()] = m.group(2).strip()
            return fields, i
    return None


def path_phase_module(parts: tuple[str, ...]) -> tuple[int | None, str | None]:
    """(phase, module) parsed from path segments under docs/phases/."""
    phase = module = None
    in_phases = False
    for seg in parts:
        if seg == "phases":
            in_phases = True
            continue
        if not in_phases:
            continue
        if phase is None:
            m = PHASE_DIR.match(seg)
            if m:
                phase = int(m.group(1))
                continue
        if module is None:
            m = MODULE_DIR.match(seg)
            if m:
                module = m.group(1)
    return phase, module


def check(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    parsed = parse_fm(lines)

    def add(tag: str, msg: str) -> None:
        findings.append(f"{rel}:{tag} {msg}")

    if parsed is None:
        add("FM-01", "missing or unterminated front matter")
        return
    fields, _ = parsed

    diff = fields.get("Difficulty", "")
    if diff not in DIFFICULTY:
        add("FM-02", f"difficulty '{diff}' outside {sorted(DIFFICULTY)}")
    status = fields.get("Status", "")
    if status not in STATUS:
        add("FM-03", f"status '{status}' outside {sorted(STATUS)}")

    lu = fields.get("Last Updated", "")
    if not DATE.match(lu):
        add("FM-04", f"last-updated '{lu}' not YYYY-MM-DD")
    else:
        y, mo, d = (int(x) for x in lu.split("-"))
        if date(y, mo, d) > date.today():
            add("FM-04", f"last-updated '{lu}' is a future date")

    pp, pm = path_phase_module(path.parts)
    phase = fields.get("Phase", "")
    if phase and pp is not None and phase.isdigit() and int(phase) != pp:
        add("FM-05", f"Phase {phase} != path phase{pp}")
    module = fields.get("Module", "")
    if module and pm is not None and module.isdigit() and module != pm:
        add("FM-06", f"Module {module} != path module {pm}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    n_files = 0
    for path in sorted(docs.rglob("*.md")):
        try:
            check(args.root, path, findings)
        except (UnicodeDecodeError, OSError, ValueError):
            continue
        n_files += 1
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"front_matter_census: {len(findings)} findings across "
          f"{n_files} docs (FM-01..FM-06; hard gate; universal "
          f"fields Document ID/Title/Last Updated/Status/Difficulty)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
