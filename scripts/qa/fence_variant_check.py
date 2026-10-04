#!/usr/bin/env python3
"""Fence variant near-miss gate for the Minder Academy corpus.

Every illustrative ```python fence is parsed as AST. A bare name that
is LOADED but defined nowhere - not in its innermost function scope,
not in enclosing scopes (closures), not in the fence's module scope,
not in any other python fence of the same document (the established
cross-fence fragment idiom), not a builtin - is reported WHEN it is a
lexical variant of a name that IS in scope: case-insensitive equal,
length-aware levenshtein (<=2 for len>=5, <=1 for len>=3), or
underscore-word prefix. Exactly the tick-330 census class:
vocab_size vs vocab, calculate vs calculator_function, range(epochs)
vs the epoch loop var - real NameError-shaped slips that look
plausible because a near-miss sibling exists.

PY-01  a loaded name is an undefined variant of an in-scope name.

Hard gate (exit 1 on findings): born at baseline 0 from the tick-330
census (260 docs, 1857 python fences, 7 survivors -> 3 real drains in
5d2dc13, 4 false positives absorbed by design below):
  - lambda/nested-def bodies resolve against the enclosing scope chain
    (TUTORIAL-012 pick_winner's `metric` closure is correct code),
  - two per-document ambient names are allowlisted with a reason:
    IND-002 `compliance_checker` is a service object in the same
    ambient idiom as position_checker/ai_model/audit_trail in that
    excerpt, 7101-ReAct `Plan` is an ambient planning class used
    corpus-wide as a concept (plan.steps/_revise_plan interface).

Out of scope v1: module-level bare loads (fragment-densest region,
future PY-02 candidate) and imports (fence_import_check IC-01 owns
import validity). Syntax-error fences are skipped: codeblock_syntax_
scan owns parseability.

Run over the whole corpus:
    python scripts/qa/fence_variant_check.py --root .
"""
from __future__ import annotations

import argparse
import ast
import builtins
import re
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^ {0,3}```(\w*)\s*$")
BUILTINS = set(dir(builtins))

# (doc relpath, undefined name) -> accepted ambient idiom, with reason
ACCEPTED: dict[tuple[str, str], str] = {
    ("docs/industry/IND-002-Finance-AI-Applications.md",
     "compliance_checker"):
        "ambient service object (same idiom as position_checker/"
        "ai_model/audit_trail in that excerpt)",
    ("docs/phases/phase7-agentic/7100-architecture/"
     "7101-ReAct-Loop-System.md", "Plan"):
        "ambient planning class (plan.steps/_revise_plan interface)",
    ("docs/comparisons/CP-001-RAG-vs-FineTuning-vs-Agents.md",
     "search_function"):
        "established placeholder idiom: @tool wrappers delegating to "
        "unshown backend functions (search/calculator/database)",
    ("docs/comparisons/CP-001-RAG-vs-FineTuning-vs-Agents.md",
     "calculator_function"):
        "established placeholder idiom: @tool wrappers delegating to "
        "unshown backend functions (search/calculator/database)",
    ("docs/comparisons/CP-001-RAG-vs-FineTuning-vs-Agents.md",
     "database_function"):
        "established placeholder idiom: @tool wrappers delegating to "
        "unshown backend functions (search/calculator/database)",
}

ATTR_ALLOWED = {
    "training", "parameters", "named_parameters", "buffers",
    "to", "eval", "train", "apply", "state_dict", "load_state_dict",
    "device", "dtype", "modules", "children", "zero_grad", "cuda",
    "cpu", "half", "float", "bfloat16", "forward", "register_buffer",
    "__dict__", "assertEqual", "formatException", "log", "name",
    "verbose",
}


def lev(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 2:
        return 99
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def words(s: str) -> list[str]:
    return [w for w in re.split(r"[_\d]+", s.lower()) if w]


def is_variant(a: str, b: str) -> bool:
    if a.lower() == b.lower():
        return True
    short = min(len(a), len(b))
    cap = 2 if short >= 5 else (1 if short >= 3 else 0)
    if cap and lev(a, b) <= cap:
        return True
    wa, wb = words(a), words(b)
    if wa and wb and wa[0] == wb[0] and (len(wa) == 1 or len(wb) == 1):
        return True
    return False


def best_variant(name: str, defined: set[str]) -> str | None:
    # bestd starts above lev()'s 99 cap so word-prefix matches (whose
    # edit distance may exceed the lev guard) still report
    best, bestd = None, 100
    for d in sorted(defined):
        if d == name:
            continue
        if is_variant(name, d):
            d2 = lev(name, d)
            if d2 < bestd:
                best, bestd = d, d2
    return best


def fences(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_fence, label, buf, start = False, "", [], 0
    for i, line in enumerate(lines, 1):
        m = FENCE_OPEN.match(line)
        if not in_fence and m:
            in_fence, label, buf, start = True, m.group(1), [], i
        elif in_fence and re.match(r"^ {0,3}```", line):
            in_fence = False
            if label == "python":
                yield start + 1, "\n".join(buf)
            buf = []
        elif in_fence:
            buf.append(line)


