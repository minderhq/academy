#!/usr/bin/env python3
"""Plain-pip gate (UV-01) for the PROJECT-OMEGA corpus.

The 2026 curriculum standard is uv (10-100x faster installs, lockfile
workflow, built-in venv management) - the uv modernization epic
converted the docs, and this gate keeps it that way: a plain pip
install (pip / pip3 / python -m pip, any indentation) inside a
bash/sh/shell/dockerfile fence is reported. Lines using the uv
interface (uv pip install, uv sync, ...) are the standard and are
never reported.

UV-01  a plain 'pip install' that bypasses the uv standard.

Birth history (tick-337): census over 408 docs found 715 non-empty
fences in the four labels; 145 pip-family lines of which 115 already
use the uv interface - the remaining 30 all triaged into five
reasoned (rel, exact-line) accept classes below, zero drained, so
the gate locked at baseline 0. Accepts are keyed by exact stripped
line: editing an accepted line (or its indentation) produces a new
finding that gets re-triaged, which is the point. The container
class (most Dockerfiles RUN plain pip while LAB-001 already used
`RUN uv pip install --system`) drained in tick-338: every Dockerfile
in the corpus now follows LAB-001's official uv image pattern
(uv binary copied from the uv image, then `RUN uv pip install
--system --no-cache`), the ENVIRONMENT-SETUP exception note dropped
Dockerfiles, and the class was removed. The only plain pip left in
the container layer is TUTORIAL-002's deliberately bad Dockerfile,
accepted as the antiexample class.

Out of scope: pip list/freeze/show (read-only), uv argument health,
Python version pins. Lexical only - no package manager is invoked.

Run over the whole corpus:
    python scripts/qa/uv_install_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^```(\w*)\s*$")
LABELS = {"bash", "sh", "shell", "dockerfile"}

# plain pip install; (?<!uv ) keeps the uv interface out
PIP_INSTALL = re.compile(r"(?<!uv )\bpip3?\s+install\b")

_FALLBACK = ("documented pip fallback: shown as the explicit non-uv "
             "alternative")
_CONDA = ("conda ecosystem: pip installs into an active conda "
          "environment that owns the interpreter")
_ANTIEXAMPLE = ("tutorial anti-example: the deliberately bad Dockerfile "
                "teaches plain pip as one of its labeled problems")
_BOOTSTRAP = "pip bootstrap: the one legitimate use - installing uv"
_NOTEBOOKS = ("notebooks boundary: notebooks/ KEEP area pinned to "
              "its own stack")

_GROUPS: list[tuple[str, str, tuple[str, ...]]] = [
    ("docs/00-META/QUICK-START.md", _FALLBACK, (
        "pip install ollama",
        "python -m pip install --upgrade pip",
    )),
    ("docs/00-META/RESOURCES.md", _CONDA, (
        "pip install -r requirements.txt",
    )),
    ("docs/learning-resources/labs/LAB-006-Train-Model-From-Scratch.md",
     _CONDA, (
         "pip install torch tqdm",
         "pip install datasets tokenizers",
         "pip install wandb",
     )),
    ("docs/learning-resources/troubleshooting/"
     "TROUBLESHOOTING-Common-Issues.md", _CONDA, (
         "pip install transformers",
     )),
    ("docs/learning-resources/tutorials/TUTORIAL-002-Docker-Essentials.md",
     _ANTIEXAMPLE, (
         "RUN pip install -r requirements.txt",
     )),
    ("docs/learning-resources/tutorials/"
     "TUTORIAL-005-Production-Deployment.md", _BOOTSTRAP, (
         "pip install uv",
     )),
    ("docs/notebooks/README.md", _NOTEBOOKS, (
        "pip install missing-package",
    )),
]
ACCEPTED: dict[tuple[str, str], str] = {
    (rel, line): reason
    for rel, reason, lines in _GROUPS
    for line in lines
}


def fences(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_fence, label, buf, start = False, "", [], 0
    for i, line in enumerate(lines, 1):
        m = FENCE_OPEN.match(line)
        if not in_fence and m:
            in_fence, label, buf, start = True, m.group(1), [], i
        elif in_fence and line.startswith("```"):
            in_fence = False
            if label in LABELS:
                yield start, label, buf
            buf = []
        elif in_fence:
            buf.append(line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    n_fen = 0

    for path in sorted((args.root / "docs").rglob("*.md")):
        rel = path.relative_to(args.root).as_posix()
        fl = [(s, lb, b) for s, lb, b in fences(path)
              if "\n".join(b).strip()]
        if not fl:
            continue
        n_docs += 1
        n_fen += len(fl)
        for start, label, buf in fl:
            for j, line in enumerate(buf, 1):
                if line.lstrip().startswith("#"):
                    continue
                if not PIP_INSTALL.search(line):
                    continue
                stripped = line.strip()
                if (rel, stripped) in ACCEPTED:
                    continue
                findings.append(
                    f"UV-01 {rel}:{start + j} [{label.upper()}] "
                    f"plain 'pip install' bypasses the uv "
                    f"standard: {stripped[:80]}")

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"uv_install_check: {len(findings)} UV-01 finding(s) across "
          f"{n_docs} docs, {n_fen} fences (bash/sh/shell/dockerfile) "
          f"in docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
