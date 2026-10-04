#!/usr/bin/env python3
r"""Mermaid diagram integrity (DM-01..03, HARD) for Minder Academy.

The corpus carries 56 mermaid blocks in 19 docs (52 graph, 2
stateDiagram-v2, 2 sequenceDiagram) and the platform renders every
one directly - a syntax-broken block renders as a visible error
box for the learner, the same defect class as a broken markdown
table (table_scan TB-01/02). Nothing validated them before.

DM-01  the first non-empty line of a block must start with a known
       diagram-type keyword (graph/flowchart/sequenceDiagram/
       stateDiagram(-v2)/erDiagram/gantt/pie/...) - an unknown
       header renders as an error box everywhere
DM-02  in graph/flowchart blocks, node-label text outside quoted
       segments must not contain ()[]{} - mermaid requires quoting
       for those in labels (the classic `A[Parent (child)]`
       breakage). Shape wrappers are understood: `id[(db)]`,
       `id((circle))`, `id{{hex}}`, `id[/para/]` are valid and
       their delimiters are not label text; `<br/>`, colons and
       commas inside labels are fine
DM-03  in graph/flowchart blocks, a node opened but closed by an
       edge operator or end-of-line before its shape close
       (unbalanced node)

Quoted segments (`"..."`) are skipped wholesale - quoted label
text may contain anything. stateDiagram/sequenceDiagram blocks get
DM-01 only (their message/state syntax has no bracket-label class).

Born tick-462: birth census over all 56 blocks found 0 real
findings; the first census draft's 25 hits were its own greedy
label regex spanning `A[x] --> B[y]` edges plus the legitimate
`[(...)]` database shape - the shipped scanner is shape- and
quote-aware, hard from birth at 0/0/0 across 56 blocks.

Run over the whole corpus:
    python scripts/qa/diagram_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(```|~~~)")  # CommonMark: <=3 leading spaces
MERMAID_OPEN = re.compile(r"^```\s*mermaid\s*$", re.I)
DIAGRAM_TYPES = (
    "flowchart", "graph", "sequenceDiagram", "classDiagram",
    "stateDiagram", "erDiagram", "journey", "gantt", "pie",
    "quadrantChart", "timeline", "gitGraph", "mindmap", "sankey-beta",
    "xychart-beta", "block-beta", "architecture-beta", "packet-beta",
    "kanban", "requirementDiagram", "C4Context", "C4Container",
    "C4Component", "C4Dynamic", "C4Deployment")
# shape-open tokens, longest first; close-sequence per opener
# [(db)] ([stadium]) ((circle)) {{hex}} [/para/] [\back/] [rect] (round) {round}
SHAPES = {"[(": ")]", "([": "])", "((": "))", "{{": "}}", "[/": "/]",
          "[\\": "\\]", "[": "]", "(": ")", "{": "}"}
OPEN_RE = re.compile(
    r"[A-Za-z0-9_]+\s*(\[\(|\(\[|\(\(|\{\{|\[\/|\[\\|\[|\(|\{)")
EDGE_OP = re.compile(r"(-{2,}>|-\.+->?|={2,}>|-{2,}x|--o|--x|\.\.\.\>|--\|)")
FM_CLOSE = re.compile(r"^---\s*$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def body_lines(text: str) -> list[str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return lines
    for i, ln in enumerate(lines[1:40], 1):
        if FM_CLOSE.match(ln):
            return lines[i + 1:]
    return lines


def scan_graph_line(ln: str) -> list[str]:
    """DM-02/DM-03 findings for one graph-family line."""
    probs: list[str] = []
    pos = 0
    while m := OPEN_RE.search(ln, pos):
        opener = m.group(1)
        close = SHAPES[opener]
        i = m.end()
        unquoted: list[str] = []
        closed = False
        while i < len(ln):
            ch = ln[i]
            if ch == '"':  # quoted segment - skip wholesale
                j = ln.find('"', i + 1)
                if j == -1:
                    break  # DM-04-ish unbalanced quote; caught as unbalanced
                i = j + 1
                continue
            if ln.startswith(close, i):
                closed = True
                i += len(close)
                break
            if EDGE_OP.search(ln, i) and EDGE_OP.match(ln, i):
                break  # edge operator before shape close -> unbalanced
            if ch in "()[]{}":
                unquoted.append(ch)
            i += 1
        if not closed:
            probs.append("DM-03 unbalanced node at col %d: %s"
                         % (m.start() + 1, ln.strip()[:70]))
        elif unquoted:
            probs.append("DM-02 unquoted %s in label at col %d: %s"
                         % ("".join(sorted(set(unquoted))),
                            m.start() + 1, ln.strip()[:70]))
        pos = i if i > pos else m.end()
    return probs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_blocks = n_docs = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        lines = body_lines(text)
        rel = path.relative_to(args.root).as_posix()
        i = 0
        while i < len(lines):
            if not MERMAID_OPEN.match(lines[i]):
                i += 1
                continue
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i >= len(lines) or FENCE.match(lines[i]):
                continue  # empty block; fence pairing owned by fence gates
            n_blocks += 1
            loc = "%s:%d" % (rel, i + 1)
            hdr = lines[i].strip()
            if not hdr.startswith(DIAGRAM_TYPES):
                findings.append("DM-01 %s: unknown diagram header `%s`"
                                % (loc, hdr[:60]))
            is_graph = hdr.startswith(("graph", "flowchart"))
            i += 1
            while i < len(lines) and not FENCE.match(lines[i]):
                if is_graph and lines[i].strip():
                    for p in scan_graph_line(lines[i]):
                        findings.append("DM %s +%d: %s"
                                        % (loc, i + 1, p))
                i += 1
        n_docs += 1
    for f in findings:
        print("  " + esc(f))
    print("diagram_scan: %d mermaid blocks in %d docs scanned; "
          "%d DM findings - all hard (header known, labels "
          "quote/shape-aware clean; born tick-462 at 0 across 56 "
          "blocks / 19 docs)" % (n_blocks, n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
