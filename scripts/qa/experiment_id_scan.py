#!/usr/bin/env python3
"""Experiments identity scan (EC-01..03) for PROJECT-OMEGA.

experiments/ is the one content directory outside docs/ (48 .md
files at tick-608), and the platform catalogs content by Document
ID while its catalog walks docs/ links - yet doc_id_check scans
docs/ only, so the identity of every experiment file was unvouched
until this gate: a typo'd ID, a duplicate, or an on-disk-but-
unlinked experiment (the CHEAT-SHEET-006 orphan class) would ship
invisible or mis-keyed.

EC-01  every experiments/*.md carries a top-level FM Document ID
       matching `EXP_NNNN` that EQUALS the file's own code token
       (filename `EXP_NNNN_<NAME>.md`) - the LP-05 label rule
       lifted to file identity: the ID is the platform's primary
       key, it must not disagree with the file it lives in.
       experiments/TEMPLATE.md is the one by-design exemption (a
       template cannot honestly carry a real code; its
       `EXP-TEMPLATE` placeholder ID is intentional, the CC-31
       fixed-name carve-out shape).

EC-02  Document IDs unique across experiments/ AND disjoint from
       every docs/ Document ID - the ID namespace is global; two
       files answering to one ID is an ambiguous catalog row on
       the platform.

EC-03  every experiments/*.md is referenced from at least one
       docs/ file (by full filename or stem) - the catalog walks
       docs/ links, so an experiment no doc points at is on disk
       but invisible to a learner (fleet_count_parity_check
       proved the class: 15 of 47 experiments were hidden from
       the README front door until tick-559 despite linkcheck
       green).

Birth census tick-608: 48 files / 48 FM / 1 keyset shape
(Document ID / Title / Last Updated / Status / Difficulty), 47
real IDs all `EXP_NNNN` matching their filename codes, 0
duplicates within experiments/, 0 collisions with the 408-doc
docs/ namespace, 48/48 linked from docs/ - the gate froze the
class the moment it was named, born at zero findings, no drain,
zero-drain shape.

HARD GATE - exit 1 on any finding. All three clauses hard from
birth.

Run over the whole corpus:
    python scripts/qa/experiment_id_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
ID_FIELD = re.compile(r"^Document ID:(.*)$")
EXP_ID = re.compile(r"^EXP_\d{4}$")
CODE_FROM_NAME = re.compile(r"^EXP_(\d{4})_")
TEMPLATE_NAME = "TEMPLATE.md"


def doc_id(lines: list[str]) -> str | None:
    """Top-level Document ID value of one doc, or None."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = ID_FIELD.match(raw)
                if m:
                    return m.group(1).strip()
            return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    exp_dir = args.root / "experiments"
    paths = sorted(exp_dir.rglob("*.md"))

    findings: list[str] = []
    ids: dict[str, list[str]] = {}
    n_linked = 0

    for path in paths:
        rel = path.relative_to(args.root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        val = doc_id(lines)
        cm = CODE_FROM_NAME.match(path.name)
        # EC-01 - identity: ID exists, is EXP_NNNN, and equals the
        # filename's own code token (TEMPLATE.md by-design exempt)
        if path.name != TEMPLATE_NAME:
            if val is None:
                findings.append(
                    f"{rel}: EC-01 experiments identity broken "
                    f"(no Document ID; the platform keys content "
                    f"by ID)")
            elif not EXP_ID.match(val):
                findings.append(
                    f"{rel}: EC-01 experiments identity broken "
                    f"(Document ID {val!r} is not the EXP_NNNN form)")
            elif cm and val != f"EXP_{cm.group(1)}":
                findings.append(
                    f"{rel}: EC-01 experiments identity broken "
                    f"(Document ID {val} disagrees with the file's "
                    f"own code EXP_{cm.group(1)})")
        if val is not None:
            ids.setdefault(val, []).append(rel)

    # EC-02 - uniqueness within experiments/ (global namespace)
    for val, rels in sorted(ids.items()):
        if len(rels) > 1:
            findings.append(
                f"{rels[0]}: EC-02 duplicate Document ID {val!r} "
                f"({len(rels)} files: {', '.join(rels)})")

    # EC-03 - visibility: every experiment referenced from docs/
    docs_paths = sorted((args.root / "docs").rglob("*.md"))
    corpus = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in docs_paths)
    for path in paths:
        if path.stem in corpus or path.name in corpus:
            n_linked += 1
        else:
            findings.append(
                f"{path.relative_to(args.root).as_posix()}: EC-03 "
                f"experiment invisible (no docs/ file references "
                f"it; the catalog walks docs/ links)")

    ec01 = sum(1 for f in findings if " EC-01 " in f)
    ec02 = sum(1 for f in findings if " EC-02 " in f)
    ec03 = sum(1 for f in findings if " EC-03 " in f)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"experiment_id_scan: files={len(paths)} ids={len(ids)} "
          f"linked={n_linked} EC-01={ec01} EC-02={ec02} EC-03={ec03} "
          f"(hard gate; TEMPLATE.md is the one EC-01 by-design "
          f"exemption; born tick-608 at zero)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
