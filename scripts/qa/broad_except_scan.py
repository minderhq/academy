#!/usr/bin/env python3
"""bare/broad except pure-swallow gate for the PROJECT-OMEGA corpus.

BE-01  a ```python fence must not carry a bare ``except:`` whose body is
       only ``pass``. A bare except catches KeyboardInterrupt, SystemExit
       and GeneratorExit alongside every programming error, and a
       pass-only body discards all of them silently - the reader ships
       an agent whose Ctrl-C looks like a no-op. The corpus vouches the
       class itself: 6304-GraphRAG's own comment teaches "a bare except
       would also swallow KeyboardInterrupt and NameError silently",
       LAB-004 marks the swallowed-output path, and the affirmative
       narrow forms are taught corpus-wide (6304's
       ``except (json.JSONDecodeError, ValueError):`` tuple, the
       json.JSONDecodeError narrows at LAB-013/LAB-014/7500-PRACTICE/
       6200-PRACTICE, LAB-012's ``except KeyboardInterrupt:``).

BE-02  a ```python fence must not carry ``except Exception:`` (or
       ``except BaseException:`` - tuple members included) whose body
       is only ``pass``. The broad type names every error on purpose
       and the pass-only body keeps none of it: the same silent-swallow
       as BE-01 one level down the MRO.

Out of the class by construction:

  - a narrow named exception with a pass-only body is the corpus-taught
    idempotent/expected case (``except ValueError: pass``,
    ``except json.JSONDecodeError: pass``, the 6304 tuple form) - the
    handler names what it forgives.
  - a bare or broad handler whose body does anything besides ``pass``
    (log, re-raise, recover, record) is out - the walk demands the
    suite be exactly one ast.Pass; comments are not AST nodes, so a
    comment next to pass does not rescue a swallow.
  - the handler ``as e`` name binding is irrelevant to the class.
  - comment-only mentions and prose never reach the walk: the check
    walks ast.ExceptHandler nodes, not text.
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, on any line) is deliberate
    danger-teaching, the sibling unsafe_* gates' escape.
  - notebooks (.ipynb) are outside the md universe, the whole
    unsafe_*/fence family scans docs/**/*.md only.

Hard gate (exit 1 on findings): the born census read the python-fence
except handlers fence-aware = 5 findings across 5 files (4 BE-01:
VOLUME-7-Production-Mastery's GPU power probe, LAB-007-Production-RAG's
collection bootstrap, 7200-PRACTICE's tool-selector JSON parse, 7103's
qdrant memory bootstrap; 1 BE-02: 6103-HNSW's delete-before-create
teardown). Drained the same tick to the narrow forms the corpus itself
teaches.

Run over the whole corpus:
    python scripts/qa/broad_except_scan.py --root .
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

BROAD_NAMES = {"Exception", "BaseException"}


def _is_broad_type(type_node: ast.expr | None) -> bool:
    """True for Exception / BaseException / builtins.Exception /
    builtins.BaseException / any tuple containing one."""
    if type_node is None:
        return False
    if isinstance(type_node, ast.Name):
        return type_node.id in BROAD_NAMES
    if isinstance(type_node, ast.Attribute):
        return (isinstance(type_node.value, ast.Name)
                and type_node.value.id == "builtins"
                and type_node.attr in BROAD_NAMES)
    if isinstance(type_node, ast.Tuple):
        return any(_is_broad_type(elt) for elt in type_node.elts)
    return False


def _is_pure_swallow(node: ast.ExceptHandler) -> bool:
    return len(node.body) == 1 and isinstance(node.body[0], ast.Pass)


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
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not _is_pure_swallow(node):
            continue
        if node.type is None:
            findings.append(
                f"{rel}:{base + node.lineno}: BE-01 bare except with a "
                f"pass-only body - a bare except catches KeyboardInterrupt, "
                f"SystemExit and GeneratorExit too, and pass discards all of "
                f"them silently (6304's own comment teaches this); narrow to "
                f"the exception you actually forgive")
        elif _is_broad_type(node.type):
            findings.append(
                f"{rel}:{base + node.lineno}: BE-02 broad except with a "
                f"pass-only body - Exception/BaseException names every error "
                f"on purpose and pass keeps none of it; narrow to the "
                f"exception you actually forgive (the corpus-taught "
                f"except (json.JSONDecodeError, ValueError) tuple form)")


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
    print(f"broad_except_scan: {len(findings)} findings "
          f"(BE-01 bare except pure-swallow, BE-02 Exception/BaseException "
          f"pure-swallow) in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
