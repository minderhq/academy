#!/usr/bin/env python3
"""legacy-chain bare-usage gate for the PROJECT-OMEGA corpus.

LC-01 (langchain_census) tars import lines - but not1 (tick-205 lesson)
holds that an UNIMPORTED usage is invisible to it: CP-001 shipped
`rag_chain = RetrievalQA.from_chain_type(...)` with no import line at
all, and every gate stayed green while the snippet raised
ModuleNotFoundError on the installed stack (tick-223, langchain 1.4.2:
`langchain.chains` does not exist; `langchain.agents` exists but no
longer carries AgentExecutor/initialize_agent).

LC-02  a name from the removed langchain_classic chain/agent surface
       is USED as a bare Name load in a python fence while never being
       bound anywhere in the document (two-pass doc model, same rule
       as kwarg_lint/fence_namecheck: a class or function defined
       inside the same document shadows the installed library, so
       teaching wrappers are out of scope).

Hard gate (exit 1 on findings): the only real corpus site drained in
tick-223; every entry in REMOVED_NAMES was empirically verified absent
from the installed langchain 1.x surface, so a bare use is guaranteed
NameError at runtime. Teaching mentions live in prose or comments,
which are not Name nodes.

Run over the whole corpus:
    python scripts/qa/legacy_chain_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

# langchain_classic names verified absent from the installed langchain
# 1.x surface (tick-224: langchain.chains raises ModuleNotFoundError;
# langchain.agents exposes create_agent only). Extend only after an
# empirical import check against the installed stack.
REMOVED_NAMES = {
    "RetrievalQA",
    "LLMChain",
    "AgentExecutor",
    "initialize_agent",
    "ConversationalRetrievalChain",
    "load_qa_chain",
    "ConversationChain",
    "create_openai_functions_agent",
    "create_react_agent",
}


def _defined_names(trees: list[tuple[ast.AST, int]]) -> set[str]:
    """Class/function/assignment names defined anywhere in the document."""
    names: set[str] = set()
    for tree, _off in trees:
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        names.add(t.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target,
                                                                ast.Name):
                names.add(node.target.id)
    return names


def scan_trees(rel: str, trees: list[tuple[ast.AST, int]], defined: set[str],
               findings: list[str], counts: dict[str, int]) -> None:
    for tree, line_offset in trees:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Name) or node.id not in REMOVED_NAMES:
                continue
            if not isinstance(node.ctx, ast.Load) or node.id in defined:
                continue  # bound locally (import/def/assign) -> shadow rule
            counts["LC-02"] += 1
            findings.append(
                f"{rel}:{node.lineno + line_offset}: "
                f"LC-02 bare use of '{node.id}' - langchain_classic-only "
                f"name, absent from installed langchain 1.x (NameError at "
                f"runtime); compose the modern equivalent instead")


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
    scan_trees(rel, trees, _defined_names(trees), findings, counts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    counts = {"LC-02": 0}
    n_files = set()
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
    print(f"legacy_chain_scan: {len(findings)} findings "
          f"(LC-02 bare langchain_classic name uses: {counts['LC-02']}) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
