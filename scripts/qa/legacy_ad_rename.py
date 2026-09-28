#!/usr/bin/env python3
"""legacy_ad_rename.py - rename the legacy repo token `ai-engineering-curriculum`.

Case-aware, context-determined mapping (sampled via legacy_ad_scan.py):

  namespace-line   `namespace: ai-engineering-curriculum`  -> project-omega   (RFC 1123)
  url-segment      preceded by `/` inside a URL            -> project-omega   (conventional)
  compound-id      followed by `-` (docker nets, conda envs,
                   container names)                        -> project-omega   (must be lowercase)
  hostname         followed by `.` (…curriculum.local)     -> project-omega
  default          paths (~/…, …/docs) and free text
                   (titles, banners, comments, FastAPI…)   -> PROJECT-OMEGA

Dry-run by default; `--apply` writes the files. Skips this script and
legacy_ad_scan.py (the survey tool must keep matching the token).
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
TOKEN = "ai-engineering-curriculum"
SKIP = {"scripts/qa/legacy_ad_rename.py", "scripts/qa/legacy_ad_scan.py"}
GLOBS = ["*.md", "*.yml", "*.yaml", "*.js", "*.py"]

NAMESPACE_RE = re.compile(r"^\s*(namespace:\s*)" + re.escape(TOKEN) + r"\s*$")

SYSTEM_TARGETS = Counter()
files_changed = 0


def map_line(line: str) -> tuple[str, str]:
    """Return (new_line, class_of_first_replacement) - all replacements in one line share rules."""
    out = []
    cls = None
    i = 0
    while True:
        j = line.find(TOKEN, i)
        if j < 0:
            out.append(line[i:])
            break
        prev = line[j - 1] if j > 0 else ""
        nxt = line[j + len(TOKEN)] if j + len(TOKEN) < len(line) else ""
        if NAMESPACE_RE.match(line):
            rep, cls = "project-omega", "namespace-line"
        elif prev == "/":
            rep, cls = "project-omega", "url-segment"
        elif nxt in "-.":
            rep, cls = "project-omega", "compound-id" if nxt == "-" else "hostname"
        else:
            rep, cls = "PROJECT-OMEGA", "default"
        out.append(line[i:j])
        out.append(rep)
        i = j + len(TOKEN)
    return "".join(out), cls or "none"


def main() -> None:
    global files_changed
    apply = "--apply" in sys.argv
    total = Counter()
    for pattern in GLOBS:
        for path in sorted(ROOT.rglob(pattern)):
            rel = path.relative_to(ROOT).as_posix()
            if ".git" in path.parts or rel in SKIP:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                print(f"warn: non-utf8 skipped: {rel}")
                continue
            if TOKEN not in text:
                continue
            new_lines, hits = [], Counter()
            for line in text.split("\n"):
                if TOKEN in line:
                    new_line, cls = map_line(line)
                    hits[cls] += 1
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)
            if hits:
                total.update(hits)
                files_changed += 1
                print(f"{rel}: {dict(hits)}")
                if apply:
                    path.write_text("\n".join(new_lines), encoding="utf-8")

    print()
    print("class totals:", dict(total))
    print("files:", files_changed, " mode:", "APPLY" if apply else "DRY-RUN")
    if apply:
        print("done - re-run scripts/qa/legacy_ad_scan.py to confirm zero remaining")


if __name__ == "__main__":
    main()
