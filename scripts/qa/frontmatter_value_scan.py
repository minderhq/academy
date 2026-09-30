#!/usr/bin/env python3
"""Front-matter VALUE contracts (FV-01..06, HARD) - the platform
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
FV-05  an integer inside a Related list must be the Document ID
       of an existing doc - the platform renders Related as
       next-lesson cards; a dangling id is a broken card at
       runtime (two-pass: collect all Document IDs first, then
       verify - cross-file reference)
FV-06  Related, when present, is a prose pointer (str) or a list
       of ids/names - never a number, bool or mapping; the triage
       census (tick-494) found exactly these forms corpus-wide:
       178 canonical "See module README", 11 lists, 4 prose
       variants, 215 absent

Scope: all docs/**/*.md, FM block = first ---...--- (within 40
lines, FS-01's contract). Related string elements (LAB-003,
TUTORIAL-002 namespaces) are NOT resolved by FV-05 - they live in
other registries (labs, learning-resources) with their own gates;
the integer namespace is the one FV-05 owns. Related is otherwise
free-form by design.

Census at birth (tick-493): 408/408 yaml-parseable, 408/408
ISO dates, Tags clean; one real drain ("1 hours" -> "1 hour" in
phase1 1100 PRACTICE.md) and the two-regime PREREQUISITES form
canonized as FV-02's second arm. FV-05/06 born tick-494
born-at-zero: 32 Related integer refs, 0 dangling.

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
    # pass 1: collect (rel, data) pairs and the Document ID universe
    parsed: list[tuple[str, dict]] = []
    doc_ids: set[int] = set()
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
        parsed.append((rel, data))
        did = data.get("Document ID")
        if isinstance(did, int):
            doc_ids.add(did)
        elif isinstance(did, str) and did.isdigit():
            doc_ids.add(int(did))
    # pass 2: value contracts
    for rel, data in parsed:
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
        relv = data.get("Related")
        if relv is not None and not isinstance(relv, (str, list)):
            findings.append(
                "FV-06 %s: Related %r is neither a prose pointer (str) "
                "nor a list - numbers, bools and mappings have no "
                "rendering on the platform (triage census in docstring)"
                % (rel, relv))
        if isinstance(relv, list):
            for el in relv:
                if isinstance(el, bool) or not isinstance(el, (int, str)):
                    findings.append(
                        "FV-06 %s: Related list element %r is neither an "
                        "id (int) nor a name (str) - the platform renders "
                        "Related as next-lesson cards" % (rel, el))
                elif isinstance(el, int) and el not in doc_ids:
                    findings.append(
                        "FV-05 %s: Related references Document ID %d, "
                        "which no doc carries - the platform renders "
                        "Related as next-lesson cards; a dangling id is "
                        "a broken card at runtime" % (rel, el))
    for f in findings:
        print("  " + esc(f))
    print("frontmatter_value_scan: %d docs with FM inspected; %d FV "
          "findings - hard (FV-01 ISO dates, FV-02 machine-comparable "
          "time, FV-03 Tags list-of-string, FV-04 yaml.safe_load, FV-05 "
          "no dangling Related int, FV-06 Related str-or-list = the "
          "platform ingestion simulation; born tick-493 with one drain "
          "('1 hours' -> '1 hour'), Related arms tick-494 born-at-zero; "
          "see docstring)"
          % (n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
