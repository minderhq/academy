#!/usr/bin/env python3
"""unsafe dynamic-execution gate for the PROJECT-OMEGA corpus.

UE-01  a ```python fence must not call the builtin ``eval()`` or
       ``exec()`` with a single positional argument (no explicit
       globals/locals, no keywords). An LLM-taught corpus makes this
       class sharper than in ordinary code: the string handed to
       eval/exec is routinely MODEL OUTPUT - a ReAct calculator tool,
       a function-calling action parser - so the single-argument call
       is a live prompt-injection -> arbitrary-code-execution path.
       The corpus itself teaches the danger: 7500-security's practice
       answers label ``eval(malicious_code)`` a "Dangerous function"
       and the phase7 README's Pitfall 2 marks
       ``result = eval(user_code)  # DANGEROUS!`` as the Wrong
       pattern - while 13 corpus sites taught the bare call as the
       go-to calculator implementation.

Out of the class by construction:

  - ``.eval()`` method calls (PyTorch module eval-mode) are Attribute
    nodes, not builtin Name calls - the AST walk never sees them.
  - ``ast.literal_eval`` is a different Name.
  - a call carrying >= 2 positional args or any keyword
    (``eval(expr, {"__builtins__": {}}, {...})``) is the sandboxed
    craft the corpus already ships 12 of - explicit restricted
    globals/locals (LAB-004, 7103, QUICK-REF-VOLUME-7 idiom).
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, on any line of the fence) is
    deliberate danger-teaching, the pattern-shown-to-avoid form; the
    phase7 README's Pitfall 2 fence is the born example.

Comment-only mentions and prose never reach the class: the check
walks ast.Call nodes, not text.

Hard gate (exit 1 on findings): the born census read 27 builtin
eval/exec calls across 17 files - 12 already the two-argument sandbox
idiom, 2 bare inside marked danger-teaching fences (the phase7 README
Pitfall 2, LAB-004's SECURITY-WARNING fence), and 13 unmarked bare
sites across 9 files - drained the same tick to the sandbox idiom.

Run over the whole corpus:
    python scripts/qa/unsafe_exec_scan.py --root .
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

UNSAFE_BUILTINS = ("eval", "exec")


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    in_fence = False
    lang = ""
    start = 0
    fence_lines: list[str] = []
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


def _scan_fence(rel: str, start: int, fence_lines: list[tuple[int, str]],
                findings: list[str]) -> None:
    src = "\n".join(raw for _, raw in fence_lines)
    if DANGER_MARKER_RE.search(src):
        return
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    base = start
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in UNSAFE_BUILTINS
                and len(node.args) == 1 and not node.keywords):
            findings.append(
                f"{rel}:{base + node.lineno}: UE-01 unsandboxed builtin "
                f"{node.func.id}() on a single argument - model output runs "
                f"with full globals (prompt-injection -> code execution); "
                f"use the two-argument sandbox idiom "
                f"{node.func.id}(expr, {{\"__builtins__\": {{}}}}, {{}}) or a "
                f"danger-marked teaching fence")


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
    print(f"unsafe_exec_scan: {len(findings)} findings "
          f"(UE-01 single-argument builtin eval()/exec() in python "
          f"fences without a danger marker) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
