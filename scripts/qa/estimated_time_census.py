#!/usr/bin/env python3
"""Estimated Time field census (ET-01..ET-03) for PROJECT-OMEGA.

The platform will use Estimated Time for scheduling and progress
math, so every value must parse and the field name must be exact.
Tick-407 measured the corpus: 111 docs carry the field, name is
already uniform (0 variants), and values fall into five shapes -
98 integer hours, 2 decimal hours, 1 minutes-only, 4 dual-mode
(`30 minutes (quick review) - N hours (full review)`), and 6
hour-ranges (`6-8 hours`).

ET-01  value matches no duration grammar (unparseable).
ET-02  field-name variant - anything in the front-matter block
       spelled `Estimated[-_ ]?Time`, `Time Required` or
       `Duration` other than the exact `Estimated Time:`.
ET-03  range form `X-Y hours`. HARD - drained tick-408: all 6
       birth sites resolved to single durations (midpoint,
       half-up, integer hours: 6-8->7, 5-6->6, 11-12->12,
       17-19->18, 35-39->37); a range re-appearing fails the
       gate with the drain rule in the message. Ranges are
       ambiguous for platform scheduling math. Dual-mode entries
       are a legal shape: two real durations for two study
       modes, both parseable.

HARD GATE - exit 1 on any finding. ET-01/ET-02 hard from birth
(KW-03 born-at-zero: both measured 0 across 111 docs at
tick-407); ET-03 joined after the tick-408 drain (census ->
drain -> gate cycle).

Run over the whole corpus:
    python scripts/qa/estimated_time_census.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
ET_FIELD = re.compile(r"^Estimated Time:(.*)$")
ET_VARIANT = re.compile(r"^(?:Estimated[-_ ]?Time|Time Required|Duration):")
SINGLE = re.compile(r"^\d+(?:\.\d+)? (?:minutes?|hours?)"
                    r"(?: \(quick review\) - \d+(?:\.\d+)? hours "
                    r"\(full review\))?$")
RANGE = re.compile(r"^\d+(?:\.\d+)?-\d+(?:\.\d+)? hours$")


def scan_fm(lines: list[str]) -> tuple[str, None] | tuple[None, str] | tuple[None, None]:
    """(value, None) if the exact field is present, (None, variant)
    if a variant spelling shadows it, (None, None) if no field."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None, None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = ET_FIELD.match(raw)
                if m:
                    return m.group(1).strip(), None
                if ET_VARIANT.match(raw):
                    return None, raw
            return None, None
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    shapes = Counter()
    n_field = 0
    for path in sorted(docs.rglob("*.md")):
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(args.root).as_posix()
        try:
            value, variant = scan_fm(lines)
        except (UnicodeDecodeError, OSError):
            continue
        if variant is not None:
            findings.append(f"{rel}: ET-02 field-name variant {variant!r} "
                            f"(exact name is 'Estimated Time:')")
            continue
        if value is None:
            continue
        n_field += 1
        if RANGE.match(value):
            shapes["range"] += 1
            findings.append(f"{rel}: ET-03 range value {value!r} "
                            f"(drain to single: midpoint half-up, "
                            f"integer hours)")
        elif SINGLE.match(value):
            shapes["single"] += 1
        else:
            shapes["unparseable"] += 1
            findings.append(f"{rel}: ET-01 unparseable value {value!r} "
                            f"(grammar: 'N hours', 'N minutes', dual "
                            f"'30 minutes (quick review) - N hours "
                            f"(full review)')")

    et01 = sum(1 for f in findings if " ET-01 " in f)
    et02 = sum(1 for f in findings if " ET-02 " in f)
    et03 = sum(1 for f in findings if " ET-03 " in f)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"estimated_time_census: fields={n_field} "
          f"shapes={dict(shapes)} ET-01={et01} ET-02={et02} "
          f"ET-03={et03} "
          f"(hard gate; ET-03 drained tick-408, midpoint half-up "
          f"integer hours)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
