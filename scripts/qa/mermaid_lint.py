#!/usr/bin/env python3
"""mermaid-lint gate for the Minder Academy corpus.

MM-01  a ```` ```mermaid ```` fence must open with a known diagram-type
       keyword. A typo'd header (``graf TD``) makes the renderer emit an
       error box instead of a diagram.
MM-02  the block's ``()``, ``[]``, ``{}`` must be balanced. Mermaid node
       syntax is bracket-delimited (``A[label]``, ``A(text)``, ``A{test}``);
       an unescaped stray bracket aborts the whole diagram render.
MM-03  ``graph``/``flowchart`` blocks must declare a direction
       (``TD|TB|LR|RL|BT``). A bare ``graph`` is a mermaid syntax error,
       not a default.
MM-04  a ``%`` outside double quotes aborts the diagram with a lexer
       "Lexical error ... Unrecognized text" - % is the mermaid comment
       token. Every label or edge label carrying a % sign must be
       double-quoted. dateFormat/axisFormat directives are exempt
       (strptime patterns, parsed fine unquoted).

The corpus carries 56 mermaid diagrams (docs/diagrams/ plus lesson
embeds) that a training platform renders directly - these checks hold
the render line without shipping a full mermaid parser. Verified
baseline 0 in tick-226 (51 graph, 3 stateDiagram-v2, 2 sequenceDiagram,
all headers, directions and brackets clean). MM-04 added in tick-337
after a user-facing render abort on three ML-LIFECYCLE diagrams
(7 unquoted % instances, now quoted).

Hard gate (exit 1 on findings): baseline 0.

Run over the whole corpus:
    python scripts/qa/mermaid_lint.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")

DIAGRAM_HEADERS = {
    "flowchart", "graph", "sequenceDiagram", "classDiagram",
    "stateDiagram", "stateDiagram-v2", "erDiagram", "gantt", "pie",
    "mindmap", "timeline", "journey", "gitGraph", "quadrantChart",
    "requirementDiagram", "C4Context", "C4Container", "C4Component",
    "C4Dynamic", "C4Deployment", "sankey-beta", "xychart-beta", "block-beta",
}
DIRECTIONS = {"TD", "TB", "LR", "RL", "BT"}


def scan_block(rel: str, start: int, chunk: list[str], findings: list[str]) -> None:
    # mermaid directives and %% comment lines are not diagram content
    code = [l for l in chunk if not l.strip().startswith("%%")]
    first = next((l.strip() for l in code if l.strip()), "")
    toks = first.split()
    kw = toks[0] if toks else ""
    if kw not in DIAGRAM_HEADERS:
        findings.append(
            f"{rel}:{start + 1}: MM-01 unknown mermaid diagram type "
            f"{kw!r} - expected one of the standard headers "
            f"(flowchart, sequenceDiagram, ...)")
        return
    if kw in ("graph", "flowchart") and (len(toks) < 2 or toks[1] not in DIRECTIONS):
        findings.append(
            f"{rel}:{start + 1}: MM-03 {kw} block without a direction - "
            f"declare TD, TB, LR, RL or BT on the header line")
    body = "\n".join(code)
    for a, b in (("(", ")"), ("[", "]"), ("{", "}")):
        if body.count(a) != body.count(b):
            findings.append(
                f"{rel}:{start + 1}: MM-02 unbalanced {a}{b} in mermaid "
                f"block - {body.count(a)} {a} vs {body.count(b)} {b}")
    for i, l in enumerate(chunk, 1):
        if l.strip().startswith("%%"):
            continue
        if re.match(r"\s*(dateFormat|axisFormat)\b", l):
            continue
        if "%" in re.sub(r'"[^"]*"', "", l):
            findings.append(
                f"{rel}:{start + i}: MM-04 unquoted '%' in mermaid block "
                f"- % is the renderer's comment token, the lexer aborts "
                f"the diagram (double-quote the label)")
            break


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    in_fence = False
    f_char = ""
    f_len = 0
    lang = ""
    start = 0
    chunk: list[str] = []
    for ln, raw in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if FENCE_RE.match(raw):
            ch = FENCE_RE.match(raw).group(1)[0]
            n = len(FENCE_RE.match(raw).group(1))
            if in_fence:
                # CommonMark fence length (tick-680): only a same-character run at least as long closes
                if ch == f_char and n >= f_len:
                    if in_fence and lang == "mermaid":
                        scan_block(rel, start, chunk, findings)
                    in_fence = False
                    lang = ""
                    start = 0
                    chunk = []
                    continue
            else:
                in_fence = True
                f_char, f_len = ch, n
                lang = FENCE_RE.match(raw).group(2).lower()
                start = ln
                chunk = []
                continue
        if in_fence and lang == "mermaid":
            chunk.append(raw)
    if in_fence and lang == "mermaid":
        scan_block(rel, start, chunk, findings)


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
    print(f"mermaid_lint: {len(findings)} findings "
          f"(MM-01 header / MM-02 brackets / MM-03 direction / "
          f"MM-04 unquoted %) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
