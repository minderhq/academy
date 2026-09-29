#!/usr/bin/env python3
"""resource-reference gate for the PROJECT-OMEGA curriculum corpus.

lab_registry_check locks what each resource id points at, and
resource_id_check locks the id itself on each resource's own Title/H1 -
but neither reads the corpus as a *reader* of the 43 resources. A
cross-document reference like "see LAB-016" or "TUTORIAL-020" claims a
resource exists; if it does not, every learner following that pointer
hits a dead end, and linkcheck cannot see it because the reference is
plain prose or a partial-name mention, not a relative link href.

RR-01  an uppercase FAMILY-0NN reference (LAB-016, PROJECT-009,
       TUTORIAL-020, CHEAT-SHEET-007) with no resource of that id on
       disk. The valid id set is derived from the same disk glob
       resource_id_check uses (docs/learning-resources/<family>/
       FAMILY-0NN-*.md), so a renamed/added resource updates the gate
       automatically.

Lowercase matches (lab-001) are out of scope by design: the birth
census (tick-327) found 101 of them and every one is a filesystem
path idiom - the ~/lab-001-docker-llm working directories the labs
create - not an id reference. Uppercase is the corpus's written id
convention (1316 mentions, 43 distinct ids, all in range).

Hard gate (exit 1 on findings): born at baseline 0 from the tick-327
census (1316 references, 0 out of range); any new out-of-range id is
a dead pointer a platform nav generator would happily render.

Run over the whole corpus:
    python scripts/qa/resource_ref_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FAMILIES = ("labs", "projects", "tutorials", "cheat-sheets")
# filename id on disk (resource_id_check's derivation)
DISK_RE = re.compile(r"^(LAB|PROJECT|TUTORIAL|CHEAT-SHEET)-(\d{3})-")
# uppercase id mentions in prose/code anywhere in a document
REF_RE = re.compile(r"\b(LAB|PROJECT|TUTORIAL|CHEAT-SHEET)-(\d{3})\b")


def valid_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for family in FAMILIES:
        d = root / "docs" / "learning-resources" / family
        for path in d.glob("*.md"):
            m = DISK_RE.match(path.name)
            if m:
                ids.add(f"{m.group(1)}-{m.group(2)}")
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    ids = valid_ids(args.root)
    if not ids:
        print("resource_ref_check: RR-00 no resources found on disk - "
              "cannot derive the valid id set")
        return 1

    findings: list[str] = []
    n_files = set()
    for path in sorted((args.root / "docs").rglob("*.md")):
        rel = path.relative_to(args.root).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in REF_RE.finditer(text):
            ref = m.group(0)
            if ref not in ids:
                lineno = text[:m.start()].count("\n") + 1
                findings.append(f"{rel}:{lineno}: RR-01 {ref} - no "
                                f"resource with this id on disk")
                n_files.add(rel)

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"resource_ref_check: {len(findings)} out-of-range id "
          f"references in {len(n_files)} files across docs/ "
          f"({len(ids)} valid ids: "
          + ", ".join(sorted(ids)) + ")")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
