#!/usr/bin/env python3
"""Corpus-wide link reachability (report-only) for Minder Academy.

NV-01 proves every module doc is linked from ITS module README;
linkcheck proves links that exist resolve. Neither answers the
platform question: starting from the repo root README and clicking
markdown links, which docs can a learner (or the future platform
crawler) ever reach? A doc reachable from no entry point is stranded
content - invisible to browsing, un-crawlable, dead weight on the
shelf - even when every one of its own links is healthy.

This tool BFS-walks the .md link graph from the repo root README.md
(the single navigation entry point) and reports unreachable docs,
grouped by corpus area. It is the complement of the local gates:
NV checks in-degree from one parent, this checks global reach.

Birth census (2026-09-30, tick-471): 410 md files, 409 reachable -
CHANGELOG.md was the single stranded file (never linked from the
root README despite documenting the release history). Drained the
same tick: a Changelog row in the README Community > Resources
table plus a [1.2.0] release entry that brought the changelog
itself current. Zero unreachable from then on.

Report-only by doctrine: some unreachable classes could be
deliberate - project templates are copied, not browsed; working
meta-docs may be reached via platform config rather than links;
solutions live behind their lab's reveal flow. The report surfaces
the inventory so each unreachable doc is a decision, not an
accident.

    python scripts/qa/link_reach_report.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

MD_LINK = re.compile(r"\]\(\s*<?([^)#\s>]+\.md)(?:#[^)]*)?\s*(?:\"[^\"]*\")?\s*\)")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def norm(path: Path, root: Path) -> str:
    return os.path.relpath(path, root).replace("\\", "/").lower()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--seed", type=Path, default=Path("README.md"),
                        help="repo-relative entry point")
    args = parser.parse_args()

    seed = (args.root / args.seed)
    if not seed.exists():
        print("link_reach_report: seed %s missing" % args.seed)
        return 1

    all_md = {}
    for path in list(args.root.glob("*.md")) + list((args.root / "docs").rglob("*.md")):
        all_md[norm(path, args.root)] = path

    def resolve(src_rel: str, target: str) -> str | None:
        base = os.path.dirname(src_rel)
        t = os.path.normpath(os.path.join(base, target)).replace("\\", "/").lower()
        return t if t in all_md else None

    seen: set[str] = set()
    queue = [norm(seed, args.root)]
    while queue:
        cur = queue.pop()
        if cur in seen:
            continue
        seen.add(cur)
        text = all_md[cur].read_text(encoding="utf-8", errors="replace")
        for m in MD_LINK.finditer(text):
            nxt = resolve(cur, m.group(1))
            if nxt and nxt not in seen:
                queue.append(nxt)

    unreachable = sorted(set(all_md) - seen)
    by_area: dict[str, list[str]] = {}
    for rel in unreachable:
        parts = rel.split("/")
        if len(parts) < 2:
            area = "(repo root)"
        else:
            area = "/".join(parts[1:3]) if parts[0] == "docs" else parts[0]
            if parts[0] == "docs" and len(parts) == 2:
                area = "docs top-level"
        by_area.setdefault(area, []).append("/".join(parts[1:]) if parts[0] == "docs" else rel)

    print("link_reach_report: seed %s; %d md files, %d reachable, "
          "%d unreachable - REPORT-ONLY (templates/solutions/meta may "
          "be deliberate; each unreachable doc is a decision, not an "
          "accident)" % (args.seed.as_posix(), len(all_md), len(seen),
                         len(unreachable)))
    for area in sorted(by_area):
        print("  %s (%d)" % (area, len(by_area[area])))
        for rel in by_area[area]:
            print("    " + esc(rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
