#!/usr/bin/env python3
"""notebook_execution_scan: execution-order NAME RESOLUTION across a
notebook's code cells (NBE-01..02, hard).

The platform launcher runs each notebook top-to-bottom in a fresh
kernel, so a Name load that resolves against neither the builtins nor
the definitions accumulated from cells 1..N is a runtime NameError
for the learner mid-lesson - NBC-01 proves the cells PARSE, nothing
proved they RESOLVE. tick-693's naive census of this class was
polluted (it collected only module-level Import/Assign/def targets
and checked every Load against them: self, function parameters,
for/with/comprehension targets and function bodies all surfaced as
false UNDEF rows), and the class was deferred rather than gated
fuzzy. tick-694 replaced the walker with a scope-aware module-flow
pass and the census came back clean at 0 over the real corpus - the
pollution was the walker, not the corpus, so the gate is born at
zero the census->classify->lock way.

The walker's contract (recorded here because it IS the judgment):
- statements processed IN ORDER per cell, cells in order, definitions
  accumulated across cells - the launcher's exact execution model
- definitions collected: Import/ImportFrom, Assign, AnnAssign,
  AugAssign (its target is also checked as a read - x += 1 reads x),
  def/class names, For/AsyncFor targets, With/AsyncWith
  optional_vars; if/try collect BOTH branches (pragmatic static
  pass - a definition visible on either path is accepted)
- scope boundaries NOT descended: function and class bodies (their
  loads are invisible to this pass), lambda bodies; decorators,
  defaults and return annotations ARE checked (they run at module
  level)
- comprehensions are a mini-scope: generator targets collected
  first, then iters/ifs/element checked against known | targets
- Delete context ignored (del x leaves x accepted afterwards)
- ACCEPTED = dir(builtins) + the IPython-provided surface (display,
  get_ipython, run_line_magic, run_cell_magic, In/Out, the
  underscore caches, get_config/set_config) - tightened from the
  first probe set and re-measured at 0

The two rules:
- NBE-01 a Name load that resolves against neither the accepted
  surface nor the accumulated definitions (the learner's NameError)
- NBE-02 an AugAssign target that does not pre-exist (x += 1 reads
  before it writes)

Jurisdiction split: structural health stays NBH-03's (unparseable
JSON, malformed sources - silently skipped here, the designed
cross-gate agreement NBC/NBL/NBT document); a cell that fails
ast.parse stays NBC-01's (counted as syntax_skipped, not resolved).
Born tick-694 at ZERO findings rc=0 (20 notebooks / 102 code cells).
"""
import argparse
import ast
import builtins
import json
import sys
from pathlib import Path

IPYTHON_BUILTINS = {
    "display", "get_ipython", "run_line_magic", "run_cell_magic",
    "In", "Out", "_", "__", "___", "get_config", "set_config",
}
ACCEPTED = frozenset(dir(builtins)) | IPYTHON_BUILTINS


def cell_source(cell):
    """Join a notebook cell's source (list-of-str or str) to one str."""
    src = cell.get("source")
    if isinstance(src, list):
        return "".join(s for s in src if isinstance(s, str))
    return src if isinstance(src, str) else ""


def names_in_target(target):
    """Every Name id inside an assignment target."""
    out = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Name):
            out.add(node.id)
    return out


def check_expr(node, known, findings, where):
    """Recursively check loads in an expression; never enter a new
    function/class/lambda body scope."""
    if node is None:
        return
    if isinstance(node, ast.Lambda):
        for d in node.args.defaults:
            check_expr(d, known, findings, where)
        for d in node.args.kw_defaults:
            check_expr(d, known, findings, where)
        return  # lambda body: own scope, not descended
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp,
                         ast.DictComp)):
        local = set()
        for gen in node.generators:
            check_expr(gen.iter, known, findings, where)
            local |= names_in_target(gen.target)
            for cond in gen.ifs:
                check_expr(cond, known | local, findings, where)
        scope = known | local
        if isinstance(node, ast.DictComp):
            check_expr(node.key, scope, findings, where)
            check_expr(node.value, scope, findings, where)
        else:
            check_expr(node.elt, scope, findings, where)
        return
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.expr):
            check_expr(child, known, findings, where)
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) \
            and node.id not in known:
        findings.append(
            "%s: NBE-01 name '%s' never resolves against the "
            "definitions accumulated from the cells before it - the "
            "launcher runs this notebook top-to-bottom in a fresh "
            "kernel and the learner hits a NameError here" % (where,
                                                              node.id))


def walk_stmts(stmts, known, findings, where):
    """Process a statement list in order (module-level flow)."""
    for st in stmts:
        flow_stmt(st, known, findings, where)


