#!/usr/bin/env python3
"""undefined-name scanner for python fences (report mode).

The langchain-modernization epic documented a census blind spot: fences
that USE names never imported or defined raise NameError at runtime but
have no broken import line to flag (UC-003: 8 latent NameErrors; 7401:
3 fences using datetime without importing it). codeblock_syntax_scan
proves the fence PARSES; this scanner asks whether the names it uses are
bound anywhere.

Model per .md file, two passes: pass 1 collects every name bound by ANY
python fence in the document (import asnames, assignments, defs, params,
for/with/except/comprehension targets); pass 2 flags names loaded in a
fence that no fence in the document ever binds. This "fragment idiom"
tolerance matches how the corpus teaches: a lesson may show a usage
snippet before (or instead of) its setup snippet, and only a name bound
nowhere is a latent NameError for the student who assembles the pieces.

Known noise (accepted for the report pass; triage before gating):
pseudo-code fragments that never bind their names by design (agent-UI
sketches like Tool(...)/Agent(...) where imports are deliberately
elided), wildcard imports making their fence opaque (check skipped),
and non-Python content that happens to parse as Python (e.g. nginx
`ssl_certificate /etc/...` is a valid division-chain expression) -
those are honest-label findings, not NC-01. Report-only: exit 0 always.

    python scripts/qa/fence_namecheck.py --root .
    python scripts/qa/fence_namecheck.py --root . --names   # triage:
        aggregate NC-01 uses by name (epic scoping; skips per-line output)
    python scripts/qa/fence_namecheck.py --root . --names --name model
        drill down: per-file distribution of one name's unbound uses
"""
from __future__ import annotations

import argparse
import ast
import builtins
import re
import sys
from collections import Counter
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

BUILTINS = set(dir(builtins))
IGNORED = BUILTINS | {"__file__", "__doc__", "__annotations__", "__package__",
                      "self", "cls", "args", "kwargs"}


def bound_names(tree: ast.AST) -> set[str]:
    """All names this fence binds, at any nesting level (two-pass input)."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            for a in node.names:
                if a.name == "*":
                    continue  # wildcard: handled as fence opacity
                names.add(a.asname or a.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.Global) or isinstance(node, ast.Nonlocal):
            names.update(node.names)
    return names


def used_names(tree: ast.AST) -> set[tuple[str, int]]:
    """(name, lineno) for every Load-context Name."""
    return {(n.id, n.lineno) for n in ast.walk(tree)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def python_fences(lines: list[str]) -> list[tuple[int, str]]:
    """(fence_start_line, source) for every ```python fence."""
    fences: list[tuple[int, str]] = []
    in_fence = False
    lang = ""
    fence_start = 0
    fence_src: list[str] = []
    for i, raw in enumerate(lines):
        m = FENCE_RE.match(raw)
        if m:
            if in_fence and lang == "python":
                fences.append((fence_start, "\n".join(fence_src)))
            in_fence = not in_fence
            lang = "" if not in_fence else m.group(2).lower()
            if in_fence:
                fence_start = i + 1
                fence_src = []
            continue
        if in_fence:
            fence_src.append(raw)
    return fences


def check_file(root: Path, path: Path, findings: list[str],
               records: list[tuple[str, str]] | None = None) -> None:
    """Append NC-01 findings; when `records` is given, also (name, rel) pairs."""
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")

    # pass 1: every name any python fence binds, regardless of position
    doc_bound: set[str] = set()
    trees: list[tuple[int, str, ast.AST, bool]] = []  # (start, src, tree, wildcard)
    for start, src in python_fences(lines):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue  # codeblock_syntax_scan owns syntax findings
        wildcard = any(isinstance(n, ast.ImportFrom) and
                       any(a.name == "*" for a in n.names)
                       for n in ast.walk(tree))
        doc_bound |= bound_names(tree)
        trees.append((start, src, tree, wildcard))

    # pass 2: Load names no fence in this document ever binds
    for start, src, tree, wildcard in trees:
        if wildcard:
            continue  # opaque: can't know what a wildcard import binds
        for name, ln in sorted(used_names(tree)):
            if (name not in IGNORED and name not in doc_bound):
                if records is not None:
                    records.append((name, rel))
                findings.append(
                    f"{rel}:{start + ln}: NC-01 name "
                    f"'{name}' used but never bound in this document's "
                    f"python fences - {src.splitlines()[ln - 1].strip()[:60]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--names", action="store_true",
                        help="triage: aggregate NC-01 uses by name instead of "
                             "printing per-line findings")
    parser.add_argument("--name", metavar="NAME",
                        help="drill-down for --names: per-file distribution "
                             "of one name's unbound uses")
    args = parser.parse_args()
    if args.name:
        args.names = True  # drill-down implies triage mode
    docs = args.root / "docs"
    findings: list[str] = []
    records: list[tuple[str, str]] = []
    for path in sorted(docs.rglob("*.md")):
        try:
            check_file(args.root, path, findings,
                       records if args.names else None)
        except (UnicodeDecodeError, OSError, SyntaxError, ValueError):
            continue
    if args.names:
        if args.name:
            files = Counter(rel for name, rel in records if name == args.name)
            print(f"fence_namecheck drill: {sum(files.values())} unbound uses of "
                  f"'{args.name}' in {len(files)} files")
            for rel, n in files.most_common(40):
                print(f"  {n:4d}  {rel}")
        else:
            counts = Counter(name for name, _ in records)
            print(f"fence_namecheck triage: {sum(counts.values())} NC-01 uses of "
                  f"{len(counts)} distinct unbound names (top 60)")
            for name, n in counts.most_common(60):
                print(f"  {n:4d}  {name}")
    for f in ([] if args.names else findings):
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    n_files = len({f.split(":", 1)[0] for f in findings})
    print(f"fence_namecheck: {len(findings)} NC-01 findings in {n_files} files "
          f"across docs/ (report mode - exit 0 by design)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
