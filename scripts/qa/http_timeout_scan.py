#!/usr/bin/env python3
"""HTTP-timeout gate for the Minder Academy corpus.

RT-01  a ``requests.<verb>(...)`` call (get / post / put / delete /
       patch / head / options / request) without a ``timeout=`` kwarg.
       ``requests`` sets NO default timeout - the underlying socket
       read blocks indefinitely, so one dead or slow peer hangs the
       caller forever: a monitor loop that stops monitoring, a web
       worker that never returns, a batch job stuck mid-flight
       accumulating hung threads. The requests project's own docs
       carry the warning ("Most requests to external servers should
       have a timeout") and Python's socket default is ``None`` -
       silence is not a policy, it is an unbounded wait.

RT-02  the same call carrying ``verify=False`` - TLS certificate
       verification disabled, the MITM door opened. Born-at-zero
       (the corpus never writes the form), owned preemptively per
       the US-02/US-03 precedent.

The corpus itself vouches the class by teaching the kwarg in 30+
places - ``timeout=5`` health pings (LAB-001:151, phase1-practice
:259), ``timeout=120`` LLM-inference calls (SOL-LAB-001, LAB-001,
LAB-002, LAB-003), ``timeout=30`` general API calls (LAB-013:855),
``timeout=self.timeout`` on the Session form (LAB-013), ``timeout=
60`` (PROJECT-001) - yet the same corpus signed 42 bare calls, in
one case the vouched 5-second form and the bare form of the very
same endpoint 9 lines apart (LAB-001 /api/tags at 151 vs 160). The
born census read every requests call in every md python fence
fence-aware = exactly 42 findings across 15 files, all RT-01, 0
danger-marked, 0 RT-02. Drained the same tick to the corpus's own
three-value idiom by call class: 120 on the twenty LLM-inference
sites, 5 on the five status/ping sites, 30 on the seventeen general
API sites.

Out of the class by construction:

  - ``timeout=`` present (ANY value): the kwarg itself is the
    contract, the encoding= rule of the sibling open_encoding gate.
  - httpx calls: the corpus's single httpx site carries a
    client-level ``timeout=300.0`` (TUTORIAL-012), and httpx
    defaults every request to 5-second timeouts - the asymmetry
    with requests' None is exactly the lesson; no httpx finding to
    own.
  - Session-form calls (``s.get(url)`` on a ``requests.Session()``):
    the corpus's single Session site (LAB-013) carries
    ``timeout=self.timeout`` at both call sites; walking session
    variables is a one-hop resolution the born census never needed.
    Out of scope by construction, not by blindness - the census
    read every ``.get/.post``-shaped call and the only session
    variable was that one.
  - ``from requests import get`` rebindings: born census read zero
    (the corpus imports the module form in all 41 requests files).
  - other-object ``.get``/``.post`` calls (``dict.get``,
    ``cache.get``, agent ``executor.execute``): the walk demands a
    bare ``requests`` Name base, not an Attribute chain.
  - string mentions and prose never reach the walk: the check walks
    ast.Call nodes, not text.
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, on any line) is deliberate
    danger-teaching, the sibling unsafe_* gates' escape.
  - notebooks (.ipynb) are outside the md universe, the whole
    unsafe_*/fence family scans docs/**/*.md only.

Hard gate (exit 1 on findings).

Run over the whole corpus:
    python scripts/qa/http_timeout_scan.py --root .
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

VERBS = {"get", "post", "put", "delete", "patch", "head", "options",
         "request"}


def _is_requests_verb(func: ast.expr) -> bool:
    return (isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "requests"
            and func.attr in VERBS)


def _scan_fence(rel: str, start: int, fence_lines: list[str],
                findings: list[str]) -> None:
    src = "\n".join(fence_lines)
    if DANGER_MARKER_RE.search(src):
        return
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    base = start  # fence content line 1 == fence-open line + 1 (tick-645 lesson)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_requests_verb(node.func):
            continue
        has_timeout = any(kw.arg == "timeout" for kw in node.keywords)
        verify_false = any(kw.arg == "verify"
                           and isinstance(kw.value, ast.Constant)
                           and kw.value.value is False
                           for kw in node.keywords)
        verb = node.func.attr
        if verify_false:
            findings.append(
                f"{rel}:{base + node.lineno}: RT-02 requests.{verb}() with "
                f"verify=False - TLS certificate verification disabled, the "
                f"MITM door opened; drop the kwarg (or point --verify at a "
                f"real CA bundle for self-signed lab servers)")
        if not has_timeout:
            findings.append(
                f"{rel}:{base + node.lineno}: RT-01 requests.{verb}() with "
                f"no timeout= - requests sets NO default timeout, the "
                f"socket read blocks indefinitely and one dead or slow "
                f"peer hangs the caller forever; pass timeout= (the "
                f"corpus idiom: 5 for status pings, 120 for LLM "
                f"inference, 30 for general API calls)")


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
            fence_lines.append(raw)
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
    print(f"http_timeout_scan: {len(findings)} findings "
          f"(RT-01 requests call without timeout, RT-02 verify=False) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
