#!/usr/bin/env python3
"""Fence-language lock (FL-01..03, HARD) for PROJECT-OMEGA.

Every fenced code block in docs/ must declare its language from the
accepted vocabulary. A platform renders, highlights and classifies
code blocks by that tag; a bare ``` is a block the renderer cannot
classify and the learner cannot skim-predict, and a typo'd tag
(`pyton`) silently drops highlighting with nothing to catch it.
linkcheck walks links, fence_exec_gate executes python fences - but
nothing pinned the one tag every fence carries.

The scan is CommonMark fence-aware: a fence opens on 3+ backticks
or tildes and closes on the same character at >= the opening width
with nothing but whitespace after (so ````markdown templates may
embed ``` fences as literal content without confusing the toggle).

FL-01  a fence opener with no language tag.
FL-02  a fence opener whose tag is outside the accepted vocabulary
       (a new real language joins by amending LANGS, never by
       slipping through).
FL-03  a fence still open at end of file - everything after it is
       literal content, so the doc's remaining structure is lost to
       the renderer.

Front matter is exempt; body lines only. Born tick-606 from a
4258-fence census across 408 docs: 22 languages (python 1860,
text 1124, bash 734, yaml 289, markdown 86, mermaid 54, json 20,
powershell 18, dockerfile 18, nginx 12, cypher 10, cuda 7, toml 4,
html 4, typescript 4, tsx 3, promql 3, sql 2, cpp 2, cron 2,
gitignore 1, c 1), zero bare openers, zero off-vocabulary tags,
zero unclosed fences - the zero-drain shape: the class froze at the
rule the moment it was named.

Run over the whole corpus:
    python scripts/qa/fence_lang_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
FM_CLOSE = re.compile(r"^---\s*$")

LANGS = frozenset({
    "python", "text", "bash", "yaml", "markdown", "mermaid", "json",
    "powershell", "dockerfile", "nginx", "cypher", "cuda", "toml",
    "html", "typescript", "tsx", "promql", "sql", "cpp", "cron",
    "gitignore", "c",
})


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()

    findings: list[str] = []
    n_fences = n_docs = 0
    for path in sorted((root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root).as_posix()
        open_fence: tuple[str, int] | None = None
        for i, ln in enumerate(body_lines(text), 1):
            m = FENCE.match(ln)
            if not m:
                continue
            fence = m.group(2)
            ch, w = fence[0], len(fence)
            info = m.group(3).strip()
            if (open_fence is not None and ch == open_fence[0]
                    and w >= open_fence[1] and not info):
                open_fence = None
                continue
            if open_fence is not None:
                continue  # literal content inside an open fence
            open_fence = (ch, w)
            n_fences += 1
            if not info:
                findings.append(
                    "FL-01 %s:%d bare %s fence (no language tag)"
                    % (rel, i, ch * 3))
            else:
                tag = info.split()[0]
                if tag not in LANGS:
                    findings.append(
                        "FL-02 %s:%d fence tag `%s` outside the "
                        "accepted vocabulary" % (rel, i, tag))
        if open_fence is not None:
            findings.append(
                "FL-03 %s: fence opened and never closed (unclosed "
                "at end of file)" % rel)
        n_docs += 1
    for f in findings:
        print("  " + esc(f))
    print("fence_lang_scan: %d fences in %d docs scanned; "
          "%d FL findings - all hard (every code block declares its "
          "language from the accepted vocabulary; born tick-606 from "
          "a 4258-fence census across 408 docs, 22 languages, "
          "zero-drain)" % (n_fences, n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
