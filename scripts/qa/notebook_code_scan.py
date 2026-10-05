#!/usr/bin/env python3
"""notebook code-cell gate (NBC-01..02) for Minder Academy.

The .md AST gate family never sees notebook code: codeblock_syntax_scan
and fence_import_check walk CommonMark fences in docs/**/*.md, while
docs/notebooks/*.ipynb code cells are JSON - a notebook teaching broken
code ships to the platform crawler, the launcher runs it, and the
learner hits the failure mid-lesson. NBC extends the fence-gate
judgments to the notebook universe.

NBC-01  code-cell syntax: ast.parse fails on a cell's joined source -
        the same guarantee codeblock_syntax_scan gives every ```python
        fence (CB-01), applied per cell. Cell indices are 0-based
        positions in the file's `cells` list (markdown cells count).

NBC-02  unresolvable import root: a top-level import root that neither
        resolves against the kurulu-stack nor belongs to the corpus
        class - fence_import_check's IC-01 judgment, mirrored
        mechanism-for-mechanism (import_module with a verdict cache,
        dotted-ancestor class matching, relative imports skipped and
        counted). A syntax-failed cell is an NBC-01 finding and its
        imports are not walked (there is no AST to walk).

Structural health (unparseable JSON, malformed cells/sources) is
NBH-03's jurisdiction - NBC silently skips what NBH flags, and the
NEG face is the designed cross-gate agreement, not a gap.

The corpus class (born tick-691 from the probe census, the same
census->classify->lock path fence_import_check took at tick-323/325):
alternative / optional third-party stacks the notebooks deliberately
reference without requiring installation, each one declared by the
corpus's own dependency surfaces - ENVIRONMENT-SETUP.md installs
chromadb, sentence-transformers and trl via `uv pip install`
(LAB-003 pins trl>=1.14.0 via `uv add`, 4102 teaches
`uv pip install optimum`, SOL-001 pins sentence-transformers==6.1.0).
A root outside the class means a learner hits ModuleNotFoundError as
written: exit 1.

Born tick-691 from the probe census: 20 notebooks, 224 cells (102
code), syntax_fails=2 -> both real defects drained this tick (NB-203
cell 7 - a quote-collision raw regex string that terminated early;
NB-703 cell 5 - a literal backslash-n inside a list tail), and
unresolvable_roots=4 (sentence_transformers x4, optimum x1, trl x1,
chromadb x1) -> all classified into the corpus class. Born at zero,
hard-gated so the broken-teaching class can never regrow.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-691).

Run over the whole corpus:
    python scripts/qa/notebook_code_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import sys
from pathlib import Path

for _pkg in ("torch", "pydantic"):
    try:
        importlib.import_module(_pkg)
    except ImportError:  # environment problem, not a doc problem
        print(f"notebook_code_scan: {_pkg} not importable in this "
              "interpreter - NBC-02 resolves cell imports against the "
              "kurulu-stack; run the scorecard with that python "
              "(see ENVIRONMENT-SETUP.md)")
        sys.exit(2)

# The corpus class for the notebook universe (born tick-691): the
# alternative/optional third-party stacks the notebooks deliberately
# reference, each declared by the corpus's own dependency surfaces
# (ENVIRONMENT-SETUP.md uv pip lines, LAB-003's uv add line, 4102's
# uv pip install optimum, SOL-001's requirements block). Dotted
# ancestors match, so optimum.bettertransformer is accepted without
# weakening the gate for a genuinely-missing root.
NBC_ACCEPTED = frozenset({
    "chromadb", "optimum", "sentence_transformers", "trl",
})

_verdict_cache: dict[str, bool] = {}


def resolves(root: str) -> bool:
    """True when the import root resolves against the kurulu-stack."""
    if root in _verdict_cache:
        return _verdict_cache[root]
    try:
        importlib.import_module(root)
        ok = True
    except Exception:  # noqa: BLE001 - any failure means "cannot run"
        ok = False
    _verdict_cache[root] = ok
    return ok


def accepted(root: str) -> bool:
    """True when root or a dotted ancestor is a corpus class member."""
    while root:
        if root in NBC_ACCEPTED:
            return True
        root = root.rpartition(".")[0]
    return False


def cell_source(cell: dict) -> str:
    src = cell.get("source")
    if isinstance(src, list):
        return "".join(s for s in src if isinstance(s, str))
    return src if isinstance(src, str) else ""


def scan_nb(root: Path, path: Path, findings: list[str],
            stats: list[int]) -> None:
    rel = path.relative_to(root).as_posix()
    try:
        nb = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        stats[2] += 1  # structural-health jurisdiction: NBH-03 flags it
        return
    if not isinstance(nb, dict) or not isinstance(nb.get("cells"), list):
        stats[2] += 1
        return
    for idx, cell in enumerate(nb["cells"]):
        if not isinstance(cell, dict) or cell.get("cell_type") != "code":
            continue
        stats[1] += 1
        if not isinstance(cell.get("source"), (str, list)):
            stats[2] += 1  # NBH-03 jurisdiction
            continue
        src = cell_source(cell)
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            findings.append(
                f"{rel}: NBC-01 code cell {idx} fails to parse - "
                f"{exc.msg}")
            continue
        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    stats[3] += 1  # relative: no package context, skipped
                    continue
                root_name = (node.module or "").split(".")[0]
                if root_name:
                    roots.add(root_name)
        for root_name in sorted(roots):
            if accepted(root_name) or resolves(root_name):
                stats[4] += 1
            else:
                findings.append(
                    f"{rel}: NBC-02 import root '{root_name}' in code "
                    f"cell {idx} does not resolve and is outside the "
                    f"corpus class - a learner hits "
                    f"ModuleNotFoundError as written")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []
    stats = [0, 0, 0, 0, 0]  # notebooks, code cells, NBH-skipped, rel, ok
    for path in sorted((args.root / "docs" / "notebooks").glob("*.ipynb")):
        stats[0] += 1
        scan_nb(args.root, path, findings, stats)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"notebook_code_scan: {len(findings)} findings "
          f"(NBC-01 code-cell syntax / NBC-02 unresolvable import root; "
          f"{stats[4]} import(s) accepted, {stats[3]} relative skipped, "
          f"{stats[2]} cell(s) left to NBH-03) across {stats[0]} "
          f"notebooks / {stats[1]} code cells in docs/notebooks/ "
          f"(hard; born tick-691 at zero - 2 real syntax defects "
          f"drained, 4 unresolvable roots corpus-classified)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
