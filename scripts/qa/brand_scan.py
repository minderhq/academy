#!/usr/bin/env python3
"""brand_scan.py - verify the legacy brand name is fully retired.

The repository was rebranded to PROJECT-OMEGA (tick-187/188). This gate
reports every remaining mention of the old name in any of its written
forms (hyphenated identifier, title case, upper case). Exit 0 only when
the count is zero outside the QA tools themselves.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
VARIANTS = ["ai-engineering-curriculum", "AI Engineering Curriculum", "AI ENGINEERING CURRICULUM"]
SKIP_FILES = {"brand_scan.py", "legacy_ad_rename.py", "legacy_ad_scan.py"}

hits = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path.name in SKIP_FILES:
        continue
    if ".git" in path.parts or "node_modules" in path.parts:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    for variant in VARIANTS:
        if variant in text:
            for lineno, line in enumerate(text.split("\n"), start=1):
                if variant in line:
                    hits.append(f"{path.relative_to(ROOT).as_posix()}:{lineno}  [{variant}] {line.strip()[:80]}")

if hits:
    print(f"legacy brand mentions remaining: {len(hits)}")
    for h in hits[:20]:
        print(" ", h)
    sys.exit(1)
print("brand scan: 0 legacy mentions - PROJECT-OMEGA consistent")
