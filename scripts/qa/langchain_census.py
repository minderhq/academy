#!/usr/bin/env python3
"""langchain import-resolution gate for the PROJECT-OMEGA curriculum.

Every langchain/langchain_*/langgraph import line inside a ```python fence
is resolved against the installed stack (importlib.import_module + getattr
for from-imports) - the same runtime-verified census that drove the
langchain-modernization epic. A finding means the fenced example raises
ImportError/AttributeError as written, i.e. the lesson teaches code that
cannot run.

LC-01  import line does not resolve (module missing or name absent)

Notes from the modernization epic (documented blind spots, out of gate
scope): the census cannot see import-less usage of removed APIs (UC-003
latent NameErrors) or missing stdlib imports (7401 missing datetime), and
dead imports inflate its findings (SOLUTION-LAB-005). Review flagging
always includes reading the surrounding fence.

Exit 0 when zero findings; exit 1 otherwise. Run over the whole corpus:
    python scripts/qa/langchain_census.py --root .
"""
from __future__ import annotations

import argparse
import importlib
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")
LC_RE = re.compile(r"\blangchain\b|\blangchain_\w+|\blanggraph\b")
IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import\s+(.+)"
    r"|(?:import)\s+([\w.]+(?:\s*,\s*[\w.]+)*))\s*$")

for _pkg in ("langchain", "langgraph"):
    try:
        importlib.import_module(_pkg)
    except ImportError:  # environment problem, not a doc problem
        print(f"langchain_census: {_pkg} not importable in this interpreter - "
              "the census resolves lesson imports against the kurulu-stack; "
              "run the scorecard with that python (see ENVIRONMENT-SETUP.md)")
        sys.exit(2)

_verdict_cache: dict[str, str] = {}


def resolve(stmt: str) -> str:
    """'OK' or 'ErrorType: message' for a normalized import statement."""
    if stmt in _verdict_cache:
        return _verdict_cache[stmt]
    try:
        if stmt.startswith("from "):
            mod, names = stmt[5:].split(" import ", 1)
            module = importlib.import_module(mod.strip())
            for name in names.split(","):
                name = name.strip()
                if not name or name == "(":
                    continue
                name = name.split(" as ")[0].strip().rstrip(")")
                if name and name != "(":
                    getattr(module, name)
        else:
            for mod in stmt[len("import "):].split(","):
                importlib.import_module(mod.strip())
        verdict = "OK"
    except Exception as e:  # noqa: BLE001 - any failure means "cannot run"
        verdict = type(e).__name__ + ": " + str(e).split("\n")[0][:90]
    _verdict_cache[stmt] = verdict
    return verdict


def lint_file(root: Path, path: Path, findings: list[str], total: list[int]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")
    in_fence = False
    lang = ""
    for i, raw in enumerate(lines):
        m = FENCE_RE.match(raw)
        if m:
            in_fence = not in_fence
            lang = "" if not in_fence else m.group(2).lower()
            continue
        if lang != "python" or not LC_RE.search(raw):
            continue
        im = IMPORT_RE.match(raw)
        if not im:
            continue
        if im.group(1):  # from X import Y
            stmt = "from %s import %s" % (im.group(1), im.group(2).strip().rstrip(","))
            stmt = re.sub(r"\s+", " ", stmt)
        else:  # import X, Y
            stmt = "import " + re.sub(r"\s+", " ", im.group(3))
        total[0] += 1
        verdict = resolve(stmt)
        if verdict != "OK":
            findings.append(
                f"{rel}:{i + 1}: LC-01 langchain import fails at runtime "
                f"[{verdict}] - {stmt}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    total = [0]
    for path in sorted(docs.rglob("*.md")):
        try:
            lint_file(args.root, path, findings, total)
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    n_files = len({f.split(":", 1)[0] for f in findings})
    print(f"langchain_census: {len(findings)} broken imports in {n_files} files "
          f"across docs/ ({total[0]} langchain imports checked)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
