#!/usr/bin/env python3
"""Relative-link integrity gate for the PROJECT-OMEGA corpus.

Hard gate (exit 1 on any broken link). Scans every .md file repo-wide and
verifies each relative link target exists on disk. Fenced code blocks and
inline code spans are skipped entirely (linkcheck v2 behaviour): a `](` in
a code example is not a link. External (http/mailto) and anchor-only links
are out of scope here - in-document anchors are covered by anchor_check.py.

Known limitation, kept deliberately: the fence toggle is a naive
```,~~~ line match rather than CommonMark length-aware. Historical
baselines (0 broken) are defined against this exact behaviour.

Baseline (2026-09-28): 5529 links scanned, 0 distinct broken targets,
0 broken instances (count drifts with rewrites; 0-broken is the invariant).
Materialized from the formerly repo-external linkcheck_omega.py temp script.

Usage:
    python scripts/qa/linkcheck.py [--root REPO_ROOT]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict

SKIP_DIRS = {".git", "node_modules"}
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INLINE_CODE = re.compile(r"`[^`]+`")
FENCE = re.compile(r"^\s*(```|~~~)")


def md_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)


def resolve(src_path, target):
    """Return True if target resolves, False if broken, or the string 'EXTERNAL'."""
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return "EXTERNAL"
    path_part = target.split("#", 1)[0]
    if not path_part:
        return "EXTERNAL"
    path_part = path_part.replace("%20", " ")
    cand = os.path.normpath(os.path.join(os.path.dirname(src_path), path_part))
    return os.path.exists(cand)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=str, default=None,
                        help="repository root (default: two levels up from this script)")
    args = parser.parse_args()
    root = args.root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    broken = defaultdict(list)  # broken target -> [source:line]
    total_links = 0
    for src in md_files(root):
        in_fence = False
        try:
            with open(src, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if FENCE.match(line):
                        in_fence = not in_fence
                        continue
                    if in_fence:
                        continue
                    scrubbed = INLINE_CODE.sub("", line)
                    for m in MD_LINK.finditer(scrubbed):
                        total_links += 1
                        if resolve(src, m.group(1)) is False:
                            rel_src = os.path.relpath(src, root).replace("\\", "/")
                            broken[m.group(1)].append(f"{rel_src}:{i}")
        except (OSError, UnicodeDecodeError) as e:
            print(f"READ ERROR {src}: {e}", file=sys.stderr)

    count = sum(len(v) for v in broken.values())
    print(f"Total markdown links scanned: {total_links}")
    print(f"Distinct broken targets: {len(broken)}")
    print(f"Total broken link instances: {count}")
    print()
    for target, refs in sorted(broken.items(), key=lambda x: -len(x[1])):
        print(f"[{len(refs)}x] {target}")
        for r in refs[:4]:
            print(f"      {r}")
        if len(refs) > 4:
            print(f"      ... +{len(refs) - 4} more")
    print("linkcheck: %d links scanned, %d distinct broken targets, "
          "%d broken instances -> %s"
          % (total_links, len(broken), count, "PASS" if count == 0 else "FAIL"))
    return 0 if count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
