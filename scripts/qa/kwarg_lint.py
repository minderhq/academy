#!/usr/bin/env python3
"""kwarg-lint gate for the Minder Academy curriculum corpus.

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
KW-03  a call to a method the library has removed entirely:
       qdrant-client >= 1.10 removed QdrantClient.search_batch() in
       favor of query_batch_points(QueryRequest(...)). Verified
       against the installed stack (qdrant-client 1.19.0):
       .search_batch is gone (AttributeError). Fires only in
       documents whose fences import qdrant_client: KW-02's kwarg
       names (query_vector=) are qdrant-specific by signature, a
       method name like .search_batch is not, so it needs import
       evidence. No locally-defined-name shadow (unlike KW-01's
       constructor model): the birth census (tick-326) found zero
       locally defined search_batch methods, and a blanket
       document-wide shadow would suppress a raw QdrantClient call
       in any doc that also teaches a same-named custom method -
       the census->classify->lock path adds a scoped shadow if a
       real doc ever needs one. Born from the tick-324 blind-spot
       note - KW-02 sees only kwargs, and the tick-326 drain found
       the migration-leak class alive in a troubleshooting doc
       (qdrant.search_batch + SearchRequest, both removed).

Hard gate (exit 1 on findings): the legacy .search(queue) drained to
zero across ticks 216-220 and the .search_batch queue drained at
tick-326; any new query_vector=/query_filter= on a .search attribute
call, or a new .search_batch( call in a qdrant-importing document, is
a runtime AttributeError on the installed qdrant-client >= 1.10
stack. fence_namecheck remains the only report-mode gate (its NC-01
fragment-idiom queue is accepted).

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

# Removed-method rule: {method attr: replacement hint}. Unlike KW-02's
# kwarg names (qdrant-specific by signature), a method name like
# .search_batch is not qdrant-specific - so this fires only in
# documents whose fences import qdrant_client. No locally-defined-name
# shadow: birth census (tick-326) has zero locally defined
# search_batch methods, and a blanket document-wide shadow would
# suppress a raw QdrantClient call in a mixed doc.
REMOVED_METHODS = {
    "search_batch": "qdrant-client >= 1.10 removed .search_batch(); "
                    "use .query_batch_points(QueryRequest(...))",
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


def _imported_roots(trees: list[tuple[ast.AST, int]]) -> set[str]:
    """Top-level package names imported anywhere in the document."""
    roots: set[str] = set()
    for tree, _off in trees:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    roots.add(alias.name.partition(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module \
                    and node.level == 0:
                roots.add(node.module.partition(".")[0])
    return roots


def lint_trees(rel: str, trees: list[tuple[ast.AST, int]], defined: set[str],
               roots: set[str], findings: list[str],
               counts: dict[str, int]) -> None:
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
                if removed:
                    bad = {kw.arg for kw in node.keywords if kw.arg
                           and kw.arg in removed}
                    if bad:
                        counts["KW-02"] += 1
                        findings.append(
                            f"{rel}:{node.lineno + line_offset}: "
                            f"KW-02 .{func.attr}("
                            f"{', '.join(sorted(bad))}=...) - "
                            + removed[next(iter(bad))])
                    continue
                hint = REMOVED_METHODS.get(func.attr)
                if hint and "qdrant_client" in roots:
                    counts["KW-03"] += 1
                    findings.append(
                        f"{rel}:{node.lineno + line_offset}: "
                        f"KW-03 .{func.attr}(...) removed method - {hint}")


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
    lint_trees(rel, trees, _defined_names(trees), _imported_roots(trees),
               findings, counts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    counts = {"KW-01": 0, "KW-02": 0, "KW-03": 0}
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
          f"KW-02 removed qdrant .search kwargs: {counts['KW-02']}; "
          f"KW-03 removed qdrant methods: {counts['KW-03']}) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
