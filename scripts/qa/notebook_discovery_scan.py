#!/usr/bin/env python3
"""notebook curriculum-discovery scan for Minder Academy.

Answers a platform question the markdown link graph cannot see: which
of the Jupyter notebooks can a learner actually find? link_reach_report
BFS-walks .md links only, so docs/notebooks/*.ipynb sit outside its
universe entirely, and MASTER-INDEX's Learning Resources tables listed
Tutorials, Labs, Cheat Sheets, Projects and Career Guides with no
notebooks row at all - the 20 notebooks' only inbound pointers were
their own directory's index README (reached via SITEMAP's collapsed
"Notebooks (1)" section). Runnable, tested content, invisible to the
browsing learner and to the future platform crawler.

This scan counts, per notebook, every inbound markdown link in the
repo, split by origin: CURRICULUM (any .md outside docs/notebooks/)
and SELF-INDEX (the notebooks directory's own README and neighbors).
A notebook with zero CURRICULUM inbound prints as NAV-ORPHAN -
stranded learning content. The honest fix is linking the notebook
from the curriculum navigation surfaces (MASTER-INDEX resource table,
SITEMAP's notebooks section), which is exactly what tick-549 did:
born at 20 NAV-ORPHAN, drained to 0 the same tick, and the dimension
stays under continuous lock from here on.

Report-only tool - exit 0 by design (same stance as
curriculum_metrics / lesson_similarity_scan / quiz_balance_scan):
an orphaned notebook is a review queue, not a failure.

Usage:
    python scripts/qa/notebook_discovery_scan.py [--root REPO_ROOT]
        [--out FILE]

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Same link shape linkcheck validates: [text](target "title")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

NB_DIRNAME = "docs/notebooks"


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    parser.add_argument("--out", type=Path, default=None,
                        help="additionally write the discovery table as a "
                             "JSON snapshot to this file (same feed idiom "
                             "as lesson_similarity_scan --out)")
    args = parser.parse_args()
    root = args.root.resolve()
    nbdir = (root / "docs" / "notebooks").resolve()

    notebooks = sorted(nbdir.glob("*.ipynb"))
    universe = {p.resolve().as_posix().lower(): p.name for p in notebooks}

    # inbound-link census over every markdown file in the repo
    curriculum: dict[str, int] = {p.name: 0 for p in notebooks}
    selfindex: dict[str, int] = {p.name: 0 for p in notebooks}
    sources: dict[str, set] = {p.name: set() for p in notebooks}
    mds = [p for p in root.rglob("*.md")]
    for md in mds:
        rel_md = md.resolve().relative_to(root).as_posix()
        in_nb_dir = md.resolve().parent == nbdir
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in MD_LINK.finditer(text):
            target = m.group(1).strip("<>").split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = os.path.normpath(
                os.path.join(str(md.parent), target))
            key = Path(resolved).resolve().as_posix().lower()
            name = universe.get(key)
            if name is None:
                continue
            if in_nb_dir:
                selfindex[name] += 1
            else:
                curriculum[name] += 1
                sources[name].add(rel_md)

    print("notebook_discovery_scan: %d notebooks, inbound-link census "
          "over %d md files (curriculum vs self-index)"
          % (len(notebooks), len(mds)))
    for p in notebooks:
        name = p.name
        tag = "" if curriculum[name] else "  NAV-ORPHAN"
        print("  %-42s curriculum=%d self=%d%s"
              % (esc(name), curriculum[name], selfindex[name], tag))
    orphans = [p.name for p in notebooks if not curriculum[p.name]]
    print("NAV-ORPHAN findings (zero curriculum-navigation inbound): %d"
          % len(orphans))
    print("notebook_discovery_scan: report only -> PASS")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "notebooks": len(notebooks),
            "md_files": len(mds),
            "rows": [{"file": p.name,
                      "curriculum_inbound": curriculum[p.name],
                      "selfindex_inbound": selfindex[p.name],
                      "sources": sorted(sources[p.name])}
                     for p in notebooks],
            "orphans": orphans,
        }
        args.out.write_text(json.dumps(snapshot, indent=1,
                                       ensure_ascii=True),
                            encoding="utf-8")
        print("wrote %s" % esc(str(args.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
