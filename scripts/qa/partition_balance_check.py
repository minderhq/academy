#!/usr/bin/env python3
"""Partition balance report (RB-01, tick-434): answers the loop
question "yeniden b\u00f6l\u00fcmlendirme gerekebilir?" with numbers, before
any re-partition is ever attempted.  Per top-level docs/ subtree,
per phase and per phase-module directory it reports md counts,
bytes, lesson shares, tree depth and the structural signals a
re-partition decision needs:

  HEAVY-DIR       - a directory holding > HEAVY_DIR_LIMIT md files
                    directly (re-partition hint, split needed)
  DEEP-PATH       - any md at depth > DEPTH_LIMIT from docs/
  KB-IMBALANCE    - one phase holding > IMBALANCE_RATIO x the
                    median phase payload bytes
  SINGLETON-LEAF  - single-file leaf directories that are NOT in
                    the two accepted patterns (see triage below)

Triage verdict (tick-434): single-file leaf dirs fall in two
accepted, deliberate patterns and are reported as accepted
texture, not signals - (a) phase-module guides/ subfolders, a
consistent NNNN-module/guides/NNNN-guide layout across all
phases, and (b) learning-resources category folders (cheat-sheets,
case-studies, interactive, troubleshooting, resources, bridges)
whose single file is the category seed and the folder is the
growth slot.  With those accepted, the tick-434 signal baseline
is 0; any NEW signal on a future tick is a re-partition review
input, not a failure - this stays a report-only tool, exit 0 by
design (same stance as curriculum_metrics/fm_staleness).

Models are borrowed for parity, not reinvented: phase/module/
lesson classification matches quality_report/curriculum_metrics
(phases live under docs/phases/phaseN-*/).  Output is
ASCII-escaped for cp1254 consoles.

Usage:
    python scripts/qa/partition_balance_check.py [--root REPO_ROOT]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PHASE_DIR = re.compile(r"^phase(\d+)-")
MODULE_DIR = re.compile(r"^(\d{4})-")
LESSON_FILE = re.compile(r"^(\d{4})-[^/]*\.md$")

HEAVY_DIR_LIMIT = 40   # md files directly in one directory
DEPTH_LIMIT = 6        # docs/ is depth 0
IMBALANCE_RATIO = 5.0

# accepted singleton-leaf categories (learning-resources seed dirs)
ACCEPTED_SINGLETON_PARENTS = {
    "learning-resources/bridges",
    "learning-resources/case-studies",
    "learning-resources/interactive",
    "learning-resources/resources",
    "learning-resources/troubleshooting",
}


def depth_of(rel: str) -> int:
    return rel.count("/")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(
        Path(__file__).resolve().parents[2]))
    args = ap.parse_args()
    docs = Path(args.root) / "docs"

    files = sorted(docs.rglob("*.md"))
    total = len(files)

    # top-level subtree rollup + per-phase rollup (phases split out)
    top: dict[str, dict] = {}
    phases: dict[str, dict] = {}
    for p in files:
        rel = p.relative_to(docs).as_posix()
        parts = rel.split("/")
        key = parts[0] if len(parts) > 1 else "(docs root)"
        d = top.setdefault(key, {"n": 0, "kb": 0.0, "lessons": 0,
                                 "maxd": depth_of(rel)})
        d["n"] += 1
        d["kb"] += p.stat().st_size / 1024
        d["maxd"] = max(d["maxd"], depth_of(rel))
        if LESSON_FILE.match(parts[-1]):
            d["lessons"] += 1
        if key == "phases" and len(parts) > 1 \
                and PHASE_DIR.match(parts[1]):
            pd = phases.setdefault(
                parts[1], {"n": 0, "kb": 0.0, "lessons": 0,
                           "maxd": depth_of(rel)})
            pd["n"] += 1
            pd["kb"] += p.stat().st_size / 1024
            pd["maxd"] = max(pd["maxd"], depth_of(rel))
            if LESSON_FILE.match(parts[-1]):
                pd["lessons"] += 1

    # per-directory subtrees for HEAVY-DIR
    heavy = []
    dirs: dict[str, dict] = {}
    for p in files:
        rel = p.relative_to(docs).as_posix()
        parent = Path(rel).parent.as_posix()   # posix: set parity
        if parent == ".":
            parent = "(docs root)"
        d = dirs.setdefault(parent, {"n": 0, "kb": 0.0})
        d["n"] += 1
        d["kb"] += p.stat().st_size / 1024
    for rel, d in dirs.items():
        if d["n"] > HEAVY_DIR_LIMIT:
            heavy.append((rel, d["n"], d["kb"]))

    # signals
    deep = []
    singletons = []
    accepted_texture = 0
    for p in files:
        rel = p.relative_to(docs).as_posix()
        parts = rel.split("/")
        if depth_of(rel) > DEPTH_LIMIT:
            deep.append((rel, depth_of(rel)))
        leaf = Path(rel).parent.as_posix()     # posix: set parity
        leaf_md = dirs.get(leaf, {}).get("n", 0) == 1 \
            and parts[-1].upper() != "README.MD"
        if not leaf_md:
            continue
        if parts[0] == "phases" and "guides" in parts:
            accepted_texture += 1          # guides/ pattern (a)
        elif leaf in ACCEPTED_SINGLETON_PARENTS:
            accepted_texture += 1          # category seed (b)
        else:
            singletons.append(rel)

    med_kb = (sorted(v["kb"] for v in phases.values())
              [len(phases) // 2] if phases else 0.0)
    imbalanced = [(k, v["kb"]) for k, v in phases.items()
                  if med_kb and v["kb"] > IMBALANCE_RATIO * med_kb]

    print("PROJECT-OMEGA partition balance (RB-01, report-only)")
    print("=" * 72)
    print(f"corpus: {total} md files across {len(top)} top-level "
          f"subtrees, {len(phases)} phases")
    print()
    print("top-level subtrees (md files / KB / lessons / max-depth):")
    for k, v in sorted(top.items(), key=lambda kv: -kv[1]["kb"]):
        print(f"  {k:34s} {v['n']:5d} md  {v['kb']:9.0f} KB  "
              f"{v['lessons']:4d} lessons  depth {v['maxd']}")
    print()
    print("phases (md files / KB / lessons / max-depth):")
    for k, v in sorted(phases.items()):
        print(f"  {k:34s} {v['n']:5d} md  {v['kb']:9.0f} KB  "
              f"{v['lessons']:4d} lessons  depth {v['maxd']}")
    print(f"  phase KB spread: median {med_kb:.0f}, "
          f"ratio max/median "
          f"{(max(v['kb'] for v in phases.values()) / med_kb) if med_kb else 0:.1f}x")
    print()
    sig = 0
    if heavy:
        sig += len(heavy)
        print(f"HEAVY-DIR (>{HEAVY_DIR_LIMIT} md directly in one "
              "directory - split candidate):")
        for rel, n, kb in sorted(heavy, key=lambda x: -x[1]):
            print(f"  {n:4d} md  {kb:8.0f} KB  {rel}/")
        print()
    if deep:
        sig += len(deep)
        print(f"DEEP-PATH (depth > {DEPTH_LIMIT} from docs/):")
        for rel, d in sorted(deep):
            print(f"  depth {d}  {rel}")
        print()
    if imbalanced:
        sig += len(imbalanced)
        print(f"KB-IMBALANCE (phase > {IMBALANCE_RATIO:.0f}x median "
              f"{med_kb:.0f} KB):")
        for k, kb in sorted(imbalanced, key=lambda x: -x[1]):
            print(f"  {kb:8.0f} KB  {k}")
        print()
    if singletons:
        sig += len(singletons)
        print("SINGLETON-LEAF (single non-README md in a leaf dir, "
              "no accepted pattern - relocate candidate):")
        for rel in singletons:
            print(f"  {rel}")
        print()
    print(f"accepted singleton texture: {accepted_texture} "
          "(phase-module guides/ dirs + learning-resources category "
          "seed dirs - deliberate patterns, triaged tick-434)")
    if sig == 0:
        print("partition signals: 0 -> structure is balanced; "
              "no re-partition pressure (baseline tick-434)")
    else:
        print(f"partition signals: {sig} -> re-partition review "
              "input; report only, exit 0 by design")
    print("partition_balance_check: report -> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
