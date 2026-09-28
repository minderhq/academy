#!/usr/bin/env python3
"""resource identity gate: numbered-resource ids are one canonical form corpus-wide.

The corpus's 43 numbered resources (LAB-000..014, PROJECT-001..007,
TUTORIAL-000..014, CHEAT-SHEET-001..006) carry their identity in the
filename, the frontmatter Title, the H1 and every cross-reference - but
nothing locked those together, so the id drifted into three spellings
("LAB 007", "Tutorial 007", "LAB-007"). The 2026-09-29 four-tick
campaign (ticks 268-271) unified every occurrence to the dashed
`FAMILY-0NN:` form; this gate keeps it there. Identities are the
corpus's navigation layer - lab_registry_check locks what each id
POINTS AT, this gate locks the id itself.

Three findings:

  RI-01  Title/H1 identity missing or wrong - a resource file whose
         frontmatter Title or first `# ` heading does not carry the
         filename's own `FAMILY-0NN:` id (covers both the id-less
         Title rot and the Title-says-other-file mismatch)
  RI-02  spaced id form - `LAB 007`, `Project 003`, `CHEAT SHEET 004`
         (any case, corpus-wide): the pre-campaign spellings, banned
         everywhere so the split cannot re-emerge

    python scripts/qa/resource_id_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# filename shape of a numbered resource: FAMILY-0NN-<slug>.md
RESOURCE_RE = re.compile(r"^(LAB|PROJECT|TUTORIAL|CHEAT-SHEET)-(\d{3})-")

# the pre-campaign spaced spellings, any case (dashed is canonical)
SPACED_RE = re.compile(r"\b(lab|project|tutorial|cheat sheet) ([0-9]{3})\b",
                       re.IGNORECASE)

FAMILIES = ("labs", "projects", "tutorials", "cheat-sheets")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    resources = 0
    for family in FAMILIES:
        d = args.root / "docs" / "learning-resources" / family
        for path in sorted(d.glob("*.md")):
            m = RESOURCE_RE.match(path.stem)
            if m is None:
                continue  # QUICK-REF-VOLUME-*, SETUP-GUIDE, PREREQUISITES-*
            resources += 1
            res_id = f"{m.group(1)}-{m.group(2)}"
            text = path.read_text(encoding="utf-8", errors="replace")

            title = re.search(r'^Title:\s*"(.*)"\s*$', text, re.M)
            if title is None or not re.search(rf"\b{res_id}:", title.group(1)):
                findings.append(
                    "%s: RI-01 frontmatter Title does not carry the "
                    "filename's own %s: id" % (
                        path.relative_to(args.root).as_posix(), res_id))
            h1 = next((l[2:].strip() for l in text.split("\n")
                       if l.startswith("# ")), None)
            if h1 is None or not re.search(rf"\b{res_id}:", h1):
                findings.append(
                    "%s: RI-01 first H1 does not carry the filename's "
                    "own %s: id" % (
                        path.relative_to(args.root).as_posix(), res_id))

    scanned = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        scanned += 1
        for ln, line in enumerate(
                path.read_text(encoding="utf-8",
                               errors="replace").split("\n"), 1):
            for m in SPACED_RE.finditer(line):
                fam = ("CHEAT-SHEET" if m.group(1).lower() == "cheat sheet"
                       else m.group(1).upper())
                findings.append(
                    "%s:%d: RI-02 spaced id form '%s %s' - use the "
                    "dashed %s-%s form" % (
                        path.relative_to(args.root).as_posix(), ln,
                        m.group(1).upper(), m.group(2), fam, m.group(2)))

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print("resource_id_check: %d findings (%d resources checked, %d corpus "
          "files scanned)" % (len(findings), resources, scanned))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
