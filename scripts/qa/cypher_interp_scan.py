#!/usr/bin/env python3
"""Cypher label/rel-type/path-bound interpolation gate for the Minder Academy corpus.

CI-01  a ```python fence must not interpolate a value into a Cypher
       *label or relationship-type position* - the literal part of the
       f-string immediately before the interpolated value ends with a
       colon (``(n:{label}``, ``[r:{rel_type}]``). Those positions are
       structurally un-parameterizable: Cypher's ``$parameters`` bind
       values, never schema names, so an interpolated label/rel-type is
       the one Cypher injection the driver cannot neutralize. The
       corpus itself vouches the class: 6301-Neo4j teaches "Values are
       bound with $parameters, never interpolated into the string - an
       entity name containing quotes or Cypher metacharacters cannot
       inject the query" and "execute parameterized Cypher through the
       Python driver session ... bind values with ``$parameters``".

CI-02  a ```python fence must not interpolate an *uncast* value into a
       Cypher *variable-length path bound* - the literal before the
       interpolated value ends with ``..`` or ``*``
       (``-[*1..{max_depth}]-``). This position is also
       un-parameterizable - "Parameters cannot set variable-length path
       bounds in Cypher" (6304-GraphRAG) - so the corpus teaches the
       mitigation: int-cast then interpolate (``hop_bound =
       max(1, int(depth))``, 6304 at 178/325/456). An interpolated raw
       parameter there is unbounded-walk injection on top of the type
       hole.

Out of the class by construction:

  - the parameterized affirmative form: a query built as a plain
    (non-f) string carrying ``$parameters`` and bound at
    ``session.run(query, ...)`` (6301's teaching, 6304's
    find_shortest_path) never enters the walk - the target is a
    Constant, not a JoinedStr.
  - colon-plus-space literals: agent-prompt ``.run()`` calls whose
    f-string literal ends with ``": "`` (VOLUME-7's
    "Design architecture for: {feature}") are prompt text, not a
    Cypher label position - only a literal ending at exactly ``:``
    fires.
  - the LIMIT position: ``LIMIT {limit}`` follows a literal ending in
    whitespace; LIMIT is a parameterizable value position (Cypher
    accepts ``LIMIT $n``), out of the label/path-bound class.
  - int-cast-defended path bounds: the interpolated expression is
    itself ``int(...)``/``max(..., int(...))`` shaped, or resolves one
    hop to an assignment of that shape - the 6304-taught escape
    (all three of its ``hop_bound = max(1, int(...))`` sites stay
    silent).
  - allowlist-defended labels/rel-types: the enclosing function
    carries a membership test on the interpolated name
    (``if label not in ALLOWED_LABELS: raise ValueError(...)``) - the
    schema-name idiom for a position no ``$parameter`` can fill.
  - string mentions and prose never reach the walk: the check walks
    ast.JoinedStr/ast.Call nodes, not text.
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, on any line) is deliberate
    danger-teaching, the sibling unsafe_* gates' escape.
  - notebooks (.ipynb) are outside the md universe, the whole
    unsafe_*/fence family scans docs/**/*.md only.

Hard gate (exit 1 on findings): the born census read the python-fence
``session.run``/``execute_query`` calls fence-aware with one-hop
query-variable resolution (nearest preceding assignment in the same
function scope) = 5 findings across 2 files (CI-01 x2: phase6-practice's
create_entity ``{label}`` direct and create_relationship ``{rel_type}``
via a query variable; CI-02 x3: phase6-practice find_connections' uncast
``{max_depth}`` plus LAB-005-GraphRAG's two ``-[*1..{max_hops}]`` /
``-[*1..{max_depth}]`` multi-hop explorers that the direct-form surface
grep missed - the indirect query-variable delivery is why the gate
resolves one hop). Drained the same tick to the corpus's own two
idioms: allowlist guards for the schema-name positions, the 6304
int-cast for the path bounds.

Run over the whole corpus:
    python scripts/qa/cypher_interp_scan.py --root .
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

# The corpus's go-to Neo4j execution entry points (6301/6304/SOL-LAB-005).
RUN_ATTRS = {"run", "execute_query"}


def _collect_assigns(body: list[ast.stmt], out: list[tuple[int, str, ast.expr]]) -> None:
    """Collect ``name = <expr>`` assignments from a statement list,
    recursing into compound statements but NOT into functions/classes
    (those own their scopes)."""
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            out.append((node.lineno, node.targets[0].id, node.value))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.value is not None:
            out.append((node.lineno, node.target.id, node.value))
        for child in ast.iter_child_nodes(node):
            _collect_assigns([child], out)


class _CallCollector(ast.NodeVisitor):
    """Collect Cypher-execution calls together with their enclosing
    function (for per-function-scope one-hop resolution)."""

    def __init__(self) -> None:
        self.calls: list[tuple[ast.Call, ast.FunctionDef | None]] = []
        self.func_stack: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    def visit_FunctionDef(self, node) -> None:  # type: ignore[override]
        self.func_stack.append(node)
        self.generic_visit(node)
        self.func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr in RUN_ATTRS \
                and node.args:
            func = self.func_stack[-1] if self.func_stack else None
            self.calls.append((node, func))
        self.generic_visit(node)


def _func_assigns(func: ast.FunctionDef | ast.AsyncFunctionDef
                  ) -> list[tuple[int, str, ast.expr]]:
    out = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            out.append((node.lineno, node.targets[0].id, node.value))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.value is not None:
            out.append((node.lineno, node.target.id, node.value))
    return sorted(out, key=lambda t: t[0])


def _nearest_assign(name: str, line: int,
                    scope_assigns: list[tuple[int, str, ast.expr]]) -> ast.expr | None:
    """Nearest PRECEDING assignment of ``name`` in the scope (per-function
    scope is the tick-649 design lesson - a flat per-fence dict let a
    second ``query =`` assignment overwrite the first and hide a site)."""
    best: ast.expr | None = None
    best_line = -1
    for lineno, aname, value in scope_assigns:
        if aname == name and best_line < lineno < line:
            best, best_line = value, lineno
    return best


def _is_cast_shaped(node: ast.expr) -> bool:
    """The 6304 mitigation shape: ``int(x)`` or ``max(1, int(depth))``
    - a value that cannot smuggle Cypher metacharacters or unbounded
    hops."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "int":
            return True
        if node.func.id in ("max", "min"):
            return any(_is_cast_shaped(a) for a in node.args)
    return False


