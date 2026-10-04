#!/usr/bin/env python3
"""unsafe deserialization gate for the Minder Academy corpus.

UD-01  a ```python fence must not call ``torch.load()`` without an
       explicit ``weights_only`` keyword. A checkpoint file IS a pickle
       payload: unpickling executes embedded ``__reduce__`` bytecode,
       so a malicious ``.pt`` is arbitrary code execution. torch >= 2.6
       flipped the default to ``weights_only=True`` and the corpus
       itself teaches the explicit form (2300-framework-engineering
       PRACTICE + PREREQUISITES: "weights_only=True is the torch >= 2.6
       default; passing it explicitly") - while 10 corpus sites taught
       the bare pre-2.6 form. state_dicts and plain-container
       checkpoints load fine under weights_only=True.

UD-02  a ```python fence must not call ``pickle.load``/``loads`` (or
       the cPickle/dill/cloudpickle/marshal/joblib siblings, or
       ``shelve.open``). The corpus's own security chapter vouches the
       class: 7500-security's scanner lists the serialization regex
       ``pickle\\.loads?`` / ``marshal\\.loads?`` / ``shelve\\.`` and its
       rule table says "pickle": "Serialization (can execute code)" -
       while a serving-cache fence taught pickle.load as the go-to
       response-cache idiom. JSON (json.load/json.dump) is the safe
       cache idiom the corpus already imports in the same fence.

UD-03  a ```python fence must not call ``yaml.load()`` without an
       explicit ``Loader=`` keyword - the default constructor resolves
       arbitrary python objects (the classic yaml RCE). Born at zero:
       the corpus already teaches yaml.safe_load / SafeLoader
       everywhere; the cell is owned preemptively.

Out of the class by construction:

  - kwarg presence: ``torch.load(p, weights_only=True)`` and
    ``yaml.load(x, Loader=yaml.SafeLoader)`` carry the guard - any
    value is accepted (2200-frameworks PRACTICE teaches
    weights_only=False WITH an explanation of the 2.6 default; the
    explanation is the teaching, the kwarg is the escape).
  - write-side calls (torch.save, pickle.dumps/dump) never construct
    the read.
  - json.load / json.dump are the safe family - the drain target.
  - .load() method calls on other bases (a loader, a model) are
    Attribute chains the family test never matches.
  - comment-only mentions and prose never reach the walk: the check
    walks ast.Call nodes, not text.
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, on any line) is deliberate
    danger-teaching, the sibling unsafe_exec_scan's escape.

Hard gate (exit 1 on findings): the born census read 1861 python
fences = 10 bare torch.load sites across 7 files (UD-01), 1 pickle.load
cache site (UD-02, drained to JSON same tick), and 0 Loader-less
yaml.load (UD-03, born-at-zero). All 10 torch sites load state_dicts
or plain-container checkpoints - verified weights_only=True-compatible
before the drain (2301's config is dict[str, Any], 2402:258 saves a
pure state_dict).

Run over the whole corpus:
    python scripts/qa/unsafe_deserialize_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")

# A fence whose lines carry any of these is deliberate danger-teaching:
# the vulnerable form shown to be avoided, not craft to copy.
DANGER_MARKER_RE = re.compile(r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)

# module base -> attribute names that unpickle / execute on read
UNSAFE_LOADS: dict[str, set[str]] = {
    "pickle": {"load", "loads"},
    "cPickle": {"load", "loads"},
    "dill": {"load", "loads"},
    "cloudpickle": {"loads"},
    "marshal": {"load", "loads"},
    "joblib": {"load"},
    "shelve": {"open"},
}


def _has_kwarg(node: ast.Call, name: str) -> bool:
    return any(k.arg == name for k in node.keywords)


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
        if mod == "torch" and attr == "load" and not _has_kwarg(node, "weights_only"):
            findings.append(
                f"{rel}:{base + node.lineno}: UD-01 torch.load() without "
                f"weights_only - a checkpoint is a pickle payload and "
                f"torch >= 2.6 defaults weights_only=True; pass it "
                f"explicitly (state_dicts and plain-container checkpoints "
                f"load fine)")
        elif mod == "yaml" and attr == "load" and not _has_kwarg(node, "Loader"):
            findings.append(
                f"{rel}:{base + node.lineno}: UD-03 yaml.load() without "
                f"Loader= - the default constructor resolves arbitrary "
                f"python objects (yaml RCE); use yaml.safe_load() or "
                f"Loader=yaml.SafeLoader")
        elif attr in UNSAFE_LOADS.get(mod, ()):
            findings.append(
                f"{rel}:{base + node.lineno}: UD-02 {mod}.{attr}() - "
                f"unpickling executes embedded __reduce__ payloads "
                f"(7500-security lists serialization as can-execute-code); "
                f"cache as JSON or use a typed serializer")


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
    print(f"unsafe_deserialize_scan: {len(findings)} findings "
          f"(UD-01 torch.load without weights_only, UD-02 unsafe "
          f"pickle-family loads, UD-03 yaml.load without Loader) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
