#!/usr/bin/env python3
"""Phase-checkpoint coverage (CK-01..03, HARD) for PROJECT-OMEGA.

The phase CHECKPOINT.md is the learner's review page for everything
above it - the phase-exit self-assessment the platform will render
at the end of every phase. When a module group is added to a phase,
the checkpoint must grow with it, or the learner's phase review
silently covers only the older modules.

Born tick-472: the census measured phase-4's checkpoint still
claiming "Modules: 2 (4100, 4200)" - written in the two-module era
and never updated when 4300 (Quantization-Aware Training, 8
lessons) and 4400 (Advanced Techniques: GPTQ, AWQ, GGUF, EXL2,
sparsity, sub-1-bit, 9 lessons) joined the phase. Modules 4300/4400
had zero presence in the phase review; Estimated Time was frozen at
the 2-module "4-5 weeks". Drained the same tick (4-module overview,
4300/4400 checkpoint sections, goal + badge bullets, 5-7 weeks);
phases 1, 2, 3, 5, 6, 7 measured fully covered.

CK-00  a phase directory has no CHECKPOINT.md at all
CK-01  a module group is absent from the checkpoint text entirely
CK-02  the "**Modules:**" overview line miscounts or mislists the
       module groups
CK-03  a module group has no "### Module NNNN:" checkpoint section

HARD GATE - exit 1 on any finding. Born-at-zero after the tick-472
drain (same census -> drain -> gate cycle as NV-02).

Run over the whole corpus:
    python scripts/qa/checkpoint_coverage_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

GROUP_DIR = re.compile(r"^(\d{4})")
MODULES_LINE = re.compile(r"^\*\*Modules:\*\*\s*(\d+)\s*\(([^)]*)\)\s*$",
                          re.MULTILINE)
MODULE_SECTION = re.compile(r"^###\s+Module\s+(\d{4}):", re.MULTILINE)


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_phases = 0
    for phase_dir in sorted((args.root / "docs" / "phases").glob("phase*")):
        if not phase_dir.is_dir():
            continue
        n_phases += 1
        rel = os.path.relpath(phase_dir, args.root).replace("\\", "/")
        cp = phase_dir / "CHECKPOINT.md"
        groups = sorted({m.group(1) for sub in phase_dir.iterdir()
                         if sub.is_dir() and (m := GROUP_DIR.match(sub.name))})
        if not cp.exists():
            findings.append("CK-00 %s: phase has no CHECKPOINT.md" % rel)
            continue
        text = cp.read_text(encoding="utf-8", errors="replace")
        for gid in groups:
            if not re.search(r"\b%s\b" % gid, text):
                findings.append("CK-01 %s/CHECKPOINT.md: module group %s "
                                "absent from the phase review" % (rel, gid))
        ml = MODULES_LINE.search(text, re.MULTILINE)
        if ml is None:
            findings.append("CK-02 %s/CHECKPOINT.md: no '**Modules:**' "
                            "overview line" % rel)
        else:
            listed = [x.strip() for x in ml.group(2).split(",") if x.strip()]
            if int(ml.group(1)) != len(groups) or listed != groups:
                findings.append("CK-02 %s/CHECKPOINT.md: overview claims "
                                "%s (%s), actual %d (%s)"
                                % (rel, ml.group(1), ", ".join(listed),
                                   len(groups), ", ".join(groups)))
        sections = set(MODULE_SECTION.findall(text))
        for gid in groups:
            if gid not in sections:
                findings.append("CK-03 %s/CHECKPOINT.md: no '### Module %s:' "
                                "checkpoint section" % (rel, gid))

    for f in findings:
        print("  " + esc(f))
    print("checkpoint_coverage_scan: %d phase checkpoints; %d findings "
          "- all hard (CK-01 group absent / CK-02 overview miscount / "
          "CK-03 section missing; born tick-472 after the phase-4 "
          "two-module-era drain)" % (n_phases, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
