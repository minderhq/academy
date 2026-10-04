#!/usr/bin/env python3
"""SQL interpolation gate for the Minder Academy corpus.

SQ-01  a ```python fence must not pass an f-string carrying SQL text to an
       execution call (``execute``/``executemany``/``executescript``/
       ``read_sql``/``read_sql_query``) - the interpolated value is merged
       into the query text client-side, before the driver ever sees it, so
       no placeholder can bind it: a name containing a quote closes the
       literal and the rest of the string executes as SQL. Direct
       (``cursor.execute(f"SELECT ... {name}")``) and via a query variable
       (``q = f"..."; cursor.execute(q)`` - nearest preceding assignment,
       per-function scope) both fire.

SQ-02  the same client-side merge through the non-f forms: percent-format
       (``"SELECT ... %s" % (uid,)`` - despite the placeholder in the text,
       the % merges the value BEFORE execution; true binding passes the
       tuple as a second argument), ``str.format()``, and concatenation
       whose fragments carry no ``%s``/``?`` placeholder
       (``"SELECT ... name = '" + name + "'"``). The placeholder-carrying
       builder (``q = "SELECT..."; q += " AND x <= %s"; params.append(v);
       cursor.execute(q, params)``) is the corpus's own taught idiom
       (7402-Agent-Memory-Implementation builds filters exactly this way)
       and stays out.

Out of the class by construction:

  - constant query strings: the corpus's SQL discipline is 36/36
    execution calls carrying Constant query text (born census tick-653,
    zero interpolated) - DDL, CRUD literals, and the
    ``cursor.execute(sql, params or ())`` repository form (LAB-013);
    a Constant never enters the walk.
  - placeholder binding: a Constant query with ``%s``/``?`` placeholders
    plus a second-argument params tuple - the canonical safe form.
  - the placeholder-carrying concatenation builder (7402's
    ``query += " AND ... %s"`` + ``params.append``): placeholders
    anywhere in the builder chain mean values travel the binding
    channel, so the chain stays silent.
  - non-SQL ``execute`` calls: agent-tool/sandbox/registry
    ``execute(...)`` calls (LAB-004, 7202, 7301) interpolate or carry
    code/tool-name strings with no SQL keyword; the walk only enters
    when the string's literal parts carry SQL vocabulary (select,
    insert, update, delete, create, drop, alter, from, where, into,
    values, order by, group by - casefold).
  - string mentions and prose never reach the walk: the check walks
    ast.JoinedStr/ast.BinOp/ast.Call nodes, not text.
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, on any line) is deliberate
    danger-teaching, the sibling unsafe_*/interp gates' escape.
  - notebooks (.ipynb) are outside the md universe, the whole
    unsafe_*/fence family scans docs/**/*.md only.

Hard gate (exit 1 on findings): born census tick-653 read every
execution-call query argument in every md python fence fence-aware with
one-hop query-variable resolution = 0 interpolated findings across 36
Constant-argument calls (9 placeholder-carrying, 27 static DDL/CRUD,
plus the params-tuple repository forms) - the corpus practices
parameterized SQL everywhere and never once merges a value client-side,
so the class froze at the rule the moment it was named: zero-drain,
hard from birth (the EC-03/fence_lang shape).

Run over the whole corpus:
    python scripts/qa/sql_interp_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")

# A fence whose lines carry any of these is deliberate danger-teaching:
# the vulnerable form shown to be avoided, not craft to copy.
DANGER_MARKER_RE = re.compile(r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)

# The corpus's execution entry points. ``run``/``execute_query`` belong to
# cypher_interp_scan - disjoint by attr, single ownership by construction.
EXEC_ATTRS = {"execute", "executemany", "executescript",
              "read_sql", "read_sql_query"}

# SQL vocabulary that must appear in the string's literal parts for the
# call to be in-class - keeps the non-SQL execute family (sandbox code
# strings, tool names, prompts) out by construction.
SQL_KEYWORD_RE = re.compile(
    r"\b(select|insert|update|delete|create|drop|alter|from|where|into"
    r"|values|order\s+by|group\s+by)\b", re.IGNORECASE)

# Value-binding placeholders: their presence anywhere in a concatenation
# builder means values travel the params channel (the 7402 idiom).
PLACEHOLDER_RE = re.compile(r"%s|\?")


def _has_sql(text: str) -> bool:
    return bool(SQL_KEYWORD_RE.search(text))


def _constant_leaves(node: ast.expr) -> list[str]:
    """Every string-Constant leaf of an expression tree (Add chains
    included)."""
    out: list[str] = []
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.append(n.value)
    return out


def _is_add_chain(node: ast.expr) -> bool:
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)


def _joinedstr_leaves(node: ast.expr) -> list[ast.JoinedStr]:
    return [n for n in ast.walk(node) if isinstance(n, ast.JoinedStr)]


def _is_percent_format(node: ast.expr) -> bool:
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod)


def _is_format_call(node: ast.expr) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "format")


def _classify(expr: ast.expr) -> str | None:
    """SQ code for a resolved query expression, or None when out of
    class. SQ-01 wins: an f-string in the chain is the loudest form."""
    for js in _joinedstr_leaves(expr):
        if any(_has_sql(p) for p in _constant_leaves(js)):
            return "SQ-01"
    if _is_percent_format(expr) or _is_format_call(expr):
        if any(_has_sql(p) for p in _constant_leaves(expr)):
            return "SQ-02"
    if _is_add_chain(expr):
        leaves = _constant_leaves(expr)
        has_placeholder = any(PLACEHOLDER_RE.search(p) for p in leaves)
        has_dynamic = any(not isinstance(n, ast.Constant)
                          for n in ast.walk(expr)
                          if isinstance(n, (ast.Name, ast.Call, ast.JoinedStr,
                                            ast.FormattedValue)))
        if not has_placeholder and has_dynamic \
                and any(_has_sql(p) for p in leaves):
            return "SQ-02"
    return None


def _collect_assigns(body: list[ast.stmt],
                     out: list[tuple[int, str, ast.expr]]) -> None:
    """``name = <expr>`` and ``name += <expr>`` assignments from a
    statement list, recursing into compound statements but NOT into
    functions/classes (those own their scopes)."""
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            out.append((node.lineno, node.targets[0].id, node.value))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.value is not None:
            out.append((node.lineno, node.target.id, node.value))
        elif isinstance(node, ast.AugAssign) \
                and isinstance(node.target, ast.Name):
            out.append((node.lineno, node.target.id, node.value))
        for child in ast.iter_child_nodes(node):
            _collect_assigns([child], out)


def _func_assigns(func: ast.AST) -> list[tuple[int, str, ast.expr]]:
    out: list[tuple[int, str, ast.expr]] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            out.append((node.lineno, node.targets[0].id, node.value))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.value is not None:
            out.append((node.lineno, node.target.id, node.value))
        elif isinstance(node, ast.AugAssign) \
                and isinstance(node.target, ast.Name):
            out.append((node.lineno, node.target.id, node.value))
    return sorted(out, key=lambda t: t[0])


def _builder_chain(name: str, line: int,
                   assigns: list[tuple[int, str, ast.expr]]) -> ast.expr | None:
    """Resolve a query variable backwards through its same-name assignment
    history (nearest PRECEDING first, then earlier fragments while the
    value is an Add chain) - the 7402 builder builds SQL across several
    ``query +=`` fragments and the last fragment alone is not the text."""
    history = sorted(((ln, v) for ln, an, v in assigns
                      if an == name and ln < line), key=lambda t: t[0])
    if not history:
        return None
    parts: list[ast.expr] = [history[-1][1]]
    for _, v in reversed(history[:-1]):
        if _is_add_chain(v) or isinstance(v, ast.Constant):
            parts.append(v)
        else:
            break
    node = parts[0]
    for p in parts[1:]:
        node = ast.BinOp(left=node, op=ast.Add(), right=p)
    return node


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

    module_assigns: list[tuple[int, str, ast.expr]] = []
    _collect_assigns(tree.body, module_assigns)

    calls: list[tuple[ast.Call, ast.AST | None]] = []

    class _Collector(ast.NodeVisitor):
        def __init__(self) -> None:
            self.func_stack: list[ast.AST] = []

        def visit_FunctionDef(self, node) -> None:  # type: ignore[override]
            self.func_stack.append(node)
            self.generic_visit(node)
            self.func_stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Attribute) \
                    and node.func.attr in EXEC_ATTRS and node.args:
                calls.append((node,
                              self.func_stack[-1] if self.func_stack else None))
            self.generic_visit(node)

    _Collector().visit(tree)

    for call, func in calls:
        arg0 = call.args[0]
        code: str | None = None
        if not isinstance(arg0, ast.Constant):
            if _classify(arg0) is not None:
                code = _classify(arg0)
            elif isinstance(arg0, ast.Name):
                scope_assigns = (_func_assigns(func) if func is not None
                                 else module_assigns)
                value = _builder_chain(arg0.id, call.lineno, scope_assigns)
                if value is None and func is not None:
                    value = _builder_chain(arg0.id, call.lineno, module_assigns)
                if value is not None:
                    code = _classify(value)
        if code is None:
            continue  # Constant query / placeholder idiom / non-SQL content
        verb = call.func.attr
        findings.append(
            f"{rel}:{base + call.lineno}: {code} SQL interpolated into "
            f"{verb}() - the value is merged into the query text "
            f"client-side, before the driver sees it, so no placeholder "
            f"can bind it (a value containing a quote closes the literal "
            f"and the rest executes as SQL); bind values instead: a "
            f"Constant query with %s/? placeholders plus a params second "
            f"argument, or the corpus-taught builder (query += \" AND x "
            f"<= %s\"; params.append(v); execute(query, params), the "
            f"7402-Agent-Memory idiom)")
        # one finding per execution call


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    in_fence = False
    f_char = ""
    f_len = 0
    lang = ""
    start = 0
    fence_lines: list[tuple[int, str]] = []
    for ln, raw in enumerate(lines, 1):
        if FENCE_RE.match(raw):
            ch = FENCE_RE.match(raw).group(1)[0]
            n = len(FENCE_RE.match(raw).group(1))
            if in_fence:
                # CommonMark fence length (tick-680): only a same-character run at least as long closes
                if ch == f_char and n >= f_len:
                    if in_fence and lang == "python" and fence_lines:
                        _scan_fence(rel, start, fence_lines, findings)
                    in_fence = False
                    lang = ""
                    start = 0
                    fence_lines = []
                    continue
            else:
                in_fence = True
                f_char, f_len = ch, n
                lang = FENCE_RE.match(raw).group(2).lower()
                start = ln
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
    print(f"sql_interp_scan: {len(findings)} findings "
          f"(SQ-01 f-string SQL interpolation, SQ-02 client-side "
          f"percent/format/non-placeholder-concat merging) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