def _has_membership_guard(scope: ast.AST | None, name: str) -> bool:
    """True if the enclosing scope tests ``name`` against a container
    (``if label not in ALLOWED_LABELS:``) - the allowlist idiom for a
    position no $parameter can fill."""
    if scope is None:
        return False
    for node in ast.walk(scope):
        if isinstance(node, ast.Compare) and any(
                isinstance(op, (ast.In, ast.NotIn)) for op in node.ops):
            for operand in [node.left, *node.comparators]:
                if isinstance(operand, ast.Name) and operand.id == name:
                    return True
    return False


def _position_interpolants(js: ast.JoinedStr, want: str) -> list[ast.expr]:
    """FormattedValues immediately following a literal part ending with
    the class marker: ``:`` for label/rel-type positions, ``..``/``*``
    for variable-length path bounds."""
    out: list[ast.expr] = []
    armed = False
    for v in js.values:
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            if want == ":":
                armed = v.value.endswith(":")
            else:
                armed = v.value.endswith("..") or v.value.endswith("*")
        elif isinstance(v, ast.FormattedValue) and armed:
            out.append(v.value)
            armed = False
    return out


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
    func_assigns: dict[int, list[tuple[int, str, ast.expr]]] = {}
    collector = _CallCollector()
    collector.visit(tree)

    for call, func in collector.calls:
        target = call.args[0]
        js: ast.JoinedStr | None = None
        if isinstance(target, ast.JoinedStr):
            js = target
        elif isinstance(target, ast.Name):
            scope_assigns = (_func_assigns(func) if func is not None
                             else module_assigns)
            value = _nearest_assign(target.id, call.lineno, scope_assigns)
            if value is None and func is not None:
                value = _nearest_assign(target.id, call.lineno, module_assigns)
            if isinstance(value, ast.JoinedStr):
                js = value
        if js is None:
            continue  # Constant = the parameterized affirmative form

        str_parts = [v.value for v in js.values
                     if isinstance(v, ast.Constant) and isinstance(v.value, str)]
        if any(p.endswith(":") for p in str_parts):
            want, code = ":", "CI-01"
        elif any(p.endswith("..") or p.endswith("*") for p in str_parts):
            want, code = "..", "CI-02"
        else:
            continue

        scope: ast.AST | None = func
        scope_assigns = (_func_assigns(func) if func is not None else module_assigns)
        for interp in _position_interpolants(js, want):
            if code == "CI-01":
                if _is_cast_shaped(interp):
                    continue
                if isinstance(interp, ast.Name) \
                        and _has_membership_guard(scope, interp.id):
                    continue
                kind = ("label/rel-type position interpolation without an "
                        "allowlist guard")
            else:
                if _is_cast_shaped(interp):
                    continue
                if isinstance(interp, ast.Name):
                    value = _nearest_assign(interp.id, call.lineno, scope_assigns)
                    if value is None and func is not None:
                        value = _nearest_assign(interp.id, call.lineno,
                                                module_assigns)
                    if value is not None and _is_cast_shaped(value):
                        continue
                kind = ("variable-length path-bound interpolation without "
                        "the int-cast")
            remedy = ("an allowlist membership guard"
                      if code == "CI-01"
                      else "the int-cast (hop_bound = max(1, int(x)))")
            findings.append(
                f"{rel}:{base + call.lineno}: {code} Cypher {kind} - "
                f"$parameters cannot fill this position (6301: values are "
                f"bound with $parameters, never interpolated into the "
                f"string; 6304: parameters cannot set variable-length path "
                f"bounds), so the interpolated value reaches the query "
                f"engine raw; guard it with {remedy}, the corpus-taught "
                f"idiom")
            break  # one finding per execution call


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
    print(f"cypher_interp_scan: {len(findings)} findings "
          f"(CI-01 Cypher label/rel-type position interpolation, CI-02 "
          f"variable-length path-bound interpolation without cast) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
