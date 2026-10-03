#!/usr/bin/env python3
"""legacy_ad_scan.py - classify remaining `ai-engineering-curriculum` mentions.

Reports every occurrence bucketed by context class so remediation can be
per-class instead of a blind replace:

  github-url   inside a github.com/<owner>/ai-engineering-curriculum URL
  git-op       clone/pip git+https install line
  path-prefix  used as a path segment (.../ai-engineering-curriculum/...)
  bare-token   anything else (prose mention, frontmatter, heading...)

Exit code is 0 always - this is a survey tool, not a gate.
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# The robustness audit (tick-638) passes --root <tree>; honor it, else scan
# this repo (the historical default) - a relocated copy must not rglob the
# whole parent tree (the NEG finding: a staged copy walked the parent dir).
_argv = sys.argv[1:]
ROOT = (Path(_argv[_argv.index("--root") + 1]) if "--root" in _argv
        else Path(__file__).resolve().parents[2])
TOKEN = "ai-engineering-curriculum"
SAMPLES_PER_CLASS = 6
MAX_LINE = 110

URL_RE = re.compile(r"github\.com/[^\s`)\]]*?" + TOKEN)
CLONE_RE = re.compile(r"\bgit clone\b|git\+https")

classes: Counter[str] = Counter()
per_file: dict[str, Counter] = defaultdict(Counter)
samples: dict[str, list[str]] = defaultdict(list)

paths = sorted(ROOT.rglob("*.md"))
skipped = 0
for path in paths:
    rel = path.relative_to(ROOT).as_posix()
    if ".git" in path.parts or "node_modules" in path.parts:
        skipped += 1
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"warn: non-utf8 file skipped: {rel}")
        continue
    if TOKEN not in text:
        continue
    for lineno, line in enumerate(text.split("\n"), start=1):
        if TOKEN not in line:
            continue
        if URL_RE.search(line):
            cls = "github-url"
        elif CLONE_RE.search(line):
            cls = "git-op"
        elif re.search(TOKEN + r"[\w.-]*/", line):
            cls = "path-prefix"
        else:
            cls = "bare-token"
        classes[cls] += 1
        per_file[rel][cls] += 1
        shown = line.strip()
        if len(shown) > MAX_LINE:
            shown = shown[: MAX_LINE - 3] + "..."
        if len(samples[cls]) < SAMPLES_PER_CLASS:
            samples[cls].append(f"{rel}:{lineno}  {shown}")

print("legacy-ad survey (token: ai-engineering-curriculum)")
print("=" * 72)
print(f"files with hits: {len(per_file)}   occurrences: {sum(classes.values())}")
print()
for cls, n in classes.most_common():
    print(f"{cls:13s} {n:5d}")
print()
for cls, _n in classes.most_common():
    print(f"--- samples: {cls} ---")
    for s in samples[cls]:
        print(" ", s)
    print()

print("top files by hits:")
flat = sorted(per_file.items(), key=lambda kv: sum(kv[1].values()), reverse=True)
for rel, ctr in flat[:12]:
    print(f"  {sum(ctr.values()):4d}  {rel}")
