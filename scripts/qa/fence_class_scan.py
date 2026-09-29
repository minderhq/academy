#!/usr/bin/env python3
"""Fence-class registry gate for the PROJECT-OMEGA corpus.

fence_label_scan locks that every open fence CARRIES a lowercase label
(FL-01/02); this gate locks that every label is CLASSIFIED. A label
must be one of:

  - parser-validated (VALIDATED): python, bash, json, yaml, mermaid -
    a syntax gate owns the content (CB-01 / BB-01 / DB-01/02 /
    MM-01..03), so these classes are code with a judge.

  - explicitly accepted (ACCEPTED): the tick-285 census inventory of
    unvalidated classes - prose dumps (text, markdown), operational
    config with no stdlib parser (dockerfile, powershell, nginx,
    cypher, cuda, promql, cron, gitignore), and small teaching samples
    (html, typescript, tsx, sql, cpp, c). Unvalidated is a deliberate
    classification, not an accident.

Anything else is FC-01: an invisible code class. Real code no gate
sees is an audit hole (a ``toml`` fence would silently skip every
data-block gate), and a platform load step cannot tell executable
fences from prose without the class being declared. Born from the
tick-285 label census (21 distinct labels across 4243 open fences;
5 validated, 16 accepted), baseline 0 at birth.

A new class entering the corpus lands here as a finding: teach a
parser gate for it or classify it here - the same
change-means-teach-the-tool contract as the claims gates' regex
idiom.

Fence model: the shared family idiom (fence_label_scan et al.) -
length-aware ticks + blockquote prefix.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-286).

Run over the whole corpus:
    python scripts/qa/fence_class_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Shared family idiom: length-aware ticks + blockquote prefix.
FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")

VALIDATED = {"python", "bash", "json", "yaml", "mermaid"}

ACCEPTED = {
    "text", "markdown",                       # prose by design
    "dockerfile", "powershell", "nginx",      # operational config, no
    "cypher", "cuda", "promql", "cron",       # stdlib parser available
    "gitignore",
    "html", "typescript", "tsx", "sql",       # small teaching samples
    "cpp", "c",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []
    n_files: set[str] = set()
    blocks = 0
    classes: set[str] = set()
    for path in sorted((args.root / "docs").rglob("*.md")):
        rel = path.relative_to(args.root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        state = 0
        before = len(findings)
        for raw in lines:
            m = FENCE_RE.match(raw)
            if m:
                ticks, lang = len(m.group(1)), m.group(2)
                if state and not lang and ticks >= state:
                    state = 0
                elif not state:
                    state = ticks
                    blocks += 1
                    classes.add(lang)
                    if lang not in VALIDATED and lang not in ACCEPTED:
                        findings.append(
                            f"{rel}: FC-01 unknown fence label class "
                            f"'{lang}' - invisible code: no parser gate "
                            f"owns it and no classification accepts it; "
                            f"teach a parser gate or add it to "
                            f"fence_class_scan's registry")
        if len(findings) > before:
            n_files.add(rel)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"fence_class_scan: {len(findings)} findings "
          f"(FC-01 unknown fence label class - invisible code no gate "
          f"owns; teach a parser gate or classify it) in "
          f"{len(n_files)} files; {len(VALIDATED)} validated + "
          f"{len(ACCEPTED)} accepted = {len(classes)} classes in use "
          f"across {blocks} fences in docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
