#!/usr/bin/env python3
"""notebook_pip_scan: the pip/uv INSTALL-DISCIPLINE dimension across a
notebook's code cells (NBP-01..02, hard).

The corpus standard is uv (the user's own modernization doctrine and
ENVIRONMENT-SETUP.md's installer): installs live in the setup doc,
the launcher's environment is pre-provisioned, and a lesson cell
mutating it is a side effect a fresh kernel cannot undo. The three
existing uv gates (pip_uv_scan, uv_install_check,
uv_workflow_census) walk docs/**/*.md only - a `!pip install torch`
inside a .ipynb code cell was invisible to every install gate while
the launcher RUNS the cells, making a committed pip line a real
environment mutation on every learner run. The census first, the
census->classify->lock way: 20 notebooks / 102 code cells measured
0 standalone pip tokens and 0 uv add commands - the corpus
convention is "install commands never appear in lesson cells", and
the gate is born at zero to keep it that way.

The two rules:
- NBP-01 a standalone pip/pip3 token anywhere in a code cell's raw
  source (the boundary regex excludes pip-tools-style package
  names and pipx/pipeline identifiers; !pip install, %pip
  install, the bare form, subprocess strings, uv pip install and
  prose comments all carry the token - the measured convention
  locks them all out; a comment wanting to teach the distinction
  rephrases around it)
- NBP-02 an `uv add` command in a code cell (the modern form is
  the same env-mutation class; `uv pip install` already falls to
  NBP-01 via its pip token)

Deliberate scope: the scan is token-level over RAW source - no AST,
no SyntaxError skip (a pip install in a broken cell is still a pip
install; cell syntax stays NBC-01's jurisdiction, structural health
stays NBH-03's - silently skipped here, the designed cross-gate
agreement NBC/NBL/NBT/NBE document).
Born tick-695 at ZERO findings rc=0 (20 notebooks / 102 code cells).
"""
import argparse
import json
import re
import sys
from pathlib import Path

PIP_TOKEN = r"(?<![\w.-])pip3?(?![\w-])"
UV_ADD = r"(?<![\w.-])uv\s+add\b"


def cell_source(cell):
    """Join a notebook cell's source (list-of-str or str) to one str."""
    src = cell.get("source")
    if isinstance(src, list):
        return "".join(s for s in src if isinstance(s, str))
    return src if isinstance(src, str) else ""


def scan_nb(root, path, findings, stats):
    """Scan one notebook's code cells' raw source for the rules."""
    try:
        nb = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        stats[2] += 1
        return
    if not isinstance(nb, dict) or not isinstance(nb.get("cells"), list):
        stats[2] += 1
        return
    for idx, cell in enumerate(nb["cells"]):
        if not isinstance(cell, dict) or \
                cell.get("cell_type") != "code":
            continue
        if not isinstance(cell.get("source"), (list, str)):
            stats[2] += 1
            continue
        src = cell_source(cell)
        stats[1] += 1
        where = "%s code cell %d" % (
            path.relative_to(root).as_posix(), idx)
        if re.search(PIP_TOKEN, src, re.IGNORECASE):
            findings.append(
                "%s: NBP-01 carries a standalone 'pip' token - "
                "installs live in docs/00-META/ENVIRONMENT-SETUP.md "
                "(uv), the launcher's environment is pre-provisioned "
                "and a lesson cell mutating it is a side effect the "
                "fresh kernel cannot undo" % where)
            continue  # one finding per cell
        if re.search(UV_ADD, src):
            findings.append(
                "%s: NBP-02 carries an 'uv add' command - the same "
                "environment-mutation class as pip on the modern "
                "tool; installs belong to the setup doc, not lesson "
                "cells" % where)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="notebook pip/uv install discipline")
    ap.add_argument("--root", type=Path,
                    default=Path(__file__).resolve().parents[2])
    args = ap.parse_args(argv)
    root = args.root
    findings = []
    stats = [0, 0, 0]  # notebooks, code cells, NBH-03
    for path in sorted((root / "docs" / "notebooks").glob("*.ipynb")):
        stats[0] += 1
        scan_nb(root, path, findings, stats)
    for line in findings:
        sys.stdout.buffer.write(
            (line + "\n").encode("utf-8", "backslashreplace"))
    sys.stdout.buffer.write(
        ("notebook_pip_scan: %d findings (NBP-01 a standalone 'pip' "
         "token in a code cell / NBP-02 an 'uv add' command in a "
         "code cell; %d code cells scanned, %d cell(s) left to "
         "NBH-03) - hard; born tick-695 at zero over the real "
         "corpus (the uv gate family walks docs/**/*.md only - the "
         "launcher RUNS notebook cells)\n"
         % (len(findings), stats[1], stats[2]))
        .encode("utf-8", "backslashreplace"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
