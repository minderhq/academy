#!/usr/bin/env python3
"""notebook hygiene gate (NBH-01..04) for Minder Academy.

The platform conversion makes docs/notebooks/*.ipynb launchable
content: a crawler previews it, a binder/colab-style launcher reads
its kernelspec, and every committed byte lands in the platform's
diff and storage. The three existing notebook gates lock catalog
parity (NC), inbound navigation (NAV) and unfinished markers (NU);
none of them locks the FILE hygiene dimension - the commit-artifact
and structural-health classes a notebook editor accumulates on
every casual "Run All + Save".

NBH-01  stored outputs: a code cell carrying a non-empty `outputs`
        list. Committed execution artifacts are diff noise, size
        bloat, and a leak surface (a traceback or a printed token
        from one local run ships to every learner).

NBH-02  execution_count set: the same commit-artifact class one
        field over - a stale count claims an execution state the
        repo cannot reproduce.

NBH-03  structural health: unparseable JSON, a non-dict root, a
        missing/non-list `cells`, or a code cell without a string/
        list `source` - the platform preview and any nbformat
        consumer stop at the first such file.

NBH-04  kernelspec contract: metadata.kernelspec absent or its
        `name` not exactly "python3" - the curriculum is all-Python
        and the launcher keys on the exact name.

Born tick-690 from the probe census: 20 notebooks, 224 cells (102
code), 0 stored outputs, 0 execution_counts, 20x kernelspec
python3, all valid JSON - born at zero, hard-gated so the
casual-edit class can never regrow. nbformat_minor is 4 corpus-wide
(cell ids optional under the files' own declared format), so ids
are deliberately NOT gated.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-690).

Run over the whole corpus:
    python scripts/qa/notebook_hygiene_scan.py --root .
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KERNEL_NAME = "python3"


def scan_nb(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    try:
        nb = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
        findings.append(f"{rel}: NBH-03 unparseable notebook JSON - "
                        f"{type(exc).__name__}")
        return
    if not isinstance(nb, dict) or not isinstance(nb.get("cells"), list):
        findings.append(f"{rel}: NBH-03 structural health - root must "
                        f"be an object with a list 'cells'")
        return
    n_out = n_exec = n_src = 0
    for cell in nb["cells"]:
        if not isinstance(cell, dict):
            findings.append(f"{rel}: NBH-03 structural health - a cell "
                            f"is not an object")
            return
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs"):
            n_out += 1
        if cell.get("execution_count") is not None:
            n_exec += 1
        src = cell.get("source")
        if not isinstance(src, (str, list)):
            n_src += 1
    if n_out:
        findings.append(f"{rel}: NBH-01 stored outputs in {n_out} code "
                        f"cell(s) - platform repos stay output-free, "
                        f"strip before commit")
    if n_exec:
        findings.append(f"{rel}: NBH-02 execution_count set on {n_exec} "
                        f"code cell(s) - a committed count claims an "
                        f"execution state the repo cannot reproduce")
    if n_src:
        findings.append(f"{rel}: NBH-03 structural health - {n_src} "
                        f"code cell(s) without a string/list 'source'")
    ks = (nb.get("metadata") or {}).get("kernelspec")
    if not isinstance(ks, dict) or ks.get("name") != KERNEL_NAME:
        got = ks.get("name") if isinstance(ks, dict) else "absent"
        findings.append(f"{rel}: NBH-04 kernelspec contract - expected "
                        f"name '{KERNEL_NAME}', got '{got}' - the "
                        f"launcher keys on the exact name")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []
    n_files = 0
    for path in sorted((args.root / "docs" / "notebooks").glob("*.ipynb")):
        n_files += 1
        scan_nb(args.root, path, findings)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"notebook_hygiene_scan: {len(findings)} findings "
          f"(NBH-01 stored outputs / NBH-02 execution_count / NBH-03 "
          f"structural health / NBH-04 kernelspec python3) across "
          f"{n_files} notebooks in docs/notebooks/ (hard; born "
          f"tick-690 at zero - platform launch + diff hygiene)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
