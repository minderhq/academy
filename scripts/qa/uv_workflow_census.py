#!/usr/bin/env python3
"""uv project-workflow adoption census (UV-02) for Minder Academy.

The uv modernization taught the corpus the imperative layer (uv pip
install, uv venv); this census tracks its migration to uv's own
declarative project workflow - dependencies declared in pyproject.toml,
pinned by uv.lock, driven by uv init/add/sync/run. It counts, across
docs/: occurrences of each tracked uv subcommand inside labeled fences,
and how many documents mention the marker files of the two dependency
layers. Born from the tick-339 census: the imperative layer was
fluent (uv pip install 135, uv venv 9 inside labeled fences; a looser
whole-file scan counted 192) while every project-workflow verb sat
at 0 - pyproject.toml lived in 2 docs, uv.lock in none. The same
tick ENVIRONMENT-SETUP gained its "uv Project Workflow (pyproject.toml
+ uv.lock)" section, contributing the first uv init/add/sync/run
occurrences; the numbers are expected to move as the declarative
standard spreads through the corpus.

tick-340: uvx joined the tracked surface when ENVIRONMENT-SETUP's
tooling section introduced the tool runner (ruff lint/format via
uvx, uv tool install for daily use).

Report mode - exit 0 by design; the census is an inventory, not a gate.

Run over the whole corpus:
    python scripts/qa/uv_workflow_census.py --root .

The fence parser is the tick-678 CommonMark canon state machine: the
opener's marker run is captured (f_char, f_len), a closer must repeat
the opener's character in a run at least as long, a different fence
character never closes, a non-closer marker line is fence content.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
LABELS = {"bash", "sh", "shell", "dockerfile", "powershell"}

# uv subcommands in display order; one word-boundary regex each
SUBCOMMANDS = [
    "uv init", "uv add", "uv remove", "uv sync", "uv lock", "uv run",
    "uv tool", "uvx", "uv self", "uv python", "uv venv",
    "uv pip install", "uv pip compile",
]
SUB_RE = {s: re.compile(r"\b" + re.escape(s) + r"\b") for s in SUBCOMMANDS}

# marker files of the two dependency-management layers
MARKERS = ["pyproject.toml", "uv.lock", "requirements.txt"]


def fences(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_fence: tuple[str, int] | None = None
    label, buf, start = "", [], 0
    for i, line in enumerate(lines, 1):
        m = FENCE_OPEN.match(line)
        if m:
            f_char, f_len = m.group(1)[0], len(m.group(1))
            if in_fence:
                if f_char == in_fence[0] and f_len >= in_fence[1]:
                    in_fence = None  # true closer ends any block
                    if label in LABELS:
                        yield start, label, buf
                    buf = []
                else:
                    buf.append(line)  # non-closer marker is content
            else:
                in_fence = (f_char, f_len)
                label, buf, start = m.group(2), [], i
        elif in_fence:
            buf.append(line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    sub_hits = {s: 0 for s in SUBCOMMANDS}
    n_fen = 0
    marker_docs = {m: 0 for m in MARKERS}

    for path in sorted((args.root / "docs").rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in MARKERS:
            if marker in text:
                marker_docs[marker] += 1
        for _start, _label, buf in fences(path):
            if not "\n".join(buf).strip():
                continue
            n_fen += 1
            for line in buf:
                for s in SUBCOMMANDS:
                    sub_hits[s] += len(SUB_RE[s].findall(line))

    counts = ", ".join(f"{s} {sub_hits[s]}" for s in SUBCOMMANDS)
    files = ", ".join(f"{m} in {marker_docs[m]} docs" for m in MARKERS)
    print(f"uv_workflow_census (report): {counts}; {files} "
          f"across docs/ ({n_fen} labeled fences scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
