#!/usr/bin/env python3
"""html_comment_scan (HC-01) - the HTML-COMMENT RENDER-VISIBILITY
dimension across docs markdown.

CommonMark turns an HTML comment outside a fenced code block into a
raw-HTML block: everything from the opener to the closer is INVISIBLE
on the platform. An editorial note, a TODO, or commented-out prose
never reaches the learner - silent content loss, the same invisibility
class render_hygiene_check's HTML_TAG targets for visible raw tags.
HTML_TAG = <(/?[a-zA-Z]...) cannot match <!-- (bang is not a letter),
so the comment class was invisible to the whole fleet until this gate.

Born tick-700 at ZERO findings rc=0 over the real corpus (408 docs);
the census measured 18 HTML comments in 4 files and ALL 18 sit inside
fenced code blocks (template teaching, diagram annotations, HTML file
examples) - the corpus convention "comments only inside fences" is
real, and the gate locks it.

The one rule HC-01: a line outside every fence whose inline-code
spans are stripped carries the raw comment opener <!-- (a comment
opens the moment the four characters appear - <!--- is also a legal
CommonMark opener and carries the prefix; a multiline comment is
caught at its opener line, which is where the invisibility starts).

Measurement rules ARE the judgment, each measured from the corpus:
- fence-aware line-state walk (a comment inside a bash/html fence is
  a teaching example - fenced content renders literally, HC stays
  silent);
- inline-code spans stripped before the opener check (a backticked
  <!-- renders literally and is safe content, the TH-01 span lesson);
- front-matter blocks exempt (body_lines walk - no comments live in
  YAML keys, and FM has no render surface);
- closing --> alone carries no opener and never fires (the opener is
  where invisibility starts; a stray closer is harmless text);
- a 4-space-indented line is an indented code block in CommonMark -
  the comment renders LITERALLY and the content stays visible, so
  the line is skipped (measured: the corpus carries 0 such lines).

NBH owns notebook cells, TH owns table shape.

Usage: python scripts/qa/html_comment_scan.py [--root PATH]
Exit 0 = clean, exit 1 = findings.
"""
import argparse
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
FM_CLOSE = re.compile(r"^---\s*$")
INLINE = re.compile(r"`[^`]*`")
OPENER = "<!--"

FINDING = ("HC-01 %s:%d: raw HTML comment outside a fence - "
           "everything through the closer renders invisibly on the "
           "platform; move the example into a fenced block or delete "
           "the note")


def body_lines(text):
    """Skip a leading YAML front-matter block."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return lines
    for i in range(1, len(lines)):
        if FM_CLOSE.match(lines[i]):
            return lines[i + 1:]
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    findings = []
    docs = 0
    n_fenced = 0
    n_indented = 0
    for path in sorted(Path(args.root, "docs").rglob("*.md")):
        docs += 1
        rel = path.relative_to(args.root).as_posix()
        lines = body_lines(path.read_text(encoding="utf-8"))
        in_fence = False
        f_char = None
        f_len = 0
        for idx, line in enumerate(lines):
            m = FENCE.match(line)
            if m:
                ch = m.group(1)[0]
                ln = len(m.group(1))
                if not in_fence:
                    in_fence, f_char, f_len = True, ch, ln
                elif ch == f_char and ln >= f_len:
                    in_fence = False
                continue
            if in_fence:
                n_fenced += 1
                continue
            if line.startswith("    ") and not line.strip() == "":
                # CommonMark: 4-space indent is an indented code block -
                # the comment renders LITERALLY, content visible, no loss
                n_indented += 1
                continue
            clean = INLINE.sub("", line)
            if OPENER in clean:
                findings.append(FINDING % (rel, idx + 1))
    print("HC: %d docs, %d fenced lines walked, %d indented-comment "
          "lines skipped, %d findings across docs/"
          % (docs, n_fenced, n_indented, len(findings)))
    for f in findings:
        print(f)
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
