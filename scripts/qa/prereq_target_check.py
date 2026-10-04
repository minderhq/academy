#!/usr/bin/env python3
"""Canonical Prerequisites pointer target integrity (PQ-05) for Minder Academy.

prereq_free_text_check (PQ-04) closed the Prerequisites free-text
vocabulary at two role-canonical strings. That closure made the
STRINGS legal - but said nothing about whether the pointer LANDS:

    "See module README"      -> the module's README.md must exist AND
                                carry a prerequisites section
    "See PREREQUISITES.md"   -> the module's PREREQUISITES.md must
                                exist

A canonical string pointing at a README without a prerequisites
section is a nav dead-end: the platform renders the pointer, the
learner follows it, and finds nothing. The birth census (2026-09-30)
measured all 33 module dirs: every README.md carries a prerequisites
heading and all 33 PREREQUISITES.md files exist, so the gate is born
at zero (KW-03 born-at-zero: deterministic predicate, census 0 ->
HARD from birth).

Module resolution: the nearest ancestor directory that contains a
README.md - "module README" means the README of the collection the
doc lives in. For numbered modules that resolves to NNNN-*/README.md
(guides/ and assessment/ subdirs resolve through them); for
top-level collections like docs/enterprise-solutions/ it resolves to
the collection README. A canonical pointer with no README-bearing
ancestor is itself a finding.

HARD GATE - exit 1 on any finding.

Run over the whole corpus:
    python scripts/qa/prereq_target_check.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
PQ_FIELD = re.compile(r"^Prerequisites:(.*)$")
PREREQ_HEADING = re.compile(r"^#{1,3}[^#\n]*[Pp]rerequis", re.M)

CANON_MODULE = "See module README"
CANON_PREREQ_DOC = "See PREREQUISITES.md"


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def pq_value(lines: list[str]) -> str | None:
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = PQ_FIELD.match(raw)
                if m:
                    return m.group(1).strip()
            return None
    return None


def module_dir(path: Path) -> Path | None:
    for anc in path.parents:
        if (anc / "README.md").exists():
            return anc
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    n_pointers = 0
    n_module = 0
    n_prereq_doc = 0
    readme_has_section: dict[Path, bool] = {}
    findings: list[str] = []

    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        val = pq_value(lines)
        if val not in (CANON_MODULE, CANON_PREREQ_DOC):
            continue  # token forms: PQ-01..03; absent field: not this gate
        n_pointers += 1
        rel = path.relative_to(args.root).as_posix()
        mod = module_dir(path)
        if mod is None:
            findings.append("PQ-05 canonical pointer with no README-bearing "
                            "ancestor: %r in %s" % (val, rel))
            continue
        if val == CANON_PREREQ_DOC:
            n_prereq_doc += 1
            target = mod / "PREREQUISITES.md"
            if not target.exists():
                findings.append("PQ-05 dangling PREREQUISITES.md target: %s "
                                "points at missing %s"
                                % (rel, target.relative_to(args.root).as_posix()))
            continue
        n_module += 1
        target = mod / "README.md"
        if not target.exists():
            findings.append("PQ-05 dangling module-README target: %s points "
                            "at missing %s"
                            % (rel, target.relative_to(args.root).as_posix()))
            continue
        if target not in readme_has_section:
            try:
                body = target.read_text(encoding="utf-8", errors="replace")
            except (UnicodeDecodeError, OSError):
                body = ""
            readme_has_section[target] = bool(PREREQ_HEADING.search(body))
        if not readme_has_section[target]:
            findings.append("PQ-05 target README lacks prerequisites "
                            "section: %s points at %s"
                            % (rel, target.relative_to(args.root).as_posix()))

    print("prereq_target_check: %d canonical pointers (%d See-module-README, "
          "%d See-PREREQUISITES.md) over %d README targets"
          % (n_pointers, n_module, n_prereq_doc, len(readme_has_section)))
    for f in findings:
        print("  " + esc(f))
    print("prereq_target_check: %d PQ-05 findings - hard gate, born at "
          "zero (census 2026-09-30: 33/33 module READMEs carry prerequisites)"
          % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
