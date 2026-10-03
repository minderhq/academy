#!/usr/bin/env python3
"""unsafe shell-execution gate for the PROJECT-OMEGA corpus.

US-01  a ```python fence must not call subprocess.run / call /
       check_call / check_output / Popen with ``shell=True``. A
       shell=True call hands the command string to /bin/sh: any
       metacharacter in an interpolated value (;, $(), backticks, &&)
       breaks out of the intended command, so allowlists and blocklists
       built for the program name are defeated by the shell - PROJECT-001
       validated cmd_parts[0] against an allowlist and then executed the
       raw string through the shell it never inspected. The corpus
       vouches the class itself: 7500-security's scanner lists
       ``r"subprocess\\."`` among its dangerous patterns and its rule
       table says "subprocess": "Process creation"; 7202-code-interpreter
       teaches the affirmative safe form -
       ``subprocess.run([sys.executable, "-I", "-c", code], ...)`` -
       the list form that never reaches a shell.

US-02  a ```python fence must not call ``os.system`` or
       ``os.popen`` (popen2/popen3/popen4 siblings included). Born at
       zero: the corpus never teaches them as the go-to, and 7500-security's
       own scanner regexes name ``r"os\\.system"`` and ``r"os\\.popen"``
       as dangerous patterns. The cell is owned preemptively per the
       QI-18 precedent.

US-03  a ```python fence must not call ``subprocess.getoutput`` or
       ``subprocess.getstatusoutput`` - both are shell=True by
       construction under a convenience name. Born at zero; the cell is
       owned preemptively.

Out of the class by construction:

  - the list form: ``subprocess.run(["ls", "-l"])`` carries no shell
    kwarg - the 7202-taught idiom, never a shell string.
  - ``shell=False`` and any non-constant ``shell=`` value: only the
    literal True enters the class (False is the explicit no-shell
    contract, a non-literal is unresolvable, neither teaches the
    shell idiom).
  - os.exec* / os.spawn* replace or fork a process image without a
    shell - not the class.
  - .system() / .run(shell=True) on other bases (a runner, a session)
    are Attribute chains whose value is not the os/subprocess Name.
  - comment-only mentions and prose never reach the walk: the check
    walks ast.Call nodes, not text.
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, on any line) is deliberate
    danger-teaching, the sibling unsafe_deserialize_scan's escape
    (born census: phase7-practice's execute_bash fence shows the
    blocklist-guarded shell call and is marked by its own
    "# Dangerous commands to block" comment).

Hard gate (exit 1 on findings): the born census read 24088 python-fence
calls fence-aware = 2 findings, both US-01 (PROJECT-001's
execute_shell_command tool executor, 1200-virtualization PRACTICE's
GPU-passthrough diagnostics helper); US-02 and US-03 born-at-zero.

Run over the whole corpus:
    python scripts/qa/unsafe_shell_scan.py --root .
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

# subprocess entry points that accept the shell kwarg
SHELL_KWARG_ATTRS = {"run", "call", "check_call", "check_output", "Popen"}

# subprocess entry points that are shell=True under a convenience name
IMPLICIT_SHELL_ATTRS = {"getoutput", "getstatusoutput"}

# os entry points that route through /bin/sh
OS_SHELL_ATTRS = {"system", "popen", "popen2", "popen3", "popen4"}


def _is_true_shell(node: ast.Call) -> bool:
    return any(
        k.arg == "shell"
        and isinstance(k.value, ast.Constant)
        and k.value.value is True
        for k in node.keywords
    )


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


def _scan_fence(rel: str, start: int, fence_lines: list[tuple[int, str]],
                findings: list[str]) -> None:
    src = "\n".join(raw for _, raw in fence_lines)
    if DANGER_MARKER_RE.search(src):
        return
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    base = start  # fence content line 1 == fence-open line + 1 (tick-645 lesson)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        val = node.func.value
        if not isinstance(val, ast.Name):
            continue
        mod = val.id
        attr = node.func.attr
        if mod == "subprocess" and attr in SHELL_KWARG_ATTRS and _is_true_shell(node):
            findings.append(
                f"{rel}:{base + node.lineno}: US-01 subprocess.{attr}()"
                f"(shell=True) - the command string goes to /bin/sh, so "
                f"metacharacters in interpolated values break out of any "
                f"name-level allowlist/blocklist; pass the argv list "
                f"(7202's [sys.executable, \"-I\", \"-c\", code] form) "
                f"without shell")
        elif mod == "subprocess" and attr in IMPLICIT_SHELL_ATTRS:
            findings.append(
                f"{rel}:{base + node.lineno}: US-03 subprocess.{attr}() - "
                f"shell=True by construction under a convenience name; "
                f"use subprocess.run(argv_list, capture_output=True, "
                f"text=True) without shell")
        elif mod == "os" and attr in OS_SHELL_ATTRS:
            findings.append(
                f"{rel}:{base + node.lineno}: US-02 os.{attr}() - the "
                f"string goes to /bin/sh (7500-security's own scanner "
                f"regexes name os\\.system/os\\.popen as dangerous); use "
                f"subprocess.run(argv_list, ...) without shell")


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
    print(f"unsafe_shell_scan: {len(findings)} findings "
          f"(US-01 subprocess shell=True, US-02 os.system/os.popen, "
          f"US-03 subprocess.getoutput/getstatusoutput) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
