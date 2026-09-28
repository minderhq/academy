#!/usr/bin/env python3
"""In-document anchor gate for the PROJECT-OMEGA corpus.

Verifies every same-document (#...) and cross-file (file.md#...) anchor
against a GitHub-accurate slugger, so anchors that render fine in a local
preview but 404 on GitHub are caught before they ship.

Slugger rules (mirrors GitHub): trim -> lowercase -> emoji-shortcode
substitution -> strip [^\\w\\s-] (dots and colons vanish) -> every
whitespace char becomes one hyphen with NO collapsing -> duplicate slugs
get -1/-2 suffixes, first occurrence bare. Example: "A 2.5G Apartment"
-> case-study-a-25g-apartment-star-network.

Hard gate (exit 1 on any finding that is not on the known-allowlist):
the two inline-code documentation examples below are intentional
`#section` placeholders in meta-documents and are excluded by rule.
If an allowlisted finding disappears, that is reported as a regression
hint (the example was rewritten) but still exits 0.

Baseline (2026-09-28): 458 files, broken anchors: exactly the 2 allowed.
Materialized from the formerly repo-external anchor_verify_omega.py
temp script (its one-off trailing-whitespace / heading-jump spot checks
were dropped as non-gate diagnostics).

Usage:
    python scripts/qa/anchor_check.py [--root REPO_ROOT]

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter

FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FM = re.compile(r"^---\s*$")
SHORT_RE = re.compile(r":([a-z0-9_+\-]+):")
CODES = {":star3:": "\U0001F31F", ":star:": "⭐", ":rotating_light:": "\U0001F6A8",
         ":rocket:": "\U0001F680", ":memo:": "\U0001F4DD", ":link:": "\U0001F517",
         ":checkered_flag:": "\U0001F3C1", ":trophy:": "\U0001F3C6", ":book:": "\U0001F4D6"}

# Corpus scope: skip virtualenvs and tool dirs - a fresh `uv sync` would
# otherwise leak installed package markdown into the gate (casecheck model).
SKIP_DIRS = {".git", ".claude", "node_modules", "__pycache__", ".venv", "venv"}

# Known-intentional broken anchors (inline-code docs examples, dokunulmaz).
ALLOWED = {
    ("docs/00-META/CROSS-REFERENCE-GUIDELINES.md", "#section"),
    ("docs/00-META/DOCUMENT-TEMPLATE.md", "#section-id"),
}


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def gh_slug(text: str) -> str:
    s = text.strip().lower()
    s = SHORT_RE.sub(lambda m: CODES.get(m.group(0), ""), s)
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s", "-", s)  # one hyphen per whitespace char (GitHub slugger)
    return s


def headings_with_slugs(text: str):
    """Yield heading texts outside frontmatter and fences."""
    heads = []
    in_f, in_fm, fm_n = False, text.startswith("---"), 0
    for ln in text.splitlines():
        if in_fm:
            if FM.match(ln):
                fm_n += 1
                in_fm = fm_n != 2
            continue
        if FENCE.match(ln):
            in_f = not in_f
            continue
        if in_f:
            continue
        m = HEADING.match(ln)
        if m:
            heads.append(m.group(2))
    return heads


def anchor_set(text: str) -> set:
    raw = [gh_slug(t) for t in headings_with_slugs(text)]
    cnt = Counter(raw)
    seen = Counter()
    out = set()
    for s in raw:
        k = seen[s]
        seen[s] += 1
        out.add(s if k == 0 else f"{s}-{k}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=str, default=None,
                        help="repository root (default: two levels up from this script)")
    args = parser.parse_args()
    root = os.path.abspath(args.root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    files = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for n in fn:
            if n.endswith(".md"):
                files.append(os.path.join(dp, n))

    cache = {}

    def slugs_for(trel):
        if trel not in cache:
            with open(os.path.join(root, trel), encoding="utf-8", newline="") as f:
                cache[trel] = anchor_set(f.read())
        return cache[trel]

    bad = []
    for p in files:
        rel = os.path.relpath(p, root).replace("\\", "/")
        with open(p, encoding="utf-8", newline="") as f:
            lines = f.read().splitlines()
        in_f = False
        in_fm = bool(lines) and lines[0].strip() == "---"
        fm_n = 0
        for i, ln in enumerate(lines, 1):
            if in_fm:
                if FM.match(ln.strip()):
                    fm_n += 1
                    in_fm = fm_n != 2
                continue
            if FENCE.match(ln.strip()):
                in_f = not in_f
                continue
            if in_f:
                continue
            for m in LINK.finditer(ln):
                url = m.group(1)
                if url.startswith("#"):
                    frag, trel = url[1:], rel
                elif "#" in url and not url.startswith("http"):
                    path, frag = url.rsplit("#", 1)
                    tf = os.path.normpath(os.path.join(os.path.dirname(p), path))
                    if not os.path.exists(tf):
                        continue
                    trel = os.path.relpath(tf, root).replace("\\", "/")
                else:
                    continue
                if frag and frag not in slugs_for(trel):
                    bad.append((rel, i, url))

    unexpected = [b for b in bad if (b[0], b[2]) not in ALLOWED]
    missing_allowed = [a for a in ALLOWED if a not in {(b[0], b[2]) for b in bad}]

    print(esc("files: %d" % len(files)))
    print(esc("broken anchors: %d" % len(bad)))
    for r in bad:
        print(esc("  %s:%d  %s" % r))
    if missing_allowed:
        print(esc("NOTE: %d allowlisted anchor(s) no longer broken - update the ALLOWED set" % len(missing_allowed)))
        for a in missing_allowed:
            print("  ", esc(str(a)))
    print("anchor_check: %d broken anchors (%d allowed, %d unexpected) -> %s"
          % (len(bad), len(bad) - len(unexpected), len(unexpected),
             "PASS" if not unexpected else "FAIL"))
    return 0 if not unexpected else 1


if __name__ == "__main__":
    sys.exit(main())
