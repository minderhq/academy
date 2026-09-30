#!/usr/bin/env python3
"""Phase-checkpoint coverage and module anatomy (CK-00..05, HARD) for PROJECT-OMEGA.

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

CK-04  a module checkpoint section has no Checkpoint Quiz, or its
       quiz is not exactly 3 items - the corpus-wide shape (33/33
       at the tick-478 census; the quiz is the module's self-test,
       and a missing or truncated one breaks the per-module
       completion ritual the platform renders)
CK-05  a module checkpoint section carries fewer than 3 "- [ ]"
       checkboxes - the hands-on verification floor. Vocabulary
       varies legitimately (Practical Verification in the modern
       blocks, Lab Verification for lab-completion checks, phase
       1's richer Knowledge Check / Practical Skills /
       Troubleshooting trio), so the gate counts the checkbox
       floor across the whole block rather than freezing one
       header word. Census tick-478: 12 modules had no checkbox
       section at all; drained the same tick (3 skill checkboxes
       each, grounded in the module's quiz and labs).

HARD GATE - exit 1 on any finding. Born-at-zero after the tick-472
drain (same census -> drain -> gate cycle as NV-02); CK-04/05 born
tick-478 after the 12-module Practical Verification drain.

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
MODULE_BLOCK = re.compile(r"^###\s+Module\s+(\d{4}):.*?(?=^### |^## |\Z)",
                          re.DOTALL | re.MULTILINE)
QUIZ_HEAD = re.compile(r"^\*\*Checkpoint Quiz:\*\*\s*$")
QUIZ_ITEM = re.compile(r"^\s*(\d+)[\.\)]\s+\S")
CHECKBOX = re.compile(r"^\s*-\s+\[[ x]\]")


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

        # CK-04/05: per-module anatomy. Every module section carries a
        # 3-item Checkpoint Quiz (the self-test) and at least 3
        # checkboxes (the hands-on floor, however the block names it).
        for bm in MODULE_BLOCK.finditer(text):
            gid = bm.group(1)
            q_items = 0
            boxes = 0
            in_q = False
            for ln in bm.group(0).split("\n"):
                if QUIZ_HEAD.match(ln):
                    in_q = True
                    continue
                if in_q and (ln.startswith("**") or ln.startswith("#")
                             or ln.strip() == "---"):
                    in_q = False
                if in_q and QUIZ_ITEM.match(ln):
                    q_items += 1
                if CHECKBOX.match(ln):
                    boxes += 1
            if q_items != 3:
                findings.append(
                    "CK-04 %s/CHECKPOINT.md: module %s Checkpoint Quiz has "
                    "%d items, corpus standard is 3" % (rel, gid, q_items))
            if boxes < 3:
                findings.append(
                    "CK-05 %s/CHECKPOINT.md: module %s carries %d checkbox "
                    "items - below the 3-checkbox hands-on floor"
                    % (rel, gid, boxes))

    for f in findings:
        print("  " + esc(f))
    print("checkpoint_coverage_scan: %d phase checkpoints; %d findings "
          "- all hard (CK-01 group absent / CK-02 overview miscount / "
          "CK-03 section missing / CK-04 quiz not exactly 3 items / "
          "CK-05 below the 3-checkbox hands-on floor; born tick-472 "
          "after the phase-4 two-module-era drain, CK-04/05 tick-478 "
          "after the 12-module Practical Verification drain)"
          % (n_phases, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
