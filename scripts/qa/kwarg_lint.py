#!/usr/bin/env python3
"""kwarg-lint gate for the PROJECT-OMEGA curriculum corpus.

LC-01 (langchain_census) resolves import lines and NC-01
(fence_namecheck) resolves name bindings - but neither reads the
keyword arguments of a call. A snippet can import and bind a real,
installed API and still be runtime-broken because it calls it with
removed or renamed kwargs: the kwarg-blind gap that let UC-003's
canonical QdrantVectorStore block ship with `embeddings=` and no
client until the tick-215 construction smoke tests caught it.

KW-01  a known langchain constructor called with a removed kwarg, or
       missing a required kwarg (two-pass doc model: a class defined
       inside the same document shadows the installed one -
       phase6-practice.md defines its own QdrantVectorStore teaching
       wrapper, so its call sites are not langchain calls)
KW-02  a call passing a kwarg a library has removed entirely:
       qdrant-client >= 1.10 removed QdrantClient.search(query_vector=)
       / query_filter= in favor of query_points(query=..., ...).
       Verified against the installed stack (qdrant-client 1.19.0):
       .search no longer exists (AttributeError); query_points works.

Report mode (exit 0 always, like fence_namecheck): the corpus is
mid-migration between the legacy and modern qdrant idioms, so KW-02
currently reports a drain queue. Once the queue reaches zero the gate
flips to exit 1 on findings and joins the hard gates.

Run over the whole corpus:
    python scripts/qa/kwarg_lint.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

# Evidence-based rule table; extend only with empirically verified
# signatures (run the call against the installed stack first).
CONSTRUCTOR_RULES: dict[str, dict[str, set[str]]] = {
    # langchain_qdrant (verified tick-215): __init__(client,
    # collection_name, embedding=None, ...). `embeddings=` raises
    # TypeError ("Did you mean 'embedding'?"); connection kwargs
    # (url/location/...) belong to from_documents()/QdrantClient, and
    # a direct constructor requires a reachable server + collection.
    "QdrantVectorStore": {
        "forbidden": {"embeddings", "location", "url", "path",
                      "prefer_grpc", "https", "api_key", "prefix",
                      "timeout", "shard_selection_fn"},
        "required": {"client", "collection_name", "embedding"},
    },
}

# Removed-kwargs rule: {method attr: {forbidden kwarg: replacement hint}}
REMOVED_KWARGS = {
    "search": {
        "query_vector": "qdrant-client >= 1.10 removed .search(); "
                        "use .query_points(query=...)",
        "query_filter": "qdrant-client >= 1.10 removed .search(); "
                        "use .query_points(query_filter=...)",
    },
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


def lint_trees(rel: str, trees: list[tuple[ast.AST, int]], defined: set[str],
               findings: list[str], counts: dict[str, int]) -> None:
    for tree, line_offset in trees:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name):
                rule = CONSTRUCTOR_RULES.get(func.id)
                if not rule or func.id in defined:
                    continue  # locally defined class shadows the library
                kwargs = {kw.arg for kw in node.keywords if kw.arg}
                bad = kwargs & rule["forbidden"]
                missing = rule["required"] - kwargs
                if bad or missing:
                    counts["KW-01"] += 1
                    detail = []
                    if bad:
                        detail.append("removed kwarg(s): %s"
                                      % ", ".join(sorted(bad)))
                    if missing:
                        detail.append("missing required kwarg(s): %s"
                                      % ", ".join(sorted(missing)))
                    findings.append(
                        f"{rel}:{node.lineno + line_offset}: "
                        f"KW-01 {func.id}(...) - "
                        + "; ".join(detail))
            elif isinstance(func, ast.Attribute):
                removed = REMOVED_KWARGS.get(func.attr)
                if not removed:
                    continue
                bad = {kw.arg for kw in node.keywords if kw.arg
                       and kw.arg in removed}
                if bad:
                    counts["KW-02"] += 1
                    findings.append(
                        f"{rel}:{node.lineno + line_offset}: "
                        f"KW-02 .{func.attr}("
                        f"{', '.join(sorted(bad))}=...) - "
                        + removed[next(iter(bad))])


def lint_file(root: Path, path: Path, findings: list[str],
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
    lint_trees(rel, trees, _defined_names(trees), findings, counts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    counts = {"KW-01": 0, "KW-02": 0}
    n_files = set()
    for path in sorted(docs.rglob("*.md")):
        try:
            before = len(findings)
            lint_file(args.root, path, findings, counts)
            if len(findings) > before:
                n_files.add(path.relative_to(args.root).as_posix())
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"kwarg_lint: {len(findings)} kwarg findings "
          f"(KW-01 langchain constructors: {counts['KW-01']}; "
          f"KW-02 removed qdrant .search kwargs: {counts['KW-02']}) "
          f"in {len(n_files)} files across docs/")
    return 0  # report mode until the KW-02 queue drains


if __name__ == "__main__":
    sys.exit(main())
