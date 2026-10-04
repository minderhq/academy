#!/usr/bin/env python3
"""un-awaited-coroutine gate for the PROJECT-OMEGA corpus.

UC-01  a ```python fence must not discard a fence-local coroutine: a
       bare-Name call to an ``async def`` defined in the same fence,
       standing alone as a full statement (``fetch_data()`` on its own
       line - no ``await``, no consumer, result dropped), creates the
       coroutine object and throws it away. The work never runs; Python
       only whispers ``RuntimeWarning: coroutine 'fetch_data' was never
       awaited`` after the fence has already moved on, so the reader
       copies a snippet whose I/O silently never happens.

       The affirmative forms are taught by the corpus itself: the direct
       ``await fetch_data()``; ``await asyncio.gather(...)``
       over collected or generator-expression calls (CHEAT-SHEET-005:501,
       1403-vLLM-Production:680); ``async for token in stream_tokens(...)``
       - the implicit await (PROJECT-007:337, 2303:559); the async
       generator handed to its consumer ``StreamingResponse(generate(),
       ...)`` (TEMPLATE-010:126, TUTORIAL-006:391, 2303:574); and the
       ``asyncio.run(main())`` entry-point idiom (10 sites).

Out of the class by construction:

  - every consumed form: the call in argument position (a call inside
    another call, a return value, an assignment), inside a list/set/dict
    comprehension or generator expression (collected, then gathered),
    under ``await``, under ``async for`` - the walk fires only when the
    call IS the entire statement (``ast.Expr`` whose value is the call).
  - ``asyncio.run(main())`` - the entry-point idiom: the inner call is
    argument-position, and ``asyncio.run`` itself is an Attribute call,
    never a bare fence-local name.
  - a bare call to a name that resolves to a plain sync ``def`` - the
    walk demands the name be defined ``async`` in the same fence.
  - a name defined BOTH sync and async in the same fence (the corpus
    teaches 3 such pairs: LAB-012 ``synthesize``, 2303 ``predict`` /
    ``predict_batch``) stays silent - the call might be the sync one,
    so only single-resolution names enter the class.
  - the named-discard idiom ``_ = coro()`` and the assign form
    ``x = coro()`` (Assignment, not Expr statement) - result-level
    dataflow is outside the statement-level proof.
  - string mentions and prose never reach the walk (AST, not text).
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, any line) is deliberate
    danger-teaching, the sibling unsafe_*/interp/crypto escape.
  - notebooks (.ipynb) are outside the md universe.

Hard gate (exit 1 on findings): born census tick-659 read every
statement in every md python fence fence-aware = exactly 0 discarded
statements across 1861 fences / 197 async defs - the corpus never
teaches the dropped-coroutine form, so this class froze hard from
birth (the preemptive-ownership shape of insecure_temp/crypto).

Run over the whole corpus:
    python scripts/qa/unawaited_coro_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

DANGER_MARKER_RE = re.compile(r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)

FINDING = (" discarded coroutine: {name}() stands alone as a statement - "
           "the coroutine object is created and dropped, the work never "
           "runs (RuntimeWarning: ... was never awaited) - await it, or "
           "hand it to asyncio.gather/create_task, or iterate it with "
           "async for")


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

    async_names = {n.name for n in ast.walk(tree)
                   if isinstance(n, ast.AsyncFunctionDef)}
    sync_names = {n.name for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef)}
    # single resolution: a name shadowed by a same-fence sync def could
    # be the sync call, so it stays out of the class
    fire = async_names - sync_names
    if not fire:
        return

    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        f = node.value.func
        if isinstance(f, ast.Name) and f.id in fire:
            msg = FINDING.format(name=f.id)
            findings.append(f"{rel}:{base + node.lineno}: UC-01{msg}")


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
    print(f"unawaited_coro_scan: {len(findings)} findings "
          f"(UC-01 bare-statement calls to fence-local async defs) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
