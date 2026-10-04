#!/usr/bin/env python3
"""async-block gate for the Minder Academy corpus.

AB-01  an ```python fence must not call a blocking ``requests`` verb
       (get/post/put/patch/delete/head/options/request) lexically
       inside an ``async def`` body. The requests client is
       synchronous: the HTTP round-trip runs on the event-loop thread,
       so while the call waits on the network the whole loop is
       frozen - every other coroutine (concurrent requests,
       heartbeats, websockets, sibling FastAPI handlers) stalls
       behind it. In a FastAPI handler the "concurrent" server serves
       one request at a time; under load the API's throughput
       collapses to the blocking call's latency. Python's answers,
       and the corpus teaches both: hand the blocking call to a
       worker thread with ``await asyncio.to_thread(requests.post,
       ...)`` (CHEAT-SHEET-005, 3502-Audio) or use a native async
       client, ``httpx.AsyncClient`` (TUTORIAL-012, 1403-vLLM-Production)
       - while the corpus's own 13 sites taught the frozen-loop form.

AB-02  the same fence must not call ``time.sleep(...)`` inside an
       ``async def``. time.sleep parks the OS thread the loop runs
       on; ``await asyncio.sleep(...)`` is the async-native form that
       lets other coroutines run. Born census: 0 sites - this class
       froze hard from birth.

Out of the class by construction:

  - blocking calls in plain sync ``def`` bodies - the sync universe
    is the corpus's default and blocking there is the normal, correct
    form; the walk enters AsyncFunctionDef bodies only, and stops at
    nested sync defs/lambdas (their calls belong to those scopes,
    e.g. an asyncio.to_thread target).
  - nested ``async def`` scopes are their own innermost scope - each
    call reports once, attributed to the innermost async body.
  - the affirmative forms: ``await asyncio.to_thread(...)``,
    ``await asyncio.sleep(...)``, ``httpx.AsyncClient`` - the walk
    fires only on the requests verbs and the time base.
  - non-verb requests attributes (``requests.Session``,
    ``requests.exceptions``) - the walk demands the verb set.
  - bare ``sleep(...)`` after ``from time import sleep`` - the walk
    demands the ``time`` Name base, the sibling bare-form rule.
  - string mentions and prose never reach the walk (AST, not text).
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, any line) is deliberate
    danger-teaching, the sibling unsafe_*/interp/crypto escape.
  - notebooks (.ipynb) are outside the md universe.

Hard gate (exit 1 on findings): born census tick-658 read every call
in every async def body in every md python fence fence-aware =
exactly 13 findings, all AB-01 requests-verb calls inside async def
across 5 files - drained the same tick in-line (each call wrapped in
``await asyncio.to_thread(...)`` with the fence's import block
gaining ``import asyncio``, the corpus's own taught escape hatch),
returning the class to zero-drain hard from the rule's naming.

Run over the whole corpus:
    python scripts/qa/async_block_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

DANGER_MARKER_RE = re.compile(r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)

VERBS = {"get", "post", "put", "patch", "delete", "head", "options", "request"}

FINDING_REQ = (" blocking requests.{verb} inside async def freezes the "
               "event loop for the whole HTTP round-trip - wrap it with "
               "await asyncio.to_thread(...) or use a native async client "
               "(httpx.AsyncClient)")

FINDING_SLEEP = (" time.sleep inside async def parks the loop's "
                 "thread - await asyncio.sleep(...) is the async-native form")


def _classify(call: ast.Call) -> tuple[str, str] | None:
    f = call.func
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
        if f.attr in VERBS and f.value.id == "requests":
            return "AB-01", f"requests.{f.attr}"
        if f.attr == "sleep" and f.value.id == "time":
            return "AB-02", "time.sleep"
    return None


def _scope_calls(fn: ast.AsyncFunctionDef):
    """Calls in this async body's innermost lexical scope.

    Stops at nested function definitions and lambdas (sync or async):
    a nested sync def's calls belong to that scope (it may be the
    asyncio.to_thread target), and a nested async def is picked up as
    its own scope by the outer walk - each call reports exactly once.
    """
    todo = list(ast.iter_child_nodes(fn))
    while todo:
        n = todo.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        if isinstance(n, ast.Call):
            yield n
        todo.extend(ast.iter_child_nodes(n))


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

    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        for call in _scope_calls(node):
            hit = _classify(call)
            if hit is None:
                continue
            code, name = hit
            msg = FINDING_REQ.format(verb=name.split(".", 1)[1]) \
                if code == "AB-01" else FINDING_SLEEP
            findings.append(f"{rel}:{base + call.lineno}: {code}{msg}")


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
    print(f"async_block_scan: {len(findings)} findings "
          f"(AB-01 blocking requests verb / AB-02 time.sleep in async def) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
