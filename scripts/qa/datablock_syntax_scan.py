#!/usr/bin/env python3
"""Data-block syntax gate: every data-labeled fence parses in its format.

Policy
------
A fence labeled ``json`` promises machine-parseable JSON (DB-01); a fence
labeled ``yaml`` promises machine-parseable YAML (DB-02).  Both are checked
with their canonical parsers:

  json   json.loads(block)                 - one JSON document per fence
  yaml   list(yaml.safe_load_all(block))   - YAML streams are first-class
           valid YAML (k8s multi-doc manifests separated by ``---``)

Anything that is not pure data (prose, formulas, ``Where:`` definitions,
checklists, step traces, annotated request/response walkthroughs) lives in
an honest ``text`` fence instead of borrowing a parseable label.  Mixed
payloads are split per language, like the bash gate requires.  The check
is strict: a ``json`` fence with a ``// comment`` line fails; a ``yaml``
fence whose embedded block-scalar indentation breaks (e.g. a stray
column-0 comment inside a ConfigMap's ``|`` block) fails.

YAML parsing needs PyYAML (``import yaml``); the gate exits 2 with a clear
message if it is unavailable rather than passing silently.

Fence-aware since tick-679: the parser tracks CommonMark fence length -
the opener's marker run is captured (f_char, f_len), a closer must repeat
the opener's character in a run at least as long, and a different fence
character never closes.  A marker line that is not a valid closer is
fence CONTENT and stays in the block body, so inner 3-backtick examples
inside 4-backtick outer template blocks are never parsed as real data
(aligned with codeblock_syntax_scan's tick-678 fix).

Output
------
  datablock_syntax_scan: N findings across docs/ (M json + K yaml blocks checked)
  rel:line: DB-01 json fence does not parse: <detail>      (exit 1)
  rel:line: DB-02 yaml fence does not parse: <detail>      (exit 1)

The recorded line is the fence CONTENT start (opener line + 1), matching
codeblock_syntax_scan / bashblock_syntax_scan so editors land on the data.

Usage:
    python scripts/qa/datablock_syntax_scan.py [--root REPO_ROOT]

Exit codes: 0 = every json/yaml fence parses,
            1 = findings (mislabels or syntax errors),
            2 = PyYAML unavailable (environment problem, not a doc problem).
Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")

try:
    import yaml
except ImportError:  # environment problem, not a doc problem
    print("datablock_syntax_scan: PyYAML is required for the yaml gate "
          "(uv add pyyaml / pip install pyyaml)")
    sys.exit(2)


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2],
                        help="repository root (default: %(default)s)")
    args = parser.parse_args()
    docs_root = args.root / "docs"

    findings: list[str] = []
    n_json = n_yaml = 0

    for path in sorted(docs_root.rglob("*.md")):
        rel = path.relative_to(docs_root).as_posix()
        lines = path.read_text(encoding="utf-8").split("\n")
        in_fence = False
        f_char = ""
        f_len = 0
        lang = ""
        start = 0
        body: list[str] = []
        for i, raw in enumerate(lines):
            m = FENCE.match(raw)
            if m and not in_fence:
                run = m.group(1)
                in_fence = True
                f_char, f_len = run[0], len(run)
                lang = m.group(2).lower()
                start = i + 1
                body = []
                continue
            if in_fence:
                if m:
                    run = m.group(1)
                    ch, n = run[0], len(run)
                    if ch == f_char and n >= f_len:
                        # CommonMark: only a same-character run at
                        # least as long closes the fence
                        src = "\n".join(body)
                        if lang == "json" and src.strip():
                            n_json += 1
                            try:
                                json.loads(src)
                            except ValueError as e:
                                findings.append(
                                    "%s:%d: DB-01 json fence does not parse: %s"
                                    % (rel, start + 1, str(e).split("\n")[0]))
                        elif lang == "yaml" and src.strip():
                            n_yaml += 1
                            try:
                                list(yaml.safe_load_all(src))
                            except yaml.YAMLError as e:
                                detail = " / ".join(
                                    part.strip() for part
                                    in str(e).split("\n")[:3])
                                findings.append(
                                    "%s:%d: DB-02 yaml fence does not parse: %s"
                                    % (rel, start + 1, detail))
                        in_fence = False
                        lang = ""
                        body = []
                        continue
                    # a marker line that is not a valid closer is
                    # fence CONTENT (an inner 3-run inside a 4-outer)
                    body.append(raw)
                    continue
                body.append(raw)

    print("datablock_syntax_scan: %d findings across docs/ "
          "(%d json + %d yaml blocks checked)"
          % (len(findings), n_json, n_yaml))
    for f in findings:
        print(esc(f))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