def defined_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(tree):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)):
            names.add(child.name)
        elif isinstance(child, ast.Import):
            for a in child.names:
                names.add((a.asname or a.name).split(".")[0])
        elif isinstance(child, ast.ImportFrom):
            for a in child.names:
                if a.name != "*":
                    names.add(a.asname or a.name)
        elif isinstance(child, ast.Name) and isinstance(child.ctx,
                                                        ast.Store):
            names.add(child.id)
    return names


def scope_locals(fn: ast.AST) -> set[str]:
    """Names bound directly in this function scope: args, stores,
    except handlers, nested def/class/lambda names."""
    names: set[str] = set()
    args = getattr(fn, "args", None)
    if args:
        allargs = (args.posonlyargs + args.args + args.kwonlyargs
                   + [a for a in (args.vararg, args.kwarg) if a])
        names.update(a.arg for a in allargs)
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef, ast.Lambda)):
            if node is not fn:
                names.add(getattr(node, "name", "<lambda>"))
    return names


def own_loads(fn: ast.AST) -> list[ast.Name]:
    """Loads bound to this scope: walk children but do not descend
    into nested function/class/lambda scopes."""
    out: list[ast.Name] = []
    stack = list(ast.iter_child_nodes(fn))
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            out.append(node)
        stack.extend(ast.iter_child_nodes(node))
    return out


def nested_scopes(fn: ast.AST) -> list[ast.AST]:
    out = []
    for node in ast.walk(fn):
        if node is not fn and isinstance(node, (ast.FunctionDef,
                                                ast.AsyncFunctionDef,
                                                ast.Lambda)):
            out.append(node)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    n_py = 0

    for path in sorted((args.root / "docs").rglob("*.md")):
        rel = path.relative_to(args.root).as_posix()
        fl = list(fences(path))
        if not fl:
            continue
        n_docs += 1
        doc_names: set[str] = set()
        trees = []
        for lineno, code in fl:
            try:
                tree = ast.parse(code)
            except SyntaxError:
                continue  # codeblock_syntax_scan owns parseability
            n_py += 1
            trees.append((lineno, code, tree))
            doc_names |= defined_names(tree)

        def check(name_node: ast.Name, visible: set[str], mod: set[str],
                  kind: str, ctx: str, lineno: int, code: str) -> None:
            nm = name_node.id
            if (nm in visible or nm in mod or nm in doc_names
                    or nm in BUILTINS):
                return
            if (rel, nm) in ACCEPTED:
                return
            v = best_variant(nm, visible | mod)
            if v:
                ln = name_node.lineno
                lines = code.splitlines()
                where = " | ".join(lines[max(0, ln - 2): ln + 1])[:90]
                findings.append(
                    f"PY-01 {rel}:{lineno} [{kind} {ctx}] '{nm}' is an "
                    f"undefined variant of '{v}' near: {where}")

        # per-fence module scope feeds the recursive closure below
        for lineno, code, tree in trees:
            mod = defined_names(tree)

            def walk(node: ast.AST, chain: set[str]) -> None:
                scope = scope_locals(node)
                visible = scope | chain
                kind = ("<lambda>" if isinstance(node, ast.Lambda)
                        else node.name)
                for sub in own_loads(node):
                    check(sub, visible, mod, "FN", kind, lineno, code)
                for child in nested_scopes(node):
                    walk(child, visible)

            for top in tree.body:
                if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    walk(top, set())

            # class attribute discipline (self.X): unchanged from census
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                attrs: set[str] = set()
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef,
                                         ast.AsyncFunctionDef)):
                        attrs.add(item.name)
                        for sub in ast.walk(item):
                            if (isinstance(sub, ast.Attribute)
                                    and isinstance(sub.value, ast.Name)
                                    and sub.value.id == "self"
                                    and isinstance(sub.ctx, ast.Store)):
                                attrs.add(sub.attr)
                for item in node.body:
                    if not isinstance(item, (ast.FunctionDef,
                                             ast.AsyncFunctionDef)):
                        continue
                    for sub in ast.walk(item):
                        if (isinstance(sub, ast.Attribute)
                                and isinstance(sub.value, ast.Name)
                                and sub.value.id == "self"
                                and isinstance(sub.ctx, ast.Load)
                                and sub.attr not in attrs
                                and sub.attr not in ATTR_ALLOWED
                                and not (sub.attr.startswith("__")
                                         and sub.attr.endswith("__"))):
                            # dunder methods are protocol hooks, never a
                            # misspelling target (_init_collection vs
                            # __init__ is a cross-fence helper, not a slip)
                            non_dunder = {
                                a for a in attrs
                                if not (a.startswith("__")
                                        and a.endswith("__"))}
                            v = best_variant(sub.attr, non_dunder)
                            if v:
                                findings.append(
                                    f"PY-01 {rel}:{lineno} [ATTR "
                                    f"{node.name}] 'self.{sub.attr}' is "
                                    f"an undefined variant of "
                                    f"'self.{v}'")

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"fence_variant_check: {len(findings)} PY-01 finding(s) "
          f"across {n_docs} docs, {n_py} python fences in docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
