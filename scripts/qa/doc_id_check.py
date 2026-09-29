#!/usr/bin/env python3
"""Document-ID uniqueness gate for the PROJECT-OMEGA corpus.

manifest_export copies each document's frontmatter `Document ID` into
the platform manifest's primary `id` field - the join key a platform
DB or nav tree would key lessons on. FM-03 locks that the key exists
and FM-07 that it matches the filename prefix, but nothing locks the
key *unique across the corpus*: two docs can carry the same Document
ID, pass every per-file gate, and produce a manifest where the join
collapses two pages into one.

DD-01  a Document ID claimed by more than one document.

Hard gate (exit 1 on findings): born at baseline 0 from the tick-328
census (408 files, 408 distinct IDs, 0 duplicates). Short-form IDs
(PHASE1-PRACTICE, CP-001, COMPARISONS-README) are the established
corpus idiom and are in scope like any other - only uniqueness is
checked here, not spelling.

Unparseable/missing frontmatter is skipped: FM-01/02/03 own those.

Run over the whole corpus:
    python scripts/qa/doc_id_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quiz_export import parse_frontmatter  # noqa: E402

SKIP_DIRS = {".git", ".claude", "node_modules", "__pycache__", ".venv", "venv"}
ID_RE = re.compile(r"^Document ID:\s*(.+)$", re.M)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    ids: dict[str, list[str]] = defaultdict(list)
    n_files = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        rel = path.relative_to(args.root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        fm = parse_frontmatter(lines)
        doc_id = fm.get("Document ID")
        if not doc_id:
            continue  # FM-03 owns existence
        n_files += 1
        ids[doc_id].append(rel)

    findings: list[str] = []
    for doc_id, files in sorted(ids.items()):
        if len(files) > 1:
            findings.append(
                f"DD-01 {doc_id}: claimed by {len(files)} files - "
                + ", ".join(files))

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"doc_id_check: {len(findings)} duplicate Document ID(s) "
          f"across {n_files} ID-bearing files, {len(ids)} distinct IDs "
          f"in docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
