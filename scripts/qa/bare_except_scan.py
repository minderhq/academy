#!/usr/bin/env python3
"""bare-except gate for the Minder Academy corpus.

BX-01  a ```python fence must not teach a bare ``except:`` with a real
       body: a handler
       with no exception type catches ``BaseException`` - not just the
       error the try block guards against, but ``KeyboardInterrupt``
       (the user's Ctrl+C is swallowed and the loop keeps going),
       ``SystemExit`` (shutdown requests eaten mid-flight), and
       ``asyncio.CancelledError`` (task cancellation silently no-ops -
       the async family of AB-01/UC-01). PEP 8 names it directly:
       "too broad" - the handler fires on exceptions the author never
       anticipated, hiding real bugs behind a default response.

       The affirmative forms are taught by the corpus itself: the
       bounded broad form ``except Exception`` (124 handlers) and the
       specific type forms ``except json.JSONDecodeError:`` /
       ``except (ValueError, KeyError):`` (65 handlers) - 189 of the
       corpus's 206 handlers already teach the bounded forms; the 17
       bare handlers are stragglers. The corpus even shows both forms
       side by side: 7500-security PRACTICE parses log timestamps with
       a bare ``except:`` directly above a sibling
       ``except json.JSONDecodeError:`` on the same JSON records.

Out of the class by construction:

  - ``except Exception:`` / ``except Exception as e:`` - the taught
    bounded broad form; BaseException-only classes
    (KeyboardInterrupt / SystemExit / GeneratorExit /
    asyncio.CancelledError) still propagate.
  - every specific-type handler - ``except Name:``,
    ``except module.Attr:``, ``except (A, B):``, any non-None type
    node (Name / Attribute / Tuple / Subscript / Call) - the walk
    fires only when ``handler.type is None``.
  - ``except* Type:`` (ExceptionGroups, py3.11) - the grammar demands
    a type there, so it cannot be bare; its handlers are ordinary
    ExceptHandler nodes with a type and stay silent.
  - string mentions and prose never reach the walk (AST, not text).
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, any line) is deliberate
    danger-teaching, the sibling unsafe_*/interp/crypto escape.
  - non-python fences (yaml / shell / dockerfile) are outside the
    python universe.
  - fences that do not parse (SyntaxError) are silently skipped, the
    sibling-gate convention; codeblock_syntax_scan owns fence
    compilability.
  - notebooks (.ipynb) are outside the md universe.
  - a pass-only body (the suite is exactly one ``ast.Pass``) is the
    pure-swallow slice - broad_except_scan BE-01 owns it (bare or
    broad-typed handler plus pass-only body, the silent-swallow
    class), this gate owns every other type-is-None handler -
    disjoint by body shape; none of the 17 drained handlers was
    pass-only (broad_except read 0 through the drain), so the
    partition moved no census number.

Hard gate (exit 1 on findings): born census tick-660 read every
except handler in every md python fence fence-aware = exactly 17 bare
handlers, all BX-01, across 12 files - drained the same tick in-line
(``except:`` -> ``except Exception:``, one line per site, zero line
shift, so every exec-census baseline row keeps its coordinates and the
runtime behavior of the guards is unchanged for every Exception
subclass the guards actually see), returning the class to zero-drain.

Run over the whole corpus:
    python scripts/qa/bare_except_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

DANGER_MARKER_RE = re.compile(r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)

FINDING = (" bare except: catches BaseException - KeyboardInterrupt, "
           "SystemExit and asyncio.CancelledError are swallowed "
           "(Ctrl+C dies silently, cancellation no-ops) - name the "
           "type, or catch Exception for the bounded broad form")


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

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                continue  # pass-only slice: broad_except_scan BE-01
            findings.append(f"{rel}:{base + node.lineno}: BX-01{FINDING}")


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
    print(f"bare_except_scan: {len(findings)} findings "
          f"(BX-01 bare except handlers with real (non-pass) bodies) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
