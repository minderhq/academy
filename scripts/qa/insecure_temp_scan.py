#!/usr/bin/env python3
"""Insecure-temp-file gate for the Minder Academy corpus.

TF-01  a ```python fence must not call ``tempfile.mktemp()`` - mktemp
       returns a name that does not exist yet: between the call and the
       file's creation another process can create the path first (a
       symlink pointing elsewhere, or a squatting file), so whatever
       the fence writes lands on attacker-chosen ground - the TOCTOU
       race class (Bandit B306). The affirmative forms create
       atomically: ``tempfile.mkstemp``/``NamedTemporaryFile`` open
       the fd at creation time, ``tempfile.TemporaryDirectory`` hands
       out a private directory. Both the module-attribute call
       (``tempfile.mktemp()``) and the bare-Name rebinding
       (``from tempfile import mktemp``) enter the walk.

TF-02  the same fence must not create a file or directory at a
       hardcoded shared temp path - a string constant starting with
       ``/tmp``, ``/var/tmp`` or ``/dev/shm`` passed directly to
       ``open``, ``os.open``, ``os.mkdir``, ``os.makedirs`` or
       ``os.mknod`` puts content at a predictable, world-writable
       location on multi-user hosts: another user can pre-create or
       overwrite it (Bandit B108's hardcoded-tmp-directory class,
       evaluated at the creation call). Only DIRECT string-constant
       arguments enter - composite literals (``tmpfs={"/tmp": ...}``)
       and non-argument contexts stay out.

Out of the class by construction:

  - the safe tempfile forms the corpus practices: ``mkdtemp`` x6
    (2401/2402/5302/PRACTICE x2/phase7-practice), ``NamedTemporaryFile``
    x7 (LAB-012, PROJECT-001, VOLUME-7, phase7-practice) and
    ``TemporaryDirectory`` (2403 imports it) - none is mktemp and none
    takes a tmp-prefixed creation argument.
  - explicit ``dir="/tmp"`` on tempfile APIs - mkstemp/mkdtemp create
    with private 0600/0700 permissions regardless of location, so the
    location is not the hazard there; the walk only enters on
    {open, os.open, os.mkdir, os.makedirs, os.mknod}.
  - ``tf.profiler.experimental.start('/tmp/xla_profile')``
    (2202:347, born-census-documented) - a profiling output path, not
    in the creation-call roster.
  - ``ALLOWED_PATHS = ["/tmp", ...]`` (phase7-practice:294) - a list
    literal in sandbox teaching, not a creation-call argument (the
    call-site-attachment lesson of the CH-01 census).
  - yaml volume mounts, shell commands and env assignments carrying
    /tmp paths (loki/tempo mounts, ``rm -rf /tmp``, CUDA_MPS_PIPE_
    DIRECTORY) - yaml/shell fences are outside the python-fence
    universe.
  - string mentions and prose never reach the walk (AST, not text).
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, any line) is deliberate
    danger-teaching, the sibling unsafe_*/interp/crypto gates' escape.
  - notebooks (.ipynb) are outside the md universe.

Hard gate (exit 1 on findings): born census tick-655 read every
tempfile call and every creation-call argument in every md python
fence fence-aware = 0 findings (0 mktemp of either spelling across
docs and scripts, 0 tmp-prefixed creation-call constants - the 14
raw /tmp mentions are all yaml/shell/docker contexts or non-argument
python forms) - the corpus never teaches the racy or the predictable
form, so the class froze at the rule the moment it was named:
zero-drain, hard from birth, owned preemptively per the US-02/US-03,
RT-02 and CH-01 precedent.

Run over the whole corpus:
    python scripts/qa/insecure_temp_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

DANGER_MARKER_RE = re.compile(r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)

# File/dir creation calls TF-02 evaluates at (bare Name or os.* attribute).
CREATE_VERBS = {"open", "mkdir", "makedirs", "mknod"}

# Predictable shared-temp path prefixes (Bandit B108's location family).
TMP_PREFIXES = ("/tmp", "/var/tmp", "/dev/shm")


def _tmp_constant(node: ast.expr) -> bool:
    return (isinstance(node, ast.Constant) and isinstance(node.value, str)
            and node.value.startswith(TMP_PREFIXES))


def _tf02_attached(call: ast.Call) -> bool:
    # DIRECT string-constant arguments only - composite literals stay out.
    for a in call.args:
        if _tmp_constant(a):
            return True
    for kw in call.keywords:
        if _tmp_constant(kw.value):
            return True
    return False


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
            if isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                base_node = node.func.value
                base_name = base_node.id if isinstance(base_node, ast.Name) \
                    else None
                if base_name == "tempfile" and attr == "mktemp":
                    findings.append(
                        f"{rel}:{base + node.lineno}: TF-01 "
                        f"tempfile.mktemp() - the name exists before the "
                        f"file does (TOCTOU race): another process can "
                        f"create the path first or squat it; create "
                        f"atomically with tempfile.mkstemp/"
                        f"NamedTemporaryFile or tempfile.TemporaryDirectory")
                elif base_name == "os" and attr in CREATE_VERBS \
                        and _tf02_attached(node):
                    findings.append(
                        f"{rel}:{base + node.lineno}: TF-02 file/dir "
                        f"created at a hardcoded shared temp path - "
                        f"/tmp, /var/tmp and /dev/shm are predictable and "
                        f"world-writable on multi-user hosts; use "
                        f"tempfile.TemporaryDirectory/mkstemp which pick "
                        f"a private name")
            elif isinstance(node.func, ast.Name):
                name = node.func.id
                if name == "mktemp":
                    findings.append(
                        f"{rel}:{base + node.lineno}: TF-01 mktemp() - "
                        f"the name exists before the file does (TOCTOU "
                        f"race): another process can create the path "
                        f"first or squat it; create atomically with "
                        f"tempfile.mkstemp/NamedTemporaryFile or "
                        f"tempfile.TemporaryDirectory")
                elif name in CREATE_VERBS and _tf02_attached(node):
                    findings.append(
                        f"{rel}:{base + node.lineno}: TF-02 file/dir "
                        f"created at a hardcoded shared temp path - "
                        f"/tmp, /var/tmp and /dev/shm are predictable and "
                        f"world-writable on multi-user hosts; use "
                        f"tempfile.TemporaryDirectory/mkstemp which pick "
                        f"a private name")
            self.generic_visit(node)

    _Collector().visit(tree)


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
    print(f"insecure_temp_scan: {len(findings)} findings "
          f"(TF-01 racy tempfile.mktemp, TF-02 hardcoded shared-temp "
          f"creation path) in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
