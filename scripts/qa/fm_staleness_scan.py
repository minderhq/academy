#!/usr/bin/env python3
"""FM-staleness report gate for the Minder Academy curriculum corpus.

Freshness map: parses ``Last Updated:`` from the frontmatter of every
docs/**/*.md and reports the age distribution against today. For an
education platform the freshness of the curriculum is a first-class
quality signal: version-sensitive content (install guides, API
walkthroughs, release notes) should not age quietly, while stable
theory lessons legitimately do. This gate makes the aging visible so
modernization passes can target the oldest material first.

Report-only (exit 0 by design, like fence_namecheck): a stale date is
a review queue, not a broken file. Hard-failing it would punish the
stable theory core every run.

Classes:
    FRESH   updated within --fresh-days (default 90)
    RECENT  updated within --stale-days (default 365)
    STALE   older than --stale-days - the review queue this gate surfaces
    MISSING no parsable Last Updated date in the frontmatter block
            (frontmatter_lint owns FM validity; this is a safety net)

The oldest STALE files are listed first, capped at --list (default 40)
lines so the console stays readable on a 461-file corpus.

Run over the whole corpus:
    python scripts/qa/fm_staleness_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

FM_DELIM = re.compile(r"^---\s*$")
LAST_UPDATED = re.compile(r"^Last Updated:\s*(\d{4})-(\d{2})-(\d{2})\s*$")


def scan_file(path: Path, root: Path, today: date) -> tuple[int, str]:
    """Return (age_days, rel) or (-1, rel) when the date is missing."""
    rel = path.relative_to(root).as_posix()
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except (OSError, UnicodeDecodeError):
        return -1, rel
    if not lines or not FM_DELIM.match(lines[0]):
        return -1, rel
    for line in lines[1:]:
        if FM_DELIM.match(line):
            break  # frontmatter closed without a parsable date
        m = LAST_UPDATED.match(line)
        if m:
            try:
                updated = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return -1, rel
            return (today - updated).days, rel
    return -1, rel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--fresh-days", type=int, default=90)
    parser.add_argument("--stale-days", type=int, default=365)
    parser.add_argument("--list", type=int, default=40,
                        help="max STALE files to print (default: %(default)s)")
    args = parser.parse_args()
    docs = args.root / "docs"
    today = date.today()

    fresh = recent = stale = missing = 0
    stale_files: list[tuple[int, str]] = []
    missing_files: list[str] = []
    n = 0
    for path in sorted(docs.rglob("*.md")):
        n += 1
        age, rel = scan_file(path, args.root, today)
        if age < 0:
            missing += 1
            missing_files.append(rel)
        elif age <= args.fresh_days:
            fresh += 1
        elif age <= args.stale_days:
            recent += 1
        else:
            stale += 1
            stale_files.append((age, rel))

    for rel in missing_files:
        print(f"MISSING {rel}: no parsable Last Updated in frontmatter")
    stale_files.sort(reverse=True)
    for age, rel in stale_files[: max(args.list, 0)]:
        print(f"STALE   {rel}: {age}d since Last Updated")
    if len(stale_files) > max(args.list, 0):
        print(f"... and {len(stale_files) - max(args.list, 0)} more stale files")

    oldest = f"{stale_files[0][0]}d {stale_files[0][1]}" if stale_files else "-"
    print(f"fm_staleness: {n} files scanned, {fresh} fresh(<={args.fresh_days}d), "
          f"{recent} recent(<={args.stale_days}d), {stale} stale(>{args.stale_days}d), "
          f"{missing} missing; oldest: {oldest} (report mode - exit 0 by design)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
