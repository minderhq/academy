#!/usr/bin/env python3
"""Case-sensitive relative-link gate for the PROJECT-OMEGA corpus.

The main linkcheck gate resolves paths on the host OS: on Windows that is
case-insensitive, so a wrong-case href (e.g. `1500-Monitoring/` when the
directory on disk is `1500-monitoring/`) passes every local gate yet
breaks on GitHub Pages / Linux checkouts. This checker resolves hrefs
segment by segment against os.listdir with a case-sensitive comparison.

Hard gates (exit 1 on any finding):
  - case mismatches between href segments and on-disk names
  - missing relative targets (also caught by linkcheck; kept for a
    single-pass complete picture)
Report-only:
  - orphan md files (zero inbound relative links). Root README.md and any
    TEMPLATE.md are exempt by rule; CHANGELOG.md is the known-by-rule
    orphan (1 at baseline) since changelogs are intentionally unlinked.

Baseline (2026-09-28): 0 case mismatches / 0 missing / 1 known orphan.
Materialized from the formerly repo-external tick77_casecheck_omega.py
temp script.

Usage:
    python scripts/qa/casecheck.py [--root REPO_ROOT]

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.parse

SKIP_DIRS = {".git", ".claude", "node_modules", "__pycache__", ".venv", "venv"}
LINK = re.compile(r"\]\(([^)\s]+)\)")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def md_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.lower().endswith(".md"):
                out.append(os.path.join(dirpath, f))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=str, default=None,
                        help="repository root (default: two levels up from this script)")
    args = parser.parse_args()
    root = os.path.abspath(args.root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    md_files_list = md_files(root)
    mismatches = []  # (src, line, href, disk-actual)
    missing = []     # (src, line, href)
    targeted = set()  # normcase abs paths of successfully resolved targets
    total_links = 0

    for src in md_files_list:
        try:
            text = open(src, encoding="utf-8", newline="").read()
        except (OSError, UnicodeDecodeError) as e:
            print(esc("READ FAIL %s: %s" % (src, e)))
            continue
        in_fence = False
        for lineno, line in enumerate(text.split("\n"), 1):
            stripped = line.lstrip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            clean = re.sub(r"`[^`]*`", "", line)
            for m in LINK.finditer(clean):
                href = m.group(1)
                if href.startswith("<"):
                    href = href.strip("<>")
                if not href or href.startswith("#") or re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", href):
                    continue
                total_links += 1
                path_part = href.split("#")[0].split("?")[0]
                if not path_part:
                    continue
                path_part = urllib.parse.unquote(path_part)
                cur = os.path.dirname(src)
                segs = path_part.replace("\\", "/").split("/")
                resolved_last = None
                mismatch = None
                is_missing = False
                for seg in segs:
                    if seg in ("", "."):
                        continue
                    if seg == "..":
                        cur = os.path.dirname(cur)
                        resolved_last = cur
                        continue
                    target = os.path.join(cur, seg)
                    if os.path.exists(target):
                        if seg not in os.listdir(cur):
                            actual = [n for n in os.listdir(cur) if n.lower() == seg.lower()][0]
                            if mismatch is None:
                                rel_cur = os.path.relpath(cur, root)
                                mismatch = (href, "%s -> disk: %s" % (rel_cur.replace("\\", "/"), actual))
                        cur = target
                        resolved_last = cur
                    else:
                        is_missing = True
                        break
                rel_src = os.path.relpath(src, root).replace("\\", "/")
                if resolved_last is not None and not is_missing:
                    targeted.add(os.path.normcase(os.path.abspath(resolved_last)))
                if is_missing:
                    missing.append((rel_src, lineno, href))
                elif mismatch:
                    mismatches.append((rel_src, lineno, mismatch[0], mismatch[1]))

    print(esc("relative links checked: %d" % total_links))
    print()
    print(esc("=== CASE MISMATCHES (invisible on Windows, break on GitHub Pages/Linux): %d ===" % len(mismatches)))
    for s, l, href, actual in mismatches:
        print(esc(" - %s:%d  %s   [%s]" % (s, l, href, actual)))
    print()
    print(esc("=== MISSING (linkcheck gate already covers): %d ===" % len(missing)))
    for s, l, href in missing[:30]:
        print(esc(" - %s:%d  %s" % (s, l, href)))

    # orphan report: md files never targeted by any relative link
    print()
    orphans = []
    for f in md_files_list:
        ap = os.path.normcase(os.path.abspath(f))
        if ap in targeted:
            continue
        rel = os.path.relpath(f, root).replace("\\", "/")
        base = os.path.basename(f)
        if rel == "README.md" or base == "TEMPLATE.md":
            continue
        orphans.append(rel)
    print(esc("=== ORPHAN MD FILES (zero inbound relative links, README/TEMPLATE exempt): %d ===" % len(orphans)))
    for o in sorted(orphans):
        print(" -", esc(o))

    ok = not (mismatches or missing)
    print("casecheck: %d relative links, %d case mismatches, %d missing, "
          "%d orphan (report-only) -> %s"
          % (total_links, len(mismatches), len(missing), len(orphans),
             "PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
