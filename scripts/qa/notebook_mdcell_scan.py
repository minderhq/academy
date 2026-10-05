#!/usr/bin/env python3
"""notebook_mdcell_scan: the MARKDOWN-CELL RENDER-SURFACE dimension
across a notebook's markdown cells (NBM-01..02, hard).

A notebook's markdown cells are the lesson's prose ON THE PLATFORM:
the launcher (and the platform conversion) renders them, while the
fence family (codeblock_syntax_scan, fence_import_check, ...) and
the HTML hygiene gates walk docs/**/*.md only - .ipynb markdown
cells are JSON, so a fenced code block or a raw HTML tag inside a
notebook's prose was invisible to every .md render gate. The corpus
convention, measured the census->classify->lock way: 20 notebooks /
122 markdown cells carried 0 fenced code blocks and 0 raw HTML tags
(inline-code spans stripped first - backticked constructs render
literally and are safe) - lesson code lives in CODE cells where
NBC/NBE prove it, prose stays pure markdown. The gate is born at
zero to keep the convention.

The two rules:
- NBM-01 a fenced code block in a markdown cell (``` or ~~~ at
  line start, up to 3 spaces of indent; a fence inside notebook
  prose renders but no gate proves it parses - the .md fence
  family never sees it; if a lesson needs shown code, it belongs
  in a code cell)
- NBM-02 a raw HTML tag in a markdown cell (any tag-shaped
  `<letter...>` construct, checked AFTER inline-code spans are
  stripped; an unknown tag like <model> passes through the
  markdown-to-HTML conversion and can render INVISIBLY on the
  platform - prose escapes such placeholders with backticks)

Deliberate scope: markdown cells only - code cells are NBC/NBE's
jurisdiction (stats-only for NBM, the same split NBL documents);
structural health (unparseable JSON, malformed sources) stays
NBH-03's - silently skipped here, the designed cross-gate
agreement NBC/NBL/NBT/NBE/NBP document.
Born tick-696 at ZERO findings rc=0 (20 notebooks / 122 md cells).
"""
import argparse
import json
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(?:```|~~~)", re.M)
TAG = re.compile(r"<[a-zA-Z/][^>]*>")
INLINE = re.compile(r"`[^`]*`")


def cell_source(cell):
    """Join a notebook cell's source (list-of-str or str) to one str."""
    src = cell.get("source")
    if isinstance(src, list):
        return "".join(s for s in src if isinstance(s, str))
    return src if isinstance(src, str) else ""


def scan_nb(root, path, findings, stats):
    """Scan one notebook's markdown cells for the render rules."""
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
                cell.get("cell_type") != "markdown":
            continue
        if not isinstance(cell.get("source"), (list, str)):
            stats[2] += 1
            continue
        src = cell_source(cell)
        stats[1] += 1
        where = "%s markdown cell %d" % (
            path.relative_to(root).as_posix(), idx)
        if FENCE.search(src):
            findings.append(
                "%s: NBM-01 carries a fenced code block - no gate "
                "proves a notebook prose fence parses (the .md "
                "fence family never sees .ipynb cells); lesson "
                "code belongs in a code cell where NBC/NBE prove "
                "it" % where)
        bare = INLINE.sub("", src)
        if TAG.search(bare):
            findings.append(
                "%s: NBM-02 carries a raw HTML tag - it passes "
                "through the markdown-to-HTML conversion and can "
                "render invisibly on the platform; escape "
                "placeholders with backticks" % where)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="notebook markdown-cell render surface")
    ap.add_argument("--root", type=Path,
                    default=Path(__file__).resolve().parents[2])
    args = ap.parse_args(argv)
    root = args.root
    findings = []
    stats = [0, 0, 0]  # notebooks, md cells, NBH-03
    for path in sorted((root / "docs" / "notebooks").glob("*.ipynb")):
        stats[0] += 1
        scan_nb(root, path, findings, stats)
    for line in findings:
        sys.stdout.buffer.write(
            (line + "\n").encode("utf-8", "backslashreplace"))
    sys.stdout.buffer.write(
        ("notebook_mdcell_scan: %d findings (NBM-01 a fenced code "
         "block in a markdown cell / NBM-02 a raw HTML tag in a "
         "markdown cell; %d markdown cells scanned, %d cell(s) "
         "left to NBH-03) - hard; born tick-696 at zero over the "
         "real corpus (the .md fence and HTML gates never see "
         ".ipynb cells - the launcher RENDERS them)\n"
         % (len(findings), stats[1], stats[2]))
        .encode("utf-8", "backslashreplace"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
