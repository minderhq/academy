#!/usr/bin/env python3
"""codeblock_syntax_scan - every ```python fence must parse as Python (CB-01).

Policy: a fence labeled python/py/python3 is a promise to the platform that
the block is real Python (a future platform will highlight, extract and run
these). This gate ast-parses every non-empty python-labeled fence corpus-wide
and fails on any block that does not parse. Non-Python content (prose,
dialogues, formulas, error output, config listings, shell commands) lives in
an honest fence label instead: ```text, ```bash, ```yaml, etc.

Fence-aware: tracks ``` and ~~~ openers/closers by CommonMark fence
length (a closer must repeat the opener's character in a run at least
as long; a different fence character never closes - nested 3-backtick
inner examples inside 4-backtick outer blocks stay fenced interior,
aligned tick-678 with render_hygiene_check's tick-677 fix), only
parses blocks opened with a python/py/python3 label, textwrap.dedents
indented blocks before parsing, skips empty blocks.

Output: one finding per failing block, then a summary line:
    codeblock_syntax_scan: N findings across docs/
Exit code: 0 if N == 0, else 1.
"""
import argparse
import ast
import re
import sys
import textwrap
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
PYTHON_LANGS = ("python", "py", "python3")


def scan_lines(root: Path):
    """ast-parse every python-labeled fence; return (findings, py_block_count)."""
    findings = []
    py_blocks = 0
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").split("\n")
        in_fence = False
        f_char = ""
        f_len = 0
        lang = ""
        start = 0
        body = []
        for i, raw in enumerate(lines):
            m = FENCE.match(raw)
            if m and not in_fence:
                run = m.group(1)
                in_fence = True
                f_char, f_len = run[0], len(run)
                lang = m.group(2).lower()
                start = i
                body = []
                continue
            if in_fence:
                if m:
                    run = m.group(1)
                    ch, n = run[0], len(run)
                    if ch == f_char and n >= f_len:
                        if lang in PYTHON_LANGS:
                            py_blocks += 1
                            src = textwrap.dedent("\n".join(body))
                            if src.strip():
                                try:
                                    ast.parse(src)
                                except SyntaxError as e:
                                    off = (
                                        src.splitlines()[e.lineno - 1].strip()
                                        if e.lineno else ""
                                    )
                                    findings.append(
                                        "%s:%d: CB-01 python fence does not parse: %s | %s"
                                        % (rel, start + 1, e.msg, off[:60])
                                    )
                        in_fence = False
                        body = []
                        continue
                # a marker line that is not a valid closer is fence content
                # (CommonMark: an inner 3-run inside a 4-run outer), keep it
                body.append(raw)
                continue
    return findings, py_blocks


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]),
                    help="repo root (default: two levels up)")
    args = ap.parse_args()
    root = Path(args.root)
    docs = root / "docs"
    findings, py_blocks = scan_lines(docs)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print("codeblock_syntax_scan: %d findings across docs/ (%d python blocks parsed)"
          % (len(findings), py_blocks))
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
