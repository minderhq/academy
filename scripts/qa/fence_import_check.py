#!/usr/bin/env python3
"""Import-resolution gate for every ```python fence in the corpus.

Generalizes langchain_census (LC-01, langchain-family only) to every
import in every python fence: an import line that does not resolve
against the kurulu-stack means a learner following the lesson hits
ModuleNotFoundError, i.e. the lesson teaches code that cannot run.

IC-01  import does not resolve (module missing or name absent)

Design, inherited from the gates this generalizes:
- the fence universe is codeblock_syntax_scan's exactly (exact ```
  / ~~~ markers, python/py/python3 labels, textwrap.dedent before
  parsing), so the two gates always see the same blocks - and CB-01's
  baseline-0 parse guarantee means ast.parse never fails here
- fences are parsed with ast, so multi-line paren imports, semicolon
  one-liners and `as` aliases all resolve - the blind spots
  langchain_census documents away are simply gone here
- stdlib always resolves; first-party teaching modules and deliberate
  references to packages outside the stack surface in the census for
  classification, the same census->classify->lock path every gate took
- conditional `try: import x / except ImportError:` graceful-degradation
  teaching texture is still found (the import line exists as written)
- relative imports (from . import x) have no package context inside a
  fence fragment - skipped and counted, not findings

Report mode at birth (tick-323): findings are a census to classify,
not a failure - the gate goes hard only after the finding class is
known to be drainable to zero, mirroring langchain_census's own birth
path (census -> classify -> lock).

Run over the whole corpus:
    python scripts/qa/fence_import_check.py --root .
"""
from __future__ import annotations

import argparse
import ast
import importlib
import re
import sys
import textwrap
from pathlib import Path

FENCE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")
PYTHON_LANGS = ("python", "py", "python3")

for _pkg in ("torch", "pydantic"):
    try:
        importlib.import_module(_pkg)
    except ImportError:  # environment problem, not a doc problem
        print(f"fence_import_check: {_pkg} not importable in this "
              "interpreter - the census resolves lesson imports against "
              "the kurulu-stack; run the scorecard with that python "
              "(see ENVIRONMENT-SETUP.md)")
        sys.exit(2)

_verdict_cache: dict[str, str] = {}


def resolve_module(mod: str) -> str:
    """'OK' or 'ErrorType: message' for a dotted module path."""
    if mod in _verdict_cache:
        return _verdict_cache[mod]
    try:
        importlib.import_module(mod)
        verdict = "OK"
    except Exception as e:  # noqa: BLE001 - any failure means "cannot run"
        verdict = type(e).__name__ + ": " + str(e).split("\n")[0][:90]
    _verdict_cache[mod] = verdict
    return verdict


def scan_file(root: Path, path: Path, findings: list[str], stats: list[int]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")
    in_fence = False
    lang = ""
    start = 0
    body: list[str] = []
    for i, raw in enumerate(lines):
        m = FENCE.match(raw)
        if m:
            if in_fence:
                if lang in PYTHON_LANGS:
                    stats[1] += 1
                    src = textwrap.dedent("\n".join(body))
                    if src.strip():
                        try:
                            tree = ast.parse(src)
                        except SyntaxError:
                            continue  # CB-01 owns fence syntax
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    stats[0] += 1
                                    verdict = resolve_module(alias.name)
                                    if verdict != "OK":
                                        findings.append(
                                            f"{rel}:{start + node.lineno + 1}: "
                                            f"IC-01 import does not resolve "
                                            f"[{verdict}] - import {alias.name}")
                            elif isinstance(node, ast.ImportFrom):
                                if node.level > 0 or node.module is None:
                                    stats[3] += 1  # relative: no context
                                    continue
                                stats[0] += 1
                                verdict = resolve_module(node.module)
                                if verdict != "OK":
                                    findings.append(
                                        f"{rel}:{start + node.lineno + 1}: "
                                        f"IC-01 import does not resolve "
                                        f"[{verdict}] - from {node.module} "
                                        f"import ...")
                                else:
                                    module = importlib.import_module(node.module)
                                    for alias in node.names:
                                        if alias.name == "*":
                                            continue
                                        if not hasattr(module, alias.name):
                                            findings.append(
                                                f"{rel}:{start + node.lineno + 1}: "
                                                f"IC-01 name absent from module "
                                                f"[AttributeError: {node.module} "
                                                f"has no attribute "
                                                f"'{alias.name}'] - from "
                                                f"{node.module} import "
                                                f"{alias.name}")
                in_fence = False
                body = []
            else:
                in_fence = True
                lang = m.group(2).lower()
                start = i
                body = []
            continue
        if in_fence:
            body.append(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    stats = [0, 0, 0, 0]  # import statements, python fences, unused, relative imports
    files_seen: set[str] = set()
    for path in sorted(docs.rglob("*.md")):
        before = len(findings)
        try:
            scan_file(args.root, path, findings, stats)
        except (UnicodeDecodeError, OSError):
            continue
        if len(findings) > before:
            files_seen.add(path.relative_to(args.root).as_posix())
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"fence_import_check: {len(findings)} unresolvable imports "
          f"(IC-01) in {len(files_seen)} files across docs/ "
          f"({stats[0]} import statements in {stats[1]} python fences, "
          f"{stats[3]} relative imports skipped) - report mode at birth "
          f"(tick-323 census)")
    return 0  # report mode at birth; hard gate only after classification


if __name__ == "__main__":
    sys.exit(main())
