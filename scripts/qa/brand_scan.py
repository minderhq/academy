#!/usr/bin/env python3
"""brand_scan.py - verify every retired brand name is fully gone.

The repository was rebranded to PROJECT-OMEGA (tick-187/188), then to
Minder Academy for the minderhq/academy publish (this tick). This gate
reports every remaining mention of any retired name in its written
forms: the pre-187 curriculum token, the PROJECT-OMEGA family
(PROJECT-OMEGA / project-omega / project_omega), the legacy subtitle
(Neural-Architect) and the bare omega infra tokens (containers,
networks, node names, cluster domains, tempfile prefixes). Exit 0 only
when the count is zero outside the QA tools themselves.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# The robustness audit (tick-638) passes --root <tree>; honor it, else scan
# this repo (the historical default) - a relocated copy must not rglob the
# whole parent tree (the NEG finding: a staged copy walked the parent dir).
_argv = sys.argv[1:]
ROOT = (Path(_argv[_argv.index("--root") + 1]) if "--root" in _argv
        else Path(__file__).resolve().parents[2])
VARIANTS = ["ai-engineering-curriculum", "AI Engineering Curriculum", "AI ENGINEERING CURRICULUM",
            "PROJECT-OMEGA", "project-omega", "project_omega", "Neural-Architect",
            "omega", "Omega"]
SKIP_FILES = {"brand_scan.py", "legacy_ad_rename.py", "legacy_ad_scan.py"}

hits = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path.name in SKIP_FILES:
        continue
    if (".git" in path.parts or "node_modules" in path.parts
            or ".venv" in path.parts or "venv" in path.parts):
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
print("brand scan: 0 legacy mentions - Minder Academy consistent")
