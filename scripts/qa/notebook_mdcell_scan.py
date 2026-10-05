#!/usr/bin/env python3
"""notebook_mdcell_scan: the MARKDOWN-CELL RENDER-SURFACE dimension
across a notebook's markdown cells (NBM-01..07, hard).

A notebook's markdown cells are the lesson's prose ON THE PLATFORM:
the launcher (and the platform conversion) renders them, while the
fence family (codeblock_syntax_scan, fence_import_check, ...) and
the HTML hygiene gates walk docs/**/*.md only - .ipynb markdown
cells are JSON, so a fenced code block, a raw HTML tag or a broken
heading hierarchy inside a notebook's prose was invisible to every
.md render gate. The corpus convention, measured the
census->classify->lock way: 20 notebooks / 122 markdown cells
carried 0 fenced code blocks and 0 raw HTML tags (inline-code spans
stripped first - backticked constructs render literally and are
safe; tick-696), and tick-697's census over the same cells measured
142 headings with 0 H1s outside the title position, 0 level skips
and 0 setext underlines. Lesson code lives in CODE cells where
NBC/NBE prove it, prose stays pure markdown. The gate is born at
zero to keep the convention.

The seven rules:
- NBM-01 a fenced code block in a markdown cell (a backtick or
  tilde fence at line start, up to 3 spaces of indent; a fence
  inside notebook prose renders but no gate proves it parses - the
  .md fence family never sees it; if a lesson needs shown code, it
  belongs in a code cell)
- NBM-02 a raw HTML tag in a markdown cell (any tag-shaped
  `<letter...>` construct, checked AFTER inline-code spans are
  stripped; an unknown tag like <model> passes through the
  markdown-to-HTML conversion and can render INVISIBLY on the
  platform - prose escapes such placeholders with backticks)
- NBM-03 an H1 heading anywhere but the canonical title position -
  the notebook's FIRST markdown cell's first H1 (NBT-01/02 pin that
  first H1's content; this pins position and uniqueness - a second
  H1 renders as a second page title on the platform)
- NBM-04 a heading-level skip across the notebook's markdown-cell
  heading sequence (a heading more than one level deeper than the
  previous heading - the same rule RH-02 applies to docs/**/*.md;
  the platform renders the md cells as one document, so h2->h4
  orphans a section)
- NBM-05 a setext-style heading (an = or -- underline directly
  under a non-blank line renders as an h1/h2 in CommonMark - an
  invisible way to mint a second title; a horizontal rule needs a
  blank line above)
- NBM-06 a pipe-table row whose pipe-separator count differs from
  its block's delimiter row (GFM sizes a pipe table by the
  delimiter row and pads or drops ragged rows silently - the same
  content-loss class TH-01 polices across docs markdown, and the
  platform renders the md cells, so the same loss reaches the
  learner here; inline-code spans are stripped before counting, a
  backticked pipe renders literally, a backslash-escaped pipe is
  cell content, and per-block consistency lets adjacent tables of
  different widths stay legal)
- NBM-07 an HTML comment opener in a markdown cell (a raw comment
  opens a CommonMark raw-HTML block and everything through its
  closer renders invisibly - the same class HC-01 polices across
  docs markdown; NBM-02's tag pattern requires a letter after the
  angle bracket and cannot match the bang opener, so the comment
  class was invisible to both universes; inline-code spans are
  stripped first and 4-space-indented lines are skipped, an
  indented code block renders literally)

Deliberate scope: markdown cells only - code cells are NBC/NBE's
jurisdiction (stats-only for NBM, the same split NBL documents);
structural health (unparseable JSON, malformed sources) stays
NBH-03's - silently skipped here, the designed cross-gate
agreement NBC/NBL/NBT/NBE/NBP document.
Born tick-696 at ZERO findings rc=0 (NBM-01..02 over 20 notebooks /
122 md cells); NBM-03..05 born tick-697 at ZERO over the same
corpus (142 headings measured); NBM-06 born tick-701 at ZERO over
the same corpus (tick-701's census measured 0 pipe-table blocks /
0 rows in the md cells - the convention 'tables live in docs, not
notebook prose' is real and this keeps it); NBM-07 born tick-705
at ZERO over the same corpus (the census measured 0 comment-opener
lines and 0 indented carve-surface lines across the same 20
notebooks / 122 md cells - notebook prose carries no HTML
comments, they live inside docs fences where HC-01 polices them).
"""
import argparse
import json
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(?:```|~~~)", re.M)
TAG = re.compile(r"<[a-zA-Z/][^>]*>")
INLINE = re.compile(r"`[^`]*`")
ATX = re.compile(r"^(#{1,6})(?!#)(?:\s+.*)?$")
SETEXT_EQ = re.compile(r"^=+\s*$")
SETEXT_DASH = re.compile(r"^-{2,}\s*$")
DELIM = re.compile(r"^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$")


def separators(line: str) -> int:
    """Pipe-separator count after inline-code spans are stripped and
    backslash-escaped pipes removed (a backticked pipe renders
    literally, an escaped pipe is cell content)."""
    stripped = INLINE.sub("", line)
    return stripped.replace("\\|", "").count("|")


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
    rel = path.relative_to(root).as_posix()
    first_md = None
    seen_h1 = False
    prev_level = 0
    for idx, cell in enumerate(nb["cells"]):
        if not isinstance(cell, dict) or \
                cell.get("cell_type") != "markdown":
            continue
        if first_md is None:
            first_md = idx
        if not isinstance(cell.get("source"), (list, str)):
            stats[2] += 1
            continue
        src = cell_source(cell)
        stats[1] += 1
        where = "%s markdown cell %d" % (rel, idx)
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
        for j, ln in enumerate(src.split("\n"), 1):
            if ln.startswith("    ") and ln.strip():
                stats[5] += 1
                continue
            if "<!--" in INLINE.sub("", ln):
                findings.append(
                    "%s line %d: NBM-07 carries an HTML comment "
                    "opener - a raw comment opens a CommonMark "
                    "raw-HTML block and everything through its "
                    "closer renders invisibly on the platform; "
                    "notes belong in docs fences" % (where, j))
        prev_line = ""
        for ln in src.split("\n"):
            if SETEXT_EQ.match(ln) or SETEXT_DASH.match(ln):
                if prev_line.strip():
                    findings.append(
                        "%s: NBM-05 setext-style heading - the "
                        "underline renders the line above as an "
                        "h1/h2 in CommonMark, an invisible second "
                        "title; a horizontal rule needs a blank "
                        "line above" % where)
                prev_line = ln
                continue
            m = ATX.match(ln)
            if not m:
                prev_line = ln
                continue
            lvl = len(m.group(1))
            if lvl == 1 and (seen_h1 or idx != first_md):
                findings.append(
                    "%s: NBM-03 an H1 outside the canonical title "
                    "position (the first markdown cell's first H1) "
                    "- the platform renders it as a second page "
                    "title" % where)
            seen_h1 = seen_h1 or lvl == 1
            if prev_level and lvl > prev_level + 1:
                findings.append(
                    "%s: NBM-04 heading-level skip h%d->h%d - the "
                    "md cells render as one document and an "
                    "orphaned section breaks its outline"
                    % (where, prev_level, lvl))
            prev_level = lvl
        # NBM-06: pipe-table structural health in the md cell (the
        # TH-01 frame; a md-cell fence is already illegal per
        # NBM-01, and its content must not double-count as table
        # blocks, so the walk is fence-aware)
        blocks = []
        block = []
        in_fence = False
        for j, ln in enumerate(src.split("\n"), 1):
            if FENCE.match(ln):
                in_fence = not in_fence
                if len(block) >= 2:
                    blocks.append(block)
                block = []
                continue
            if in_fence or "|" not in ln:
                if len(block) >= 2:
                    blocks.append(block)
                block = []
                continue
            block.append((j, ln))
        if len(block) >= 2:
            blocks.append(block)
        for blk in blocks:
            if len(blk) < 2 or not DELIM.match(blk[1][1]):
                continue
            stats[3] += 1
            stats[4] += len(blk)
            width = separators(blk[1][1])
            for j, ln in blk:
                n = separators(ln)
                if n != width:
                    findings.append(
                        "%s line %d: NBM-06 row carries %d pipe "
                        "separators, the delimiter row %d - GFM "
                        "pads short rows with empty cells and "
                        "drops long ones" % (where, j, n, width))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="notebook markdown-cell render surface")
    ap.add_argument("--root", type=Path,
                    default=Path(__file__).resolve().parents[2])
    args = ap.parse_args(argv)
    root = args.root
    findings = []
    stats = [0, 0, 0, 0, 0, 0]  # nb, md cells, NBH-03, blocks, rows, indented
    for path in sorted((root / "docs" / "notebooks").glob("*.ipynb")):
        stats[0] += 1
        scan_nb(root, path, findings, stats)
    for line in findings:
        sys.stdout.buffer.write(
            (line + "\n").encode("utf-8", "backslashreplace"))
    sys.stdout.buffer.write(
        ("notebook_mdcell_scan: %d findings (NBM-01 a fenced code "
         "block in a markdown cell / NBM-02 a raw HTML tag in a "
         "markdown cell / NBM-03 an H1 outside the title position / "
         "NBM-04 a heading-level skip / NBM-05 a setext-style "
         "heading / NBM-06 a pipe-table row ragged against its "
         "delimiter row / NBM-07 an HTML comment opener in a "
         "markdown cell; %d markdown cells scanned, %d table "
         "block(s) / %d row(s) walked, %d cell(s) left to "
         "NBH-03, %d indented line(s) skipped) - hard; "
         "NBM-01..02 born tick-696, NBM-03..05 born tick-697, "
         "NBM-06 born tick-701, NBM-07 born tick-705, all at zero "
         "over the real corpus (the .md render gates never see "
         ".ipynb cells - the launcher RENDERS them)\n"
         % (len(findings), stats[1], stats[3], stats[4], stats[2],
            stats[5]))
        .encode("utf-8", "backslashreplace"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
