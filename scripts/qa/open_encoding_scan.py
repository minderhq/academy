#!/usr/bin/env python3
"""Text-write-encoding gate for the Minder Academy corpus.

OE-01  a ```python fence must not open a file in *text write mode*
       (mode carrying any of ``w`` / ``a`` / ``x`` / ``+`` and no
       ``b``) without an explicit ``encoding=`` - ``open(path, 'w')``,
       ``open(path, 'a')``. A text-mode open without ``encoding``
       falls back to ``locale.getpreferredencoding(False)``: cp1252 or
       cp1254 on Windows, an ASCII-ish locale on many CI images - so
       non-ASCII content silently mojibakes or raises
       ``UnicodeEncodeError`` on exactly the platforms the reader did
       not test on. PEP 597 ships an ``EncodingWarning`` for the form;
       PEP 686 moves the default to UTF-8 only in 3.15.

OE-02  the same class one step removed: ``Path.write_text(data)``
       without ``encoding=`` - the convenience wrapper resolves the
       identical locale default.

The corpus itself vouches the class by teaching the affirmative form
in 24 places - ``encoding="utf-8"`` appears in LAB-006,
SOLUTION-LAB-010, 2306, 2401, 2402, 2403, 4408, 5302 and more - yet
the same corpus wrote 29 text-write opens without it (born census
below), every one a data artifact the reader is told to produce
(synthetic-data JSON, JSONL training sets, tokenizer stats, plugin
code, dashboards).

Out of the class by construction:

  - ``encoding=`` present (ANY value): the corpus also teaches
    ``encoding="latin-1"``-style foreign-charset reads/writes; the
    kwarg itself is the escape, not the value.
  - binary modes (``b`` anywhere in the mode - ``'wb'``, ``'rb+'``):
    ``encoding`` is a TypeError there; the born census counted 4 such
    opens (SOL-001, LAB-009 x2, PROJECT-004) and they stay silent.
  - read-only opens (no mode or ``'r'``): out of scope by design -
    the write side is where a wrong default *persists* corruption
    into the artifact the reader produces; a mismatched read only
    mangles display and is owned by the same cell only if a future
    tick grows the scope.
  - non-constant modes (``open(p, mode_var)`` / ``mode=var``):
    unresolvable - born census read 0.
  - ``Path.write_bytes``: binary by definition, no encoding param,
    a different attribute.
  - method ``.open()`` calls (``Image.open('photo.jpg')``): OE walks
    the builtin ``open`` Name-call and the exact ``write_text``
    attribute only; born census read 2 such method calls, both PIL,
    silent.
  - string mentions and prose never reach the walk: the check walks
    ast.Call nodes, not text.
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, on any line) is deliberate
    danger-teaching, the sibling unsafe_* gates' escape.
  - notebooks (.ipynb) are outside the md universe, the whole
    unsafe_*/fence family scans docs/**/*.md only.

Hard gate (exit 1 on findings): the born census read every open call
in every md python fence fence-aware = exactly 31 findings across 16
files (29 OE-01 + 2 OE-02, 0 danger-marked): ORGANIZATION-GUIDE's
SITEMAP writer, 2401's four ``open(out, 'w')`` tokenizer-stat writers,
LAB-003's four dataset writers, 5300-synthetic PRACTICE's six
synthetic-data writers, TUTORIAL-000's three, CHEAT-SHEET-002's two,
SOLUTION-LAB-001's ``self.file_path`` logger, 5104's sample_data.jsonl,
2302's cache_path, PROJECT-005's train/test writers, TUTORIAL-010's
report writer, the 1500-monitoring PRACTICE's dashboard writer, 2400's
and 2300-framework-engineering PRACTICE writers - all at true file lines (fence content line 1 = fence
open line + 1, the tick-645 lesson pre-applied) - plus OE-02's
2301-Framework-Design-Patterns ``write_text(args.to_json_string())``
and PROJECT-001's ``write_text(content)``. Drained the same tick to
the corpus-taught idiom: ``encoding="utf-8"`` added in-line at every
site (no line shifts, no census collateral).

Run over the whole corpus:
    python scripts/qa/open_encoding_scan.py --root .
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

WRITE_CHARS = set("wax+")


def _mode_of(call: ast.Call) -> str | None:
    """The mode string of a builtin ``open(...)`` call - positional
    args[1] or the ``mode=`` kwarg, constants only, else None."""
    if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant) \
            and isinstance(call.args[1].value, str):
        return call.args[1].value
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant) \
                and isinstance(kw.value.value, str):
            return kw.value.value
    return None


def _is_text_write(mode: str | None) -> bool:
    """A text write mode: carries w/a/x/+ and never b (binary takes
    no encoding at all)."""
    return mode is not None and "b" not in mode and WRITE_CHARS & set(mode)


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
        if not isinstance(node, ast.Call):
            continue
        # OE-01: builtin open() in text-write mode without encoding=
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            if _is_text_write(_mode_of(node)) \
                    and not any(kw.arg == "encoding" for kw in node.keywords):
                findings.append(
                    f"{rel}:{base + node.lineno}: OE-01 text write via "
                    f"`open()` with no encoding= - the mode defaults to "
                    f"locale.getpreferredencoding(False) (cp1252/cp1254 "
                    f"on Windows, an ASCII-ish locale on CI), so non-ASCII "
                    f"content silently mojibakes or raises "
                    f"UnicodeEncodeError (PEP 597 warns, PEP 686 fixes the "
                    f"default only in 3.15); pass encoding=\"utf-8\" - the "
                    f"idiom the corpus itself teaches in 24 places")
            continue
        # OE-02: Path.write_text() without encoding=
        if isinstance(node.func, ast.Attribute) and node.func.attr == "write_text":
            if not any(kw.arg == "encoding" for kw in node.keywords):
                findings.append(
                    f"{rel}:{base + node.lineno}: OE-02 text write via "
                    f"`Path.write_text()` with no encoding= - the wrapper "
                    f"resolves the same locale default as bare open() "
                    f"(cp1252/cp1254 on Windows); pass encoding=\"utf-8\" - "
                    f"the idiom the corpus itself teaches in 24 places")


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
    print(f"open_encoding_scan: {len(findings)} findings "
          f"(OE-01 open() text write without encoding, OE-02 "
          f"Path.write_text without encoding) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
