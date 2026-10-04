#!/usr/bin/env python3
"""CORS wildcard+credentials gate for the PROJECT-OMEGA corpus.

COR-01  a ```python fence configuring CORS must not combine a wildcard
        origin list (``allow_origins=["*"]``) with credential support
        (``allow_credentials=True``). The Fetch spec forbids the pair:
        a credentialed cross-origin request requires the response to
        name the actual origin - ``Access-Control-Allow-Origin: *``
        alongside ``Access-Control-Allow-Credentials: true`` is an
        invalid combination the browser rejects, so the fence's CORS
        setup silently fails for exactly the logged-in users it was
        configured to serve; and middleware stacks that reflect the
        request origin under the wildcard+credentials pair instead
        hand EVERY origin credentialed access (CSRF-class exposure:
        any site can ride a user's session cookies). The fix the
        corpus itself teaches is the explicit origin list - the
        TEMPLATE-010 dev form ``allow_origins=["http://localhost:3000"]``
        and the TUTORIAL-014 production form
        ``allow_origins=["https://yourdomain.com"]``.

Out of the class by construction:

  - wildcard WITHOUT credentials - a public API open to every origin
    is a deliberate, spec-valid teaching form (no cookie rides).
  - credentials WITH an explicit origin list - the safe form, 2 of the
    corpus's 4 CORS sites (TEMPLATE-010, TUTORIAL-014).
  - ``allow_credentials=False`` (or any non-True constant) next to a
    wildcard - no credential channel, the pair is not formed.
  - ``allow_methods=["*"]``/``allow_headers=["*"]`` wildcards - the
    origin header is the spec's hard constraint; methods/headers
    wildcard scope is a different (weaker) lesson and all 4 corpus
    sites teach the wildcard there by design.
  - non-constant origins (a Name/Call expression in the list) - only
    literal string constants enter the wildcard check.
  - other middleware names - the walk attaches only on
    ``add_middleware`` whose first argument is the CORSMiddleware
    class (a bare Name - the corpus's only form - a direct constructor
    Call, or a string name) or a direct ``CORSMiddleware(...)`` call.
  - string mentions and prose never reach the walk (AST, not text).
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, any line) is deliberate
    danger-teaching, the sibling unsafe_*/interp/crypto escape.
  - notebooks (.ipynb) are outside the md universe.

Hard gate (exit 1 on findings): born census tick-656 read every CORS
call in every md python fence fence-aware = exactly 2 findings, both
COR-01 (LAB-007-Production-RAG and TUTORIAL-006-Real-time-AI - the
"Production" lab itself teaching the invalid pair) - drained the same
tick in-line (origin lists swapped for the corpus's own explicit forms,
zero line shift so the exec-census baseline rows at LAB-007:921 and
TUTORIAL-006:141 keep their coordinates), returning the class to
zero-drain hard from the rule's naming.

Run over the whole corpus:
    python scripts/qa/cors_wildcard_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

DANGER_MARKER_RE = re.compile(r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)

FINDING = (": COR-01 CORS wildcard origins combined with "
           "allow_credentials=True - the Fetch spec forbids the pair "
           "(a credentialed cross-origin request must name the actual "
           "origin; wildcard + credentials is rejected by browsers or "
           "reflected into every-origin credentialed access); list "
           "explicit origins or drop the credential support")


def _is_wildcard(value: ast.expr) -> bool:
    # literal string constants only - a Name/Call origin is out of scope.
    if isinstance(value, ast.Constant) and value.value == "*":
        return True
    if isinstance(value, ast.List):
        return any(isinstance(e, ast.Constant) and e.value == "*"
                   for e in value.elts)
    return False


def _cors_attached(call: ast.Call) -> bool:
    func = call.func
    name = func.id if isinstance(func, ast.Name) else (
        func.attr if isinstance(func, ast.Attribute) else None)
    if name == "CORSMiddleware":
        return True
    if name == "add_middleware" and call.args:
        first = call.args[0]
        # the class arrives as a bare Name (the corpus's only form), a
        # direct constructor Call, or a string name.
        if isinstance(first, ast.Name) and first.id == "CORSMiddleware":
            return True
        if isinstance(first, ast.Constant) and first.value == "CORSMiddleware":
            return True
        if isinstance(first, ast.Call):
            inner = first.func
            inner_name = inner.id if isinstance(inner, ast.Name) else (
                inner.attr if isinstance(inner, ast.Attribute) else None)
            if inner_name == "CORSMiddleware":
                return True
    return False


def _scan_fence(rel: str, start: int, fence_lines: list[tuple[int, str]],
                findings: list[str]) -> None:
    src = "\n".join(raw for _, raw in fence_lines)
    if DANGER_MARKER_RE.search(src):
        return
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    base = start  # fence content line 1 == fence-open line + 1

    class _Collector(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            if _cors_attached(node):
                origins = None
                credentials = None
                for kw in node.keywords:
                    if kw.arg == "allow_origins":
                        origins = kw.value
                    elif kw.arg == "allow_credentials":
                        credentials = kw.value
                if origins is not None and _is_wildcard(origins) \
                        and credentials is not None \
                        and isinstance(credentials, ast.Constant) \
                        and credentials.value is True:
                    findings.append(f"{rel}:{base + node.lineno}{FINDING}")
            self.generic_visit(node)

    _Collector().visit(tree)


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
    print(f"cors_wildcard_scan: {len(findings)} findings "
          f"(COR-01 CORS wildcard origins + allow_credentials=True) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
