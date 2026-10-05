#!/usr/bin/env python3
"""notebook_title_scan: the notebook H1-title parity dimension the .md
title gates never see (NBT-01..02, hard).

title_h1_parity_scan and the heading family walk docs/**/*.md while a
notebook's title lives in JSON (the first markdown cell's first `# `
heading), so a notebook whose open-broadcast title drifted from the
docs/notebooks/README.md index was invisible to every title gate. The
index is what a learner (and the platform conversion) reads first; a
title that exists only inside the .ipynb does not exist.

tick-693 measured the drift before locking it: 20 notebooks, 14/20
already carry exact H1 == README-link-text parity (the corpus
convention), 6/20 had drifted (NB-204/301/303/401/601/701). The drain
realigned the README link texts to the notebooks' own H1 truth and the
MASTER-INDEX title cells to the H1 minus the 'NB-NNN: ' prefix (the
notebook_catalog_check README_ROW regex consumes the prefix before its
title capture, so NC-02 compares README-minus-prefix vs MI verbatim
and the drain keeps both green). NBT-01 locks H1 -> README verbatim
presence; NC-02 chains H1 -> MI transitively for every id MI carries.

The two rules:
- NBT-01 the first markdown cell's first H1 heading is absent
  verbatim from docs/notebooks/README.md (the launcher-facing
  catalog: a learner browsing the index never sees the drifted
  title).
- NBT-02 the notebook carries no H1 at all - the first markdown cell
  has no `# ` heading, or there is no markdown cell (born at zero:
  the census measured 20/20 with an H1).

Jurisdiction split with NBH: structural health (unparseable JSON,
malformed sources) stays NBH-03's - this gate silently skips what NBH
flags, the same designed cross-gate agreement NBC and NBL document.
Born tick-693 at ZERO findings rc=0 over the drained corpus.
"""
import argparse
import json
import re
import sys
from pathlib import Path

H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def cell_source(cell):
    """Join a notebook cell's source (list-of-str or str) to one str."""
    src = cell.get("source")
    if isinstance(src, list):
        return "".join(s for s in src if isinstance(s, str))
    return src if isinstance(src, str) else ""


def scan_nb(root, path, findings, stats):
    """Scan one notebook's first markdown cell H1 against the README."""
    rel = path.relative_to(root).as_posix()
    try:
        nb = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        stats[2] += 1
        return
    if not isinstance(nb, dict) or not isinstance(nb.get("cells"), list):
        stats[2] += 1
        return
    first_md = None
    for cell in nb["cells"]:
        if not isinstance(cell, dict):
            stats[2] += 1
            return
        if cell.get("cell_type") == "markdown":
            first_md = cell_source(cell)
            break
    if first_md is None:
        findings.append(
            "%s: NBT-02 the notebook carries no markdown cell at all - "
            "the open-broadcast title the index should carry does not "
            "exist anywhere in it" % rel)
        return
    m = H1.search(first_md)
    if m is None:
        findings.append(
            "%s: NBT-02 the first markdown cell carries no '# ' H1 "
            "heading - the notebook opens without a title the README "
            "index could mirror" % rel)
        return
    title = m.group(1)
    if title not in README_TEXT:
        findings.append(
            "%s: NBT-01 the first markdown cell H1 '%s' is absent "
            "verbatim from docs/notebooks/README.md - the index and "
            "the notebook's own open-broadcast title have drifted"
            % (rel, title))
        return
    stats[1] += 1


README_TEXT = ""


def main(argv=None):
    global README_TEXT
    ap = argparse.ArgumentParser(
        description="notebook H1-title parity vs the README index")
    ap.add_argument("--root", type=Path,
                    default=Path(__file__).resolve().parents[2])
    args = ap.parse_args(argv)
    root = args.root
    readme = root / "docs" / "notebooks" / "README.md"
    try:
        README_TEXT = readme.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        README_TEXT = ""  # an absent index fails every title parity
    findings = []
    stats = [0, 0, 0]  # notebooks, with-H1-parity, NBH-03 jurisdiction
    for path in sorted((root / "docs" / "notebooks").glob("*.ipynb")):
        stats[0] += 1
        scan_nb(root, path, findings, stats)
    for line in findings:
        sys.stdout.buffer.write(
            (line + "\n").encode("utf-8", "backslashreplace"))
    sys.stdout.buffer.write(
        ("notebook_title_scan: %d findings (NBT-01 first-md-cell H1 "
         "absent verbatim from docs/notebooks/README.md / NBT-02 no H1 "
         "in the first markdown cell; %d/%d notebooks carry index "
         "parity, %d cell(s) left to NBH-03) - hard; born tick-693 at "
         "zero over the drained corpus (README link texts and "
         "MASTER-INDEX title cells realigned to the notebooks' own H1 "
         "truth)\n"
         % (len(findings), stats[1], stats[0], stats[2]))
        .encode("utf-8", "backslashreplace"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
