#!/usr/bin/env python3
"""LangGraph legacy entry-point setter gate for the Minder Academy corpus.

LG-01  a python fence calling ``builder.set_entry_point(node)`` (or its
       finish twin ``set_finish_point``) teaches the legacy LangGraph
       spelling on an API whose modern form the corpus itself teaches:
       entry is the START pseudo-node (``builder.add_edge(START, node)``).
       The 7300 orchestration guide says it verbatim - "set_entry_point
       still works but is the legacy spelling" - so a reader copying an
       exercise solution or a cheat-sheet snippet learns the exact form
       the corpus labels legacy, and the worst fences mixed both worlds
       in one block (a modern ``add_edge(x, END)`` finish edge beside a
       legacy entry setter). The calls still run today, so nothing
       crashes - the defect is the corpus vouching an API it calls
       legacy somewhere else, the standardization face of the modernity
       mandate: lessons, exercises and cheat sheets must speak one
       spelling of the same mechanism.

No gate owned the class: legacy_chain_scan walks bare Name loads of
the removed langchain_classic surface (a different library, a Name
not an Attribute call), deprecated_scan's vocabulary is
datetime/torch/pydantic faces, kwarg_lint walks constructor kwargs,
and no sibling reads method-call names on builder objects - the
Attribute-call surface was syntactically legal everywhere,
defect-owned nowhere.

The scan is fence-aware by design (same two-pass model as
kwarg_lint/fence_namecheck/legacy_chain_scan): the class is a CALL,
and calls live in python fences. Prose stays out of the class by
construction because the paren-less prose mention is the affirmative
teaching form - the 7303 mapping sentence ("set_entry_point still
works but is the legacy spelling") is exactly the sentence a reader
needs, and an AST walk cannot see it anyway. Comments and strings
are out of scope (ast.Call nodes do not include them).

Out of the class by construction:

  - ``builder.add_edge(START, node)`` - the modern affirmative form
    the lessons teach (7300 README, tick-676 interrupt fence).
  - ``add_edge(a, b)`` between real nodes and to END - always current.
  - ``add_conditional_edges`` - the modern conditional surface.
  - prose/backtick mentions without call parens - the teaching form.
  - notebooks (.ipynb) are outside the md universe.

Born census tick-677 read every python fence corpus-wide = exactly
2 findings (the 7300 PRACTICE Exercise 3 solution and the VOLUME-7
cheat-sheet snippet, both legacy ``set_entry_point`` calls inside
fences that already carried a modern ``add_edge(x, END)`` finish
edge - the mixed-spelling worst shape). Drained the same tick BEFORE
the gate landed (the tick-675 inverted protocol): both calls became
``add_edge(START, ...)`` and both fences' langgraph.graph import
lines gained START, zero line shift so every exec-census baseline
row keeps its coordinates - returning the class to born-at-zero,
hard from the rule's naming (the SS-01 zero-drain shape).

Hard gate (exit 1 on findings): the class has no legitimate form -
a legacy-setter call in a teaching fence is the defect by definition,
teaching or not.

Run over the whole corpus:
    python scripts/qa/legacy_langgraph_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

# the legacy LangGraph graph-builder setters; the modern surface builds
# the same edges with add_edge(START|END, ...) and add_conditional_edges.
LEGACY_SETTERS = {
    "set_entry_point",
    "set_finish_point",
}


def scan_trees(rel: str, trees: list[tuple[ast.AST, int]],
               findings: list[str], counts: dict[str, int]) -> None:
    for tree, line_offset in trees:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in LEGACY_SETTERS:
                continue
            counts["LG-01"] += 1
            findings.append(
                f"{rel}:{node.lineno + line_offset}: "
                f"LG-01 legacy setter '{func.attr}' - the modern "
                f"LangGraph surface builds this edge with "
                f"add_edge(START|END, node); the corpus teaches the "
                f"START-edge form and calls the setter the legacy "
                f"spelling - use the modern form")


def scan_file(root: Path, path: Path, findings: list[str],
              counts: dict[str, int]) -> None:
    rel = path.relative_to(root).as_posix()
    in_fence = False
    lang = ""
    chunk: list[str] = []
    chunk_start = 0
    trees: list[tuple[ast.AST, int]] = []

    def flush() -> None:
        if not chunk:
            return
        try:
            trees.append((ast.parse("\n".join(chunk)), chunk_start - 1))
        except SyntaxError:
            pass  # CB-01 owns fence syntax; skip unparseable chunks

    for lineno, raw in enumerate(path.read_text(encoding="utf-8")
                                 .split("\n"), start=1):
        m = FENCE_RE.match(raw)
        if m:
            if in_fence and lang == "python":
                flush()
            in_fence = not in_fence
            lang = "" if not in_fence else m.group(2).lower()
            chunk = []
            chunk_start = lineno
            continue
        if in_fence and lang == "python":
            if not chunk:
                chunk_start = lineno
            chunk.append(raw)
    flush()

    if not trees:
        return
    scan_trees(rel, trees, findings, counts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    counts = {"LG-01": 0}
    n_files: set[str] = set()
    for path in sorted(docs.rglob("*.md")):
        try:
            before = len(findings)
            scan_file(args.root, path, findings, counts)
            if len(findings) > before:
                n_files.add(path.relative_to(args.root).as_posix())
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"legacy_langgraph_scan: {len(findings)} findings "
          f"(LG-01 legacy LangGraph entry/finish setters: {counts['LG-01']}) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