def flow_stmt(st, known, findings, where):
    if isinstance(st, (ast.Import, ast.ImportFrom)):
        for a in st.names:
            known.add(a.asname or a.name.split(".")[0])
        return
    if isinstance(st, ast.Assign):
        check_expr(st.value, known, findings, where)
        for t in st.targets:
            known |= names_in_target(t)
        return
    if isinstance(st, ast.AnnAssign):
        check_expr(st.annotation, known, findings, where)
        check_expr(st.value, known, findings, where)
        if isinstance(st.target, ast.Name):
            known.add(st.target.id)
        return
    if isinstance(st, ast.AugAssign):
        for n in sorted(names_in_target(st.target)):
            if n not in known:
                findings.append(
                    "%s: NBE-02 augmented assignment reads '%s' "
                    "before any cell defines it (x += 1 reads x) - "
                    "the fresh kernel has no '%s' yet" % (where, n, n))
        check_expr(st.value, known, findings, where)
        known |= names_in_target(st.target)
        return
    if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for d in st.decorator_list:
            check_expr(d, known, findings, where)
        check_expr(st.returns, known, findings, where)
        for d in st.args.defaults + [d for d in st.args.kw_defaults
                                     if d]:
            check_expr(d, known, findings, where)
        known.add(st.name)
        return
    if isinstance(st, ast.ClassDef):
        for d in st.decorator_list:
            check_expr(d, known, findings, where)
        for b in st.bases:
            check_expr(b, known, findings, where)
        for kw in st.keywords:
            check_expr(kw.value, known, findings, where)
        known.add(st.name)
        return
    if isinstance(st, (ast.For, ast.AsyncFor)):
        check_expr(st.iter, known, findings, where)
        known |= names_in_target(st.target)
        walk_stmts(st.body, known, findings, where)
        walk_stmts(st.orelse, known, findings, where)
        return
    if isinstance(st, ast.While):
        check_expr(st.test, known, findings, where)
        walk_stmts(st.body, known, findings, where)
        walk_stmts(st.orelse, known, findings, where)
        return
    if isinstance(st, (ast.With, ast.AsyncWith)):
        for item in st.items:
            check_expr(item.context_expr, known, findings, where)
            if item.optional_vars is not None:
                known |= names_in_target(item.optional_vars)
        walk_stmts(st.body, known, findings, where)
        return
    if isinstance(st, ast.If):
        check_expr(st.test, known, findings, where)
        walk_stmts(st.body, known, findings, where)
        walk_stmts(st.orelse, known, findings, where)
        return
    if isinstance(st, ast.Try):
        walk_stmts(st.body, known, findings, where)
        for h in st.handlers:
            walk_stmts(h.body, known, findings, where)
        walk_stmts(st.orelse, known, findings, where)
        walk_stmts(st.finalbody, known, findings, where)
        return
    if isinstance(st, ast.Return):
        check_expr(st.value, known, findings, where)
        return
    if isinstance(st, ast.Expr):
        check_expr(st.value, known, findings, where)
        return
    if isinstance(st, ast.Delete):
        return  # del x: known untouched (pragmatic)
    if isinstance(st, (ast.Break, ast.Continue, ast.Pass,
                       ast.Global, ast.Nonlocal)):
        return
    for child in ast.iter_child_nodes(st):
        if isinstance(child, ast.expr):
            check_expr(child, known, findings, where)
        elif isinstance(child, ast.stmt):
            flow_stmt(child, known, findings, where)
    return


def scan_nb(root, path, findings, stats):
    """Walk one notebook's code cells in launcher execution order."""
    try:
        nb = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        stats[3] += 1
        return
    if not isinstance(nb, dict) or not isinstance(nb.get("cells"), list):
        stats[3] += 1
        return
    known = set(ACCEPTED)
    for idx, cell in enumerate(nb["cells"]):
        if not isinstance(cell, dict) or \
                cell.get("cell_type") != "code":
            continue
        src = cell_source(cell)
        if not isinstance(cell.get("source"), (list, str)):
            stats[3] += 1
            continue
        stats[1] += 1
        try:
            tree = ast.parse(src)
        except SyntaxError:
            stats[2] += 1  # NBC-01 jurisdiction
            continue
        where = "%s code cell %d" % (
            path.relative_to(root).as_posix(), idx)
        walk_stmts(tree.body, known, findings, where)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="notebook execution-order name resolution")
    ap.add_argument("--root", type=Path,
                    default=Path(__file__).resolve().parents[2])
    args = ap.parse_args(argv)
    root = args.root
    findings = []
    stats = [0, 0, 0, 0]  # notebooks, code cells, NBC-01, NBH-03
    for path in sorted((root / "docs" / "notebooks").glob("*.ipynb")):
        stats[0] += 1
        scan_nb(root, path, findings, stats)
    for line in findings:
        sys.stdout.buffer.write(
            (line + "\n").encode("utf-8", "backslashreplace"))
    sys.stdout.buffer.write(
        ("notebook_execution_scan: %d findings (NBE-01 a Name load "
         "that never resolves against the accumulated cell "
         "definitions / NBE-02 an AugAssign target read before "
         "definition; %d code cells walked, %d cell(s) left to "
         "NBC-01, %d cell(s) left to NBH-03) - hard; born tick-694 "
         "at zero over the real corpus (tick-693's naive census "
         "pollution was the walker, not the corpus)\n"
         % (len(findings), stats[1], stats[2], stats[3]))
        .encode("utf-8", "backslashreplace"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
