#!/usr/bin/env python3
"""Case-sensitive relative-link gate for the Minder Academy corpus.

The main linkcheck gate resolves paths on the host OS: on Windows that is
case-insensitive, so a wrong-case href (e.g. `1500-Monitoring/` when the
directory on disk is `1500-monitoring/`) passes every local gate yet
breaks on GitHub Pages / Linux checkouts. This checker resolves hrefs
segment by segment against os.listdir with a case-sensitive comparison.

Hard gates (exit 1 on any finding):
  - case mismatches between href segments and on-disk names
  - missing relative targets (also caught by linkcheck; kept for a
    single-pass complete picture). A segment the OS swallows via path
    normalization (Win32 strips trailing dots/spaces, so `...` or
    `name.` exists()-true yet matches no on-disk name) resolves as
    MISSING, never a crash - hardening tick-637, born from the
    tick-636 fleet-trap where such a href crashed this resolver with
    a bare IndexError and no diagnostic.
  - orphan md files with zero inbound relative links - since
    2026-09-30. A content doc no nav link points at is invisible to
    the platform browse graph: it cannot be reached by clicking, only
    by search. Exempt by rule: root README.md (the entry doc), any
    TEMPLATE.md, and CHANGELOG.md (changelogs are intentionally
    unlinked - the known-by-rule orphan, 1 at baseline). Any NEW
    orphan must arrive with the link that surfaces it.

Baseline (2026-09-28): 0 case mismatches / 0 missing / 1 known orphan.
Materialized from a formerly repo-external verification temp script.

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
                            matches = [n for n in os.listdir(cur) if n.lower() == seg.lower()]
                            if not matches:
                                # exists() lied: the OS normalized the segment
                                # (Win32 strips trailing dots/spaces), so no
                                # on-disk name resolves it - a broken target,
                                # not a case variant. Missing, never a crash.
                                is_missing = True
                                break
                            actual = matches[0]
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

    # orphan gate: md files never targeted by any relative link
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
    known_orphans = {"CHANGELOG.md"}  # changelogs are intentionally unlinked
    unexpected = [o for o in orphans if os.path.basename(o) not in known_orphans]
    print(esc("=== ORPHAN MD FILES (zero inbound relative links, README/TEMPLATE/CHANGELOG exempt): %d (%d unexpected) ===" % (len(orphans), len(unexpected))))
    for o in sorted(orphans):
        tag = "" if os.path.basename(o) in known_orphans else "  <- HARD"
        print(" -", esc(o) + tag)

    ok = not (mismatches or missing or unexpected)
    print("casecheck: %d relative links, %d case mismatches, %d missing, "
          "%d orphan (%d unexpected - hard since 2026-09-30) -> %s"
          % (total_links, len(mismatches), len(missing), len(orphans),
             len(unexpected), "PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
