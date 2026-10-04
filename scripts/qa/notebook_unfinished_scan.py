#!/usr/bin/env python3
"""notebook unfinished-content marker gate for the Minder Academy corpus.

NU-01  a markdown cell must not carry an unfinished-content marker:
       "coming soon", "under construction", "to be written", "to be
       added", "work in progress", or an uppercase TODO/TBD/FIXME.
       A notebook's markdown cells are its prose - they obey the same
       rule unfinished_marker_scan (UM-01) applies to .md files, with
       the same inline-code scrub.
NU-02  a code cell must not carry a marker in a non-comment position:
       a TODO/TBD/FIXME sitting in an identifier, a string literal or
       a bare expression is code the author meant to revisit, not an
       exercise prompt. Markers inside "#" comment segments stay
       invisible by design - the notebooks/README.md convention
       codifies "# TODO:" starter-code exercise prompts and the corpus
       carries 108 of them across all 20 notebooks (born tick-550
       census). UM-01 structurally cannot see any of this: its
       extraction model walks .md fences, so the .ipynb universe was
       unlocked the same way the discovery scan unlocked it in
       tick-549 - a file class every md-only gate silently skipped.

TODO/TBD/FIXME match uppercase only: lowercase "todo" is the exercise
domain noun, the marker idiom is always shouted (UM-01 parity). The
comment-stripping split is per line, first "#" onward - matching how
the corpus's prompts are written (marker never precedes a "#").

Hard gate (exit 1 on findings): baseline 0 at birth (tick-550) over
all 20 notebooks / 109 raw marker-shaped hits, 108 in the legitimate
comment-prompt class and the 1 remaining hit NB-703's "how to hack"
prompt-injection test string, which no RULES pattern matches. The
gate locks the notebook fleet against the same unfinished-content rot
UM-01 locks prose against.

Run over the whole corpus:
    python scripts/qa/notebook_unfinished_scan.py --root .
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

INLINE_CODE_RE = re.compile(r"`[^`]*`")

# Same (pattern, label) pairs as unfinished_marker_scan - one marker
# vocabulary across md prose and notebook prose.
RULES = [
    (re.compile(r"coming soon", re.IGNORECASE), "coming soon"),
    (re.compile(r"under construction", re.IGNORECASE), "under construction"),
    (re.compile(r"to be written", re.IGNORECASE), "to be written"),
    (re.compile(r"to be added", re.IGNORECASE), "to be added"),
    (re.compile(r"work in progress", re.IGNORECASE), "work in progress"),
    (re.compile(r"\b(?:TODO|TBD|FIXME)\b"), "shouted TODO/TBD/FIXME"),
]


def _hit(text: str) -> str | None:
    for pat, label in RULES:
        if pat.search(text):
            return label
    return None


def scan_notebook(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    nb = json.loads(path.read_bytes().decode("utf-8"))
    for ci, cell in enumerate(nb.get("cells", [])):
        src = "".join(cell.get("source", []))
        if cell.get("cell_type") == "markdown":
            prose = INLINE_CODE_RE.sub("", src)
            for ln, raw in enumerate(prose.split("\n"), 1):
                label = _hit(raw)
                if label:
                    findings.append(
                        f"{rel}#c{ci}:NU-01 unfinished-content marker in "
                        f"markdown cell ({label}); notebook prose obeys "
                        f"the same rule as .md prose (UM-01 parity)")
        elif cell.get("cell_type") == "code":
            for ln, raw in enumerate(src.split("\n"), 1):
                code_part = raw.split("#", 1)[0]
                label = _hit(code_part)
                if label:
                    findings.append(
                        f"{rel}#c{ci}:NU-02 unfinished-content marker in "
                        f"code-cell non-comment position ({label}); "
                        f"comment-line exercise prompts are invisible "
                        f"by design")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    nbdir = args.root / "docs" / "notebooks"
    findings: list[str] = []
    n_files: set[str] = set()
    n_nb = 0
    for path in sorted(nbdir.glob("*.ipynb")):
        n_nb += 1
        try:
            before = len(findings)
            scan_notebook(args.root, path, findings)
            if len(findings) > before:
                n_files.add(path.relative_to(args.root).as_posix())
        except (UnicodeDecodeError, OSError, json.JSONDecodeError, KeyError):
            findings.append(f"{path.relative_to(args.root).as_posix()}: "
                            f"NU-00 unreadable notebook (json/encoding)")
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"notebook_unfinished_scan: {len(findings)} findings "
          f"(NU-01 markers in markdown cells, NU-02 markers in "
          f"code-cell non-comment positions) in {len(n_files)} of "
          f"{n_nb} notebooks across docs/notebooks/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
