#!/usr/bin/env python3
"""Mutable-default-argument gate for the Minder Academy corpus.

MD-01  a ```python fence must not sign a function with a *mutable
       literal default* - ``def f(x=[])``, ``def f(x={})``,
       ``def f(x={1, 2})`` (ast.List/ast.Dict/ast.Set as a default).
       The default object is created once at ``def`` time and shared
       across every call, so any mutation (append, update, add)
       writes into every other call's view - the canonical Python
       shared-state bug.

MD-02  the same class one step removed: a *zero-argument mutable
       constructor call* as a default - ``def f(x=list())``,
       ``dict()``, ``set()``. Syntactically a call, semantically the
       identical shared object.

The corpus itself vouches the class by refusing it: the stdlib it
teaches with rejects the exact form - ``dataclasses`` raises
``ValueError: mutable default <class 'list'> for field ... is not
allowed`` (use ``default_factory``) - and the corpus teaches the safe
idiom ``field(default_factory=list/dict/...)`` in 15+ places (LAB-013
x3, LAB-014 x4, 2301, 2303, 2306 x2, 6502 x2, 7103, 7302). The
``default_factory`` escape hatch exists precisely because the shared
mutable default is an error; yet the same corpus signed 7 plain
functions with literal mutable defaults (born census below).

Out of the class by construction:

  - immutable literal defaults (int/str/bool/float/None/tuple/bytes):
    a tuple literal is immutable, ``def f(x=(1, 2))`` never enters.
  - the None-sentinel affirmative idiom (``x=None`` + ``if x is None:
    x = []`` in the body): the ``None`` default is not mutable, the
    walk never sees it - the corpus-taught escape for plain functions,
    the sibling of dataclass ``default_factory``.
  - ``field(default_factory=list)``: an Attribute call on a dataclass
    field, not a function default; a fresh object per instance.
  - call defaults with arguments (``datetime.now()``,
    ``threading.Event()``): MD-02 demands a zero-arg ``Name``
    constructor of exactly list/dict/set - other calls are not
    adjudicated as mutable.
  - ``lambda: []`` as a default: ast.Lambda, not a literal - and each
    call invokes the lambda, a fresh list per call; corpus boundary
    census read 0 comp/lambda defaults.
  - ListComp/DictComp/SetComp defaults: a different node family, out
    of the single-owned class; corpus boundary census read 0.
  - string mentions and prose never reach the walk: the check walks
    ast.FunctionDef/ast.AsyncFunctionDef ``args.defaults`` /
    ``kw_defaults``, not text.
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, on any line) is deliberate
    danger-teaching, the sibling unsafe_* gates' escape.
  - notebooks (.ipynb) are outside the md universe, the whole
    unsafe_*/fence family scans docs/**/*.md only.

Hard gate (exit 1 on findings): the born census read every function
signature in every md python fence fence-aware = exactly 7 findings
across 7 files, all MD-01 (6 List + 1 Dict; MD-02 silent born):
SOLUTION-LAB-006's ``SimpleNN.__init__(hidden_sizes=[256, 128])``,
4302's ``insert_fake_quant(target_layers=['Linear', 'Conv2d'])``,
4304's ``progressive_qat(epochs_per_bit=[5, 5, 10])``, 4306's
``skip_layer_quantization(layer_types=['LayerNorm', 'Softmax'])``,
5100-peft PRACTICE's ``apply_lora_to_model(target_modules=["c_attn"])``,
6300-context PRACTICE's ``benchmark_context_length(lengths=[512, ...])``,
VOLUME-6's ``fuse_graphrag_context(weights={"graph": 0.3, ...})`` - all
at true file lines (fence content line 1 = fence-open line + 1, the
tick-645 lesson pre-applied). Drained the same tick to the
None-sentinel idiom the stdlib itself teaches for plain functions.

Run over the whole corpus:
    python scripts/qa/mutable_default_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

# A fence whose lines carry any of these is deliberate danger-teaching:
# the vulnerable form shown to be avoided, not craft to copy.
DANGER_MARKER_RE = re.compile(r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)

MUT_LITERALS = (ast.List, ast.Dict, ast.Set)
MUT_CTORS = {"list", "dict", "set"}


def _classify(default: ast.expr) -> str | None:
    """MD-01 for a mutable literal default, MD-02 for a zero-arg
    list()/dict()/set() default, None for everything else."""
    if isinstance(default, MUT_LITERALS):
        return "MD-01"
    if isinstance(default, ast.Call) and isinstance(default.func, ast.Name) \
            and default.func.id in MUT_CTORS \
            and not default.args and not default.keywords:
        return "MD-02"
    return None


def _scan_fence(rel: str, start: int, fence_lines: list[tuple[int, str]],
                findings: list[str]) -> None:
    src = "\n".join(raw for _, raw in fence_lines)
    if DANGER_MARKER_RE.search(src):
        return
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    base = start  # fence content line 1 == fence-open line + 1 (tick-645 lesson)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        defaults = list(node.args.defaults) \
            + [d for d in node.args.kw_defaults if d is not None]
        for d in defaults:
            code = _classify(d)
            if code is None:
                continue
            kind = ("mutable literal default ([]/ {} / set literal)"
                    if code == "MD-01"
                    else "zero-arg list()/dict()/set() default")
            findings.append(
                f"{rel}:{base + d.lineno}: {code} {kind} on "
                f"`{node.name}` - the default object is created once at "
                f"def time and shared across every call, so any mutation "
                f"writes into every other call's view (dataclasses "
                f"rejects the same form: 'mutable default ... is not "
                f"allowed'); use the None-sentinel idiom (x=None + "
                f"`if x is None: x = ...` in the body), the corpus-taught "
                f"escape for plain functions (dataclass world already "
                f"teaches field(default_factory=...))")


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    in_fence = False
    lang = ""
    start = 0
    fence_lines: list[tuple[int, str]] = []
    for ln, raw in enumerate(lines, 1):
        if FENCE_RE.match(raw):
            if in_fence and lang == "python" and fence_lines:
                _scan_fence(rel, start, fence_lines, findings)
            in_fence = not in_fence
            lang = "" if not in_fence else FENCE_RE.match(raw).group(2).lower()
            start = ln if in_fence else 0
            fence_lines = []
            continue
        if in_fence:
            fence_lines.append((ln, raw))
    if in_fence and lang == "python" and fence_lines:
        _scan_fence(rel, start, fence_lines, findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    n_files: set[str] = set()
    for path in sorted(docs.rglob("*.md")):
        try:
            before = len(findings)
            scan_file(args.root, path, findings)
            if len(findings) > before:
                n_files.add(path.relative_to(args.root).as_posix())
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"mutable_default_scan: {len(findings)} findings "
          f"(MD-01 mutable literal default, MD-02 zero-arg "
          f"list()/dict()/set() default) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
