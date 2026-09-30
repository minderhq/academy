#!/usr/bin/env python3
"""Front-matter VALUE contracts (FV-01..04, HARD) - the platform
ingestion simulation.

FS-01/02 gate the six standard field NAMES; the dup gates check
specific values in isolation. This gate verifies the VALUE
CONTRACTS the eventual platform will rely on when it ingests
front matter as machine metadata - by doing exactly what the
platform will do: yaml.safe_load the block, then type-check the
fields that drive filters, sort orders and reading-time displays.

FV-01  Last Updated is a real calendar date in YYYY-MM-DD form -
       the ISO-8601 contract; a display layer parses it with a
       date parser, and locale-flavored or prose dates
       ("Sept 30th, 2026") crash it
FV-02  Estimated Time is machine-comparable: either the
       single-regime form "N hours|minutes" (fractional N legal,
       singular with 1) or the canonical two-regime form
       "30 minutes (quick review) - N hours (full review)" used
       by PREREQUISITES docs - the reading-time pipeline does
       arithmetic on this field, prose variants are invisible
FV-03  Tags parses to a list of strings - the platform's tag
       filter builds UI checkboxes from this list; a bare string
       or a string-with-commas silently degrades into one giant
       filter token
FV-04  the whole front-matter block yaml.safe_loads to a dict -
       this IS the ingestion call; one unparseable value and the
       platform drops the doc's metadata entirely

Scope: all docs/**/*.md, FM block = first ---...--- (within 40
lines, FS-01's contract). Related is OUT of value-typing on
purpose: its canonical values are the prose pointer
"See module README" and mixed string/int lists, both long-
established corpus conventions - a separate axis if ever gated.

Census at birth (tick-493): 408/408 yaml-parseable, 408/408
ISO dates, Tags clean; one real drain ("1 hours" -> "1 hour" in
phase1 1100 PRACTICE.md) and the two-regime PREREQUISITES form
canonized as FV-02's second arm.

Note: this gate is the fleet's only third-party import (PyYAML) -
deliberate, because the rule under test is "yaml.safe_load
succeeds", and a re-implementation would test something else.

Run over the whole corpus:
    python scripts/qa/frontmatter_value_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

TIME_SINGLE = re.compile(r"^\d+(\.\d+)? (hour|minute)s?$")
TIME_DOUBLE = re.compile(r"^30 minutes \(quick review\) - \d+(\.\d+)? hours \(full review\)$")
ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def fm_block(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3 or len(parts[0].splitlines()) > 40:
        return None
    return parts[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        rel = path.relative_to(args.root).as_posix()
        text = path.read_text(encoding="utf-8")
        block = fm_block(text)
        if block is None:
            continue  # FS-01's domain
        n_docs += 1
        try:
            data = yaml.safe_load(block)
            if not isinstance(data, dict):
                raise yaml.YAMLError("front matter is not a mapping")
        except yaml.YAMLError as exc:
            findings.append(
                "FV-04 %s: front matter fails yaml.safe_load - %s; the "
                "platform ingests FM with this exact call and drops all "
                "metadata when it fails (see docstring)" % (rel, str(exc)[:80]))
            continue
        lu = data.get("Last Updated")
        # yaml auto-converts bare ISO dates to datetime.date - that
        # conversion IS the ISO contract (it fails for impossible
        # dates); quoted ISO strings and (as failure) everything
        # else are checked explicitly
        if isinstance(lu, dt.date) and not isinstance(lu, dt.datetime):
            pass
        elif isinstance(lu, str) and ISO_DATE.match(lu):
            try:
                dt.date(int(lu[:4]), int(lu[5:7]), int(lu[8:10]))
            except ValueError:
                findings.append(
                    "FV-01 %s: Last Updated %r is not a real calendar "
                    "date" % (rel, lu))
        else:
            findings.append(
                "FV-01 %s: Last Updated %r is not YYYY-MM-DD - the "
                "ISO-8601 contract; date parsers crash on locale or "
                "prose forms" % (rel, lu))
        et = data.get("Estimated Time")
        if et is not None and not (isinstance(et, str)
                                   and (TIME_SINGLE.match(et)
                                        or TIME_DOUBLE.match(et))):
            findings.append(
                "FV-02 %s: Estimated Time %r is not machine-comparable - "
                "use \"N hours|minutes\" or the canonical \"30 minutes "
                "(quick review) - N hours (full review)\"; the reading-"
                "time pipeline does arithmetic on this field"
                % (rel, et))
        tags = data.get("Tags")
        if not (isinstance(tags, list) and tags
                and all(isinstance(t, str) and t for t in tags)):
            findings.append(
                "FV-03 %s: Tags %r is not a non-empty list of strings - "
                "the platform's tag filter builds UI from this list; "
                "bare/comma strings degrade into one giant token"
                % (rel, tags))
    for f in findings:
        print("  " + esc(f))
    print("frontmatter_value_scan: %d docs with FM inspected; %d FV "
          "findings - hard (FV-01 ISO dates, FV-02 machine-comparable "
          "time, FV-03 Tags list-of-string, FV-04 yaml.safe_load = the "
          "platform ingestion simulation; born tick-493, one drain "
          "('1 hours' -> '1 hour'); see docstring)"
          % (n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
