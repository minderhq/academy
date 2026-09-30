#!/usr/bin/env python3
"""Model-name form consistency (report-only) for PROJECT-OMEGA.

Vendors ship every model in two forms: the space form in prose and
paper titles ("Mistral 7B", "Llama 2 7B") and the hyphen form in
repo ids and model cards (mistralai/Mistral-7B-v0.1). The tick-470
census found the corpus follows the same organic convention - prose
sentences space-form, spec/benchmark/VRAM table rows hyphen-form -
but carried context mismatches on both sides, drained the same tick:
11 table rows space-in-table (3402 spec, phase1 throughput+memory,
CP-001 cost) and 16 prose/heading sites hyphen-in-prose (5104,
LAB-003, 3403, the phase-4 KV-cache and phase-5 LoRA objective
bullets, PRACTICE task). The rule is codified in STYLE-GUIDE
"Name Forms (prose vs identifiers)".

MF-01  a space-form checkpoint inside a table row
MF-02  a hyphen-form checkpoint in non-table prose

Known intended hits at birth (KEEP, each documented):
  - QUICK-START "What You Just Learned" concept-definition row
    (| **Mistral 7B** |): a definitional gloss, not a benchmark row
  - REAL-WORLD-EXAMPLES Tech Stack line: comma-enumeration of
    identifiers
  - TGI guide "(TheBloke/Mistral-7B-Instruct-v0.2-AWQ, ...)": a
    full repo id inside a prose parenthetical
  - VOLUME-4 capstone "(Llama-2-70B or similar)": names the model
    to download
  - GUIDE-CAREER resume-bullet quote (skipped by pattern): an
    example artifact

Family-name rows ("| **Llama 2** |") never match: MF-01 requires a
size token. Official variant names are excluded by pattern
(Llama-2-Chat, Llama-2-Long); LLaMA-7B physics tables are tick-469
doctrine and out of scope (LLaMA spelling, not Llama).

REPORT-ONLY by doctrine: the identifier-vs-prose boundary needs
human judgment at the edges; this tool surfaces drift, never gates.

    python scripts/qa/model_form_report.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(```|~~~)")  # CommonMark: <=3 leading spaces
FM_CLOSE = re.compile(r"^---\s*$")
TABLE = re.compile(r"^\s*[|\u2502]")
INLINE_CODE = re.compile(r"`{2,}[^`]*`{2,}|`[^`]*`")
QUOTED_ARTIFACT = re.compile(r'^\s*-\s"')

S_VENDOR = re.compile(r"\b(?:Mistral|Gemma|Qwen|Falcon)\s\d+(?:\.\d+)?[Bb]\b")
S_LLAMA = re.compile(r"\bLlama\s\d+(?:\.\d+)?\s\d+B\b")
H_VENDOR = re.compile(r"\b(?:Mistral|Gemma|Qwen|Falcon)-\d+(?:\.\d+)?B\b")
H_LLAMA = re.compile(
    r"\bLlama-\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?B)?\b(?!-Chat)(?!-Long)")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def body_lines(text: str) -> list[str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return lines
    for i, ln in enumerate(lines[1:40], 1):
        if FM_CLOSE.match(ln):
            return lines[i + 1:]
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    mf01: list[str] = []
    mf02: list[str] = []
    n_docs = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        n_docs += 1
        rel = os.path.relpath(path, args.root).replace("\\", "/")
        lines = body_lines(path.read_text(encoding="utf-8",
                                          errors="replace"))
        in_fence = False
        for i, ln in enumerate(lines, 1):
            if FENCE.match(ln):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            scrub = INLINE_CODE.sub("", ln)
            if TABLE.match(scrub):
                if S_VENDOR.search(scrub) or S_LLAMA.search(scrub):
                    mf01.append(f"{rel}:{i}: {scrub.strip()[:60]}")
            elif not QUOTED_ARTIFACT.match(scrub):
                if H_VENDOR.search(scrub) or H_LLAMA.search(scrub):
                    mf02.append(f"{rel}:{i}: {scrub.strip()[:60]}")

    for loc in mf01:
        print("  MF-01 " + esc(loc))
    for loc in mf02:
        print("  MF-02 " + esc(loc))
    print("model_form_report: %d docs; %d MF-01 space-in-table, %d "
          "MF-02 hyphen-in-prose - REPORT-ONLY (identifier-vs-prose "
          "boundary needs judgment; birth hits above are documented "
          "intended uses, see module docstring; rule codified in "
          "STYLE-GUIDE Name Forms)" % (n_docs, len(mf01), len(mf02)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
