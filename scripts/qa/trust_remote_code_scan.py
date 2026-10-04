#!/usr/bin/env python3
"""trust_remote_code gate for the Minder Academy corpus.

TRC-01  a ```python fence must not pass ``trust_remote_code=True`` to
        any loader. The flag tells the Hub-side loader to download the
        repository's own modeling/loading Python and execute it on the
        local machine at load time - the caller hands code execution to
        whatever the repo (or anything that later pushes to it)
        contains. Hugging Face's own guidance is to leave it at the
        default False and only enable it for repositories you trust,
        ideally pinned to a revision. The corpus's 10 sites never
        needed the flag at all: every one loads a stock-code
        checkpoint (Mistral-7B(-Instruct), meta-llama/Llama-2-7b-hf,
        TheBloke/Llama-2-7B-AWQ, a local GPTQ export, gpt2) whose
        modeling code ships inside transformers itself - and the same
        corpus loads the SAME models flag-free lines away
        (SOLUTION-LAB-003's AutoTokenizer, 4307's AutoTokenizer), so
        the flagged form was cargo-cult teaching the reader to
        reflexively enable remote code execution.

Out of the class by construction:

  - the kwarg absent - the default is False, the safe form the
    corpus's own flag-free loads teach.
  - ``trust_remote_code=False`` (or any non-True constant).
  - non-constant values (a Name/Call expression) - only the literal
    True constant enters, the sibling non-constant-mode rule.
  - kwarg names that merely contain the fragment (``allow_*`` family)
    - the walk demands the exact ``trust_remote_code`` keyword.
  - string mentions and prose never reach the walk (AST, not text).
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, any line) is deliberate
    danger-teaching, the sibling unsafe_*/interp/crypto escape.
  - notebooks (.ipynb) are outside the md universe.

Hard gate (exit 1 on findings): born census tick-657 read every call
kwarg in every md python fence fence-aware = exactly 10 findings, all
TRC-01, all on stock-code checkpoints across 8 files - drained the
same tick in-line (flag removed or the argument line swapped for a
one-line why-comment, zero line shift so every exec-census baseline
row in the 8 files keeps its coordinates), returning the class to
zero-drain hard from the rule's naming.

Run over the whole corpus:
    python scripts/qa/trust_remote_code_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")

DANGER_MARKER_RE = re.compile(r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)

FINDING = (": TRC-01 trust_remote_code=True hands code execution to the "
           "loaded repository at load time - leave the default False "
           "unless the checkpoint genuinely needs custom remote code "
           "(and pin a revision when it does)")


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
            for kw in node.keywords:
                if kw.arg == "trust_remote_code" \
                        and isinstance(kw.value, ast.Constant) \
                        and kw.value.value is True:
                    findings.append(f"{rel}:{base + node.lineno}{FINDING}")
            self.generic_visit(node)

    _Collector().visit(tree)


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    in_fence = False
    f_char = ""
    f_len = 0
    lang = ""
    start = 0
    fence_lines: list[tuple[int, str]] = []
    for ln, raw in enumerate(lines, 1):
        if FENCE_RE.match(raw):
            ch = FENCE_RE.match(raw).group(1)[0]
            n = len(FENCE_RE.match(raw).group(1))
            if in_fence:
                # CommonMark fence length (tick-680): only a same-character run at least as long closes
                if ch == f_char and n >= f_len:
                    if in_fence and lang == "python" and fence_lines:
                        _scan_fence(rel, start, fence_lines, findings)
                    in_fence = False
                    lang = ""
                    start = 0
                    fence_lines = []
                    continue
            else:
                in_fence = True
                f_char, f_len = ch, n
                lang = FENCE_RE.match(raw).group(2).lower()
                start = ln
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
    print(f"trust_remote_code_scan: {len(findings)} findings "
          f"(TRC-01 trust_remote_code=True) in {len(n_files)} files "
          f"across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
