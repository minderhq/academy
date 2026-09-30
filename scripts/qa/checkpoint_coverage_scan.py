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

CK-06  the phase Completion Badge criteria block has no "All required
       modules completed" bullet - a completion badge that does not
       require module completion. The badge sits once per checkpoint
       (phase level, not module level); the bullet may carry the
       phase-1-style explicit module list "(1400, 1500)". Census
       tick-479: phases 4-7 listed only skill bullets, phase 2 said
       "All modules completed" - all drained the same tick.
CK-07  the badge criteria block carries fewer than 3 bullets
CK-08  badge-block shape drift: a criterion bullet with a decorated
       prefix (phase 1/4 carried checkmark-emoji bullets), or the
       "**Badge:**" line placed after the criteria block (phase 1) -
       corpus order is Badge, then "You've earned it when:"
CK-09  the phase checkpoint has no "## Common Pitfalls" section, or
       fewer than 4 numbered "**Name:**" items in it. The review page
       must consolidate the phase's failure modes before the badge
       (the deep wrong/correct examples live in the module files -
       the corpus's 29-file rich-pitfalls pattern). Census tick-480:
       phases 2-7 had no pitfalls section at all and phase 1 carried
       generic filler ("Rush Through: Take time to understand
       concepts") - drained the same tick with grounded, module-tied
       items (phase 1's from its own README pitfalls: MTU mismatch,
       GPU passthrough, rate limiting, storage class).

HARD GATE - exit 1 on any finding. Born-at-zero after the tick-472
drain (same census -> drain -> gate cycle as NV-02); CK-04/05 born
tick-478 after the 12-module Practical Verification drain; CK-06/07/08
born tick-479 after the badge-criteria drain; CK-09 tick-480 after
the grounded pitfalls drain.

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
EARN_HEAD = re.compile(r"^\*\*You've earned it when:\*\*\s*$", re.MULTILINE)
BADGE_LINE = re.compile(r"^\*\*Badge:\*\*", re.MULTILINE)
MODULES_DONE = re.compile(
    r"^- All required modules(?: \(\d{4}(?:, \d{4})*\))? completed$")
DECOR_BULLET = re.compile(r"^-\s*[^\w\s\-\[]")
PITFALLS_HEAD = re.compile(r"^##\s+Common Pitfalls\s*$", re.MULTILINE)
PITFALL_ITEM = re.compile(r"^\d+\.\s+\*\*[^*]+:\*\*")


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

        # CK-06/07/08: phase Completion Badge anatomy. The badge sits
        # once per checkpoint: the "**Badge:**" line first, then the
        # "You've earned it when:" criteria block, which must include
        # the module-completion criterion plus at least two more plain
        # (undecorated) bullets.
        badge_m = BADGE_LINE.search(text)
        earn_m = EARN_HEAD.search(text)
        if badge_m is None or earn_m is None:
            findings.append(
                "CK-06 %s/CHECKPOINT.md: no Completion Badge criteria "
                "block (**Badge:** + **You've earned it when:**)" % rel)
        else:
            bullets = []
            for ln in text[earn_m.start():].split("\n")[1:]:
                if ln.startswith("#") or ln.startswith("**") \
                        or ln.strip() == "---":
                    break
                if ln.startswith("- "):
                    bullets.append(ln)
            if not any(MODULES_DONE.match(b) for b in bullets):
                findings.append(
                    "CK-06 %s/CHECKPOINT.md: badge criteria lack the "
                    "'- All required modules completed' bullet" % rel)
            if len(bullets) < 3:
                findings.append(
                    "CK-07 %s/CHECKPOINT.md: badge criteria block carries "
                    "%d bullets - below the 3-criteria floor"
                    % (rel, len(bullets)))
            for b in bullets:
                if DECOR_BULLET.match(b):
                    findings.append(
                        "CK-08 %s/CHECKPOINT.md: badge criterion uses a "
                        "decorated bullet prefix: %s" % (rel, b[:50]))
                    break
            if badge_m.start() > earn_m.start():
                findings.append(
                    "CK-08 %s/CHECKPOINT.md: Badge line appears after the "
                    "criteria block - corpus order is Badge, then criteria"
                    % rel)

        # CK-09: the review page must consolidate the phase's failure
        # modes - a "## Common Pitfalls" section with at least 4
        # numbered "**Name:**" items (deep wrong/correct examples live
        # in the module files; the checkpoint carries the grounded list).
        pm = PITFALLS_HEAD.search(text)
        if pm is None:
            findings.append(
                "CK-09 %s/CHECKPOINT.md: no '## Common Pitfalls' section"
                % rel)
        else:
            n_items = 0
            for ln in text[pm.end():].split("\n")[1:]:
                if ln.startswith("#"):
                    break
                if PITFALL_ITEM.match(ln):
                    n_items += 1
            if n_items < 4:
                findings.append(
                    "CK-09 %s/CHECKPOINT.md: Common Pitfalls section "
                    "carries %d numbered '**Name:**' items - below the "
                    "4-pitfall floor" % (rel, n_items))

    for f in findings:
        print("  " + esc(f))
    print("checkpoint_coverage_scan: %d phase checkpoints; %d findings "
          "- all hard (CK-01 group absent / CK-02 overview miscount / "
          "CK-03 section missing / CK-04 quiz not exactly 3 items / "
          "CK-05 below the 3-checkbox hands-on floor / CK-06 badge "
          "criteria lack the modules-completion bullet / CK-07 badge "
          "criteria below the 3-bullet floor / CK-08 badge-block shape "
          "drift / CK-09 no Common Pitfalls section or below the "
          "4-pitfall floor; born tick-472 after the phase-4 "
          "two-module-era drain, CK-04/05 tick-478 after the 12-module "
          "Practical Verification drain, CK-06/07/08 tick-479 after the "
          "badge-criteria drain, CK-09 tick-480 after the grounded "
          "pitfalls drain)"
          % (n_phases, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
