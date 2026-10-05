#!/usr/bin/env python3
"""notebook markdown-cell link gate (NBL-01..03) for Minder Academy.

The .md link gate family never sees a notebook link: linkcheck,
link_case_scan, link_text_scan and casecheck walk docs/**/*.md, while
docs/notebooks/*.ipynb markdown cells are JSON - a link inside a
notebook was invisible to every link gate. The probe census (tick-692)
measured the notebook layer link-free across every flavor: 20
notebooks, 122 markdown cells, 0 inline/image links, 0 reference-style
definitions, 0 HTML anchors, 0 angle autolinks, and 0 link-shaped
literals in the 102 code cells (byte-verified with grep against the raw
.ipynb files). The .md corpus carries 6175 gated links; the notebook
layer carries zero by design.

NBL-01  inline or image markdown link `[text](target)` in a markdown
        cell (the `!` image form matches - the bracket/target pair is
        the same construct).

NBL-02  reference-style link definition `[label]: target` in a
        markdown cell.

NBL-03  HTML anchor (`href=`) or angle autolink `<https://...>` in a
        markdown cell.

Why the zero-link shape is the platform-safe shape: the launcher serves
a notebook standalone - a repo-relative target breaks at serve time
(the .ipynb is copied out of the repo layout) and an http target rots
with no gate able to see it. Lesson navigation lives in the .md layer
(module READMEs, MASTER-INDEX, notebooks/README), which every link
gate already locks; this gate locks that the notebook layer stays
navigation-free so the class can never regrow.

Scope: markdown cells only (the rendering surface). A link-shaped
string inside a code cell is counted informationally but not gated -
a string that never renders is not a learner-facing link, and a
notebook teaching Markdown syntax would false-positive.

Structural health (unparseable JSON, malformed sources) is NBH-03's
jurisdiction - NBL silently skips what NBH flags, the same designed
cross-gate agreement NBC documents.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-692).

Run over the whole corpus:
    python scripts/qa/notebook_link_scan.py --root .
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The three rule faces. INLINE also matches the `![alt](src)` image
# form (the `!` sits outside the bracket pair) and the pure in-notebook
# `#anchor` form (an anchor href still renders as a link surface).
INLINE_LINK = re.compile(r"\[[^\]]*\]\([^)\s]+\)")
REFDEF_LINK = re.compile(r"^\s*\[[^\]]+\]:\s*\S+", re.MULTILINE)
AUTOLINK = re.compile(r"<https?://[^>\s]+>")
HTML_HREF = re.compile(r"href\s*=", re.IGNORECASE)


def cell_source(cell: dict) -> str:
    src = cell.get("source")
    if isinstance(src, list):
        return "".join(s for s in src if isinstance(s, str))
    return src if isinstance(src, str) else ""


def scan_nb(root: Path, path: Path, findings: list[str],
            stats: list[int]) -> None:
    rel = path.relative_to(root).as_posix()
    try:
        nb = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        stats[3] += 1  # structural-health jurisdiction: NBH-03 flags it
        return
    if not isinstance(nb, dict) or not isinstance(nb.get("cells"), list):
        stats[3] += 1
        return
    for idx, cell in enumerate(nb["cells"]):
        if not isinstance(cell, dict):
            stats[3] += 1
            continue
        if cell.get("cell_type") == "markdown":
            stats[1] += 1
            if not isinstance(cell.get("source"), (str, list)):
                stats[3] += 1  # NBH-03 jurisdiction
                continue
            src = cell_source(cell)
            for m in INLINE_LINK.finditer(src):
                findings.append(
                    f"{rel}: NBL-01 markdown cell {idx} carries an "
                    f"inline/image link '{m.group(0)[:48]}' - the "
                    f"notebook layer is link-free by design; lesson "
                    f"navigation lives in the .md layer and the "
                    f"platform serves notebooks standalone (a "
                    f"repo-relative target breaks at serve time, an "
                    f"http target rots with no gate able to see it)")
            for m in REFDEF_LINK.finditer(src):
                findings.append(
                    f"{rel}: NBL-02 markdown cell {idx} carries a "
                    f"reference-style link definition "
                    f"'{m.group(0)[:48]}' - the notebook layer is "
                    f"link-free by design; lesson navigation lives in "
                    f"the .md layer and the platform serves notebooks "
                    f"standalone")
            for m in AUTOLINK.finditer(src):
                findings.append(
                    f"{rel}: NBL-03 markdown cell {idx} carries an "
                    f"angle autolink '{m.group(0)[:48]}' - the "
                    f"notebook layer is link-free by design; lesson "
                    f"navigation lives in the .md layer and the "
                    f"platform serves notebooks standalone")
            for m in HTML_HREF.finditer(src):
                findings.append(
                    f"{rel}: NBL-03 markdown cell {idx} carries an "
                    f"HTML anchor (href=) - the notebook layer is "
                    f"link-free by design; lesson navigation lives in "
                    f"the .md layer and the platform serves notebooks "
                    f"standalone")
        elif cell.get("cell_type") == "code":
            # informational only: a string that never renders is not a
            # learner-facing link (see docstring - scope decision)
            if isinstance(cell.get("source"), (str, list)):
                stats[2] += len(INLINE_LINK.findall(cell_source(cell)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []
    # notebooks, md cells, code-cell link-shaped (informational), skipped
    stats = [0, 0, 0, 0]
    for path in sorted((args.root / "docs" / "notebooks").glob("*.ipynb")):
        stats[0] += 1
        scan_nb(args.root, path, findings, stats)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"notebook_link_scan: {len(findings)} findings "
          f"(NBL-01 inline/image markdown link / NBL-02 reference-style "
          f"link definition / NBL-03 HTML anchor or angle autolink; "
          f"{stats[2]} link-shaped code-cell literal(s) informational, "
          f"{stats[3]} cell(s) left to NBH-03) across {stats[0]} "
          f"notebooks / {stats[1]} markdown cells in docs/notebooks/ "
          f"(hard; born tick-692 at zero - the notebook layer carries "
          f"no links by design)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
