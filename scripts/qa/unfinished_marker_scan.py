#!/usr/bin/env python3
"""unfinished-content marker gate for the Minder Academy corpus.

UM-01  a prose line (outside any code fence, inline code scrubbed)
       must not carry an unfinished-content marker: "coming soon",
       "under construction", "to be written", "to be added", "work in
       progress", or an uppercase TODO/TBD/FIXME. Born from the
       tick-276 census: 108 raw matches corpus-wide and every one
       landed in a legitimate class - starter-code "# TODO:" exercise
       prompts (the convention notebooks/README.md codifies:
       educational prompts, not incomplete tasks), a git-stash message
       example, a git-grep teaching example, a review bot whose job is
       DETECTING TODOs, and a todo-app exercise whose domain objects
       are todos. Code fences are invisible to this gate by design -
       that is where every legitimate idiom lives, and the fence
       toggle + inline-code scrub is the shared extraction model.
       Fence markers may carry a ">" blockquote prefix - callout-
       embedded code (e.g. "> ```python") is fenced too.
       Fence state follows CommonMark (tick-678 canon): the opener
       captures its marker run, a closer repeats the opener's
       character in a run at least as long, a different fence
       character never closes, and a marker line that is not a valid
       closer is fence content - 4-outer template blocks (FLASHCARDS
       Notebook-Template, DOCUMENT-TEMPLATE) are content, their
       interiors never reach the prose scan.
       TODO/TBD/FIXME match uppercase only: lowercase "todo" is the
       exercise domain noun ("todo list manager"), the marker idiom is
       always shouted.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-276) - the
gate locks the corpus against future unfinished-content rot, the same
class whose draft "coming soon" rows were already swept once in the
link era (tick-68) and could come back through prose.

Run over the whole corpus:
    python scripts/qa/unfinished_marker_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Fence markers may carry a ">" blockquote prefix - callout-embedded code
# (e.g. "> ```python") is fenced code and must toggle the fence state too.
FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
INLINE_CODE_RE = re.compile(r"`[^`]*`")

# (pattern, label) pairs - each finding reports the first matching rule.
RULES = [
    (re.compile(r"coming soon", re.IGNORECASE), "coming soon"),
    (re.compile(r"under construction", re.IGNORECASE), "under construction"),
    (re.compile(r"to be written", re.IGNORECASE), "to be written"),
    (re.compile(r"to be added", re.IGNORECASE), "to be added"),
    (re.compile(r"work in progress", re.IGNORECASE), "work in progress"),
    (re.compile(r"\b(?:TODO|TBD|FIXME)\b"), "shouted TODO/TBD/FIXME"),
]


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    in_fence: tuple[str, int] | None = None
    for ln, raw in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        m = FENCE_RE.match(raw)
        if m:
            f_char, f_len = m.group(1)[0], len(m.group(1))
            if in_fence:
                if f_char == in_fence[0] and f_len >= in_fence[1]:
                    in_fence = None
            else:
                in_fence = (f_char, f_len)
            continue
        if in_fence is None:
            prose = INLINE_CODE_RE.sub("", raw)
            for pat, label in RULES:
                if pat.search(prose):
                    findings.append(
                        f"{rel}:{ln}: UM-01 unfinished-content marker "
                        f"({label}); prose only - fenced code is invisible "
                        f"by design")
                    break


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    n_files: set[str] = set()
    for path in sorted(docs.rglob("*.md")):
        try:
            before = len(findings)
            scan_file(args.root, path, findings)
            if len(findings) > before:
                n_files.add(path.relative_to(args.root).as_posix())
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"unfinished_marker_scan: {len(findings)} findings "
          f"(UM-01 unfinished-content markers in prose: coming soon / "
          f"under construction / to be written / to be added / work in "
          f"progress / shouted TODO-TBD-FIXME) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
