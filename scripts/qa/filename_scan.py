#!/usr/bin/env python3
"""Filename hygiene (FN-01..06, HARD) - path segments are API.

A file name is surface that every layer downstream consumes:
git, editors, CI shells, and above all the eventual web platform,
which derives URLs and slugs from paths. Names that need quoting,
percent-encoding or case-disambiguation work here and break
elsewhere. Six rules, all mechanical, zero editorial judgment:

FN-01  within one directory, two names differing only by case -
       fine on a case-insensitive checkout (Windows/macOS), a
       silent overwrite on case-sensitive Linux CI, and an
       unresolvable pair for any tool that lowercases slugs
FN-02  a space in a path segment - becomes %20 in URLs, must be
       quoted in every shell command, breaks naive linkers
FN-03  a reserved or URL-significant character in a segment:
       the 9 Windows-invalid chars (angle brackets, colon,
       quote, slash and backslash, pipe, question and
       asterisk) plus the URL-semantics set  % # & ; = @ $
       (percent-encoding bugs, fragment/query smuggling).
       Note: ! ( ) { } [ ] ' ` ~ ^ + , are OUT - they are
       shell-irksome but URL-legal and some are legitimate
       in tooling config names; the gate refuses the chars
       that actually break layers, not taste
FN-04  non-ASCII in a segment - the corpus language is English;
       Unicode names render differently across filesystems,
       terminals and CDN layers, and mint non-ASCII URLs
FN-05  a segment that is not equal to its own strip() or ends
       with '.' - trailing dots/spaces are unrepresentable on
       Windows and silently truncate on older tooling
FN-06  a relative path longer than 200 chars - headroom below
       the Windows MAX_PATH (260) cliff, which still bites
       checkouts inside deep tool directories

Scope: every file under the repo root, EXCEPT well-known
generated/vendor trees (.git, .venv, node_modules, __pycache__,
pytest/mypy/ruff caches, dist, build, .ipynb_checkpoints) and
tool-local state (.claude) at ANY depth - those are machine
output, not authored surface; the ignore check runs per path
segment, not just at the root (scripts/qa/__pycache__ would
otherwise slip through).

Born tick-492 born-at-zero: 597 tracked files censused, all six
rules clean. The gate guards the platform era where new
contributions (and copied-in assets) arrive with names chosen
for one filesystem and consumed on five.

Run over the whole tree:
    python scripts/qa/filename_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build",
    ".ipynb_checkpoints", ".tox", ".eggs", "site-packages", ".claude",
}
WIN_INVALID = set('<>:"/\\|?*')
URL_SIGNIFICANT = set("%#&;=@$")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_files = 0
    # FN-01 index: (parent dir, lowercase name) -> [display names]
    seen: dict[tuple[str, str], set[str]] = {}
    for path in sorted(args.root.rglob("*")):
        relparts = path.relative_to(args.root).parts
        if any(part in IGNORE_DIRS for part in relparts):
            continue
        if not path.is_file():
            continue
        n_files += 1
        rel = path.relative_to(args.root).as_posix()
        name = relparts[-1]
        parent = relparts[:-1]
        seen.setdefault((parent, name.lower()), set()).add(name)
        for seg in relparts:
            if " " in seg:
                findings.append(
                    "FN-02 %s: space in path segment - spaces become "
                    "%%20 in URLs and must be quoted in every shell "
                    "command; use hyphens" % rel)
                break
        for seg in relparts:
            bad = sorted(set(seg) & WIN_INVALID | set(seg) & URL_SIGNIFICANT)
            if bad:
                findings.append(
                    "FN-03 %s: reserved/URL-significant char(s) in path "
                    "segment: %r - these are invalid on Windows or mint "
                    "ambiguous URLs (see docstring for the legal set)"
                    % (rel, "".join(bad)))
        for seg in relparts:
            try:
                seg.encode("ascii")
            except UnicodeEncodeError:
                findings.append(
                    "FN-04 %s: non-ASCII character in path segment - "
                    "the corpus language is English; Unicode names mint "
                    "non-ASCII URLs and render differently across "
                    "filesystems" % rel)
        for seg in relparts:
            if seg != seg.strip() or seg.endswith("."):
                findings.append(
                    "FN-05 %s: segment has edge whitespace or a trailing "
                    "dot - unrepresentable on Windows, silently "
                    "truncated by older tooling" % rel)
        if len(rel) > 200:
            findings.append(
                "FN-06 %s: %d-char path - keep paths under 200, "
                "headroom below the Windows MAX_PATH cliff"
                % (rel, len(rel)))
    # FN-01 after the walk: report each colliding pair once
    for (parent, low), names in seen.items():
        if len(names) > 1:
            rel = "/".join(parent) if parent else low
            findings.append(
                "FN-01 %s: case-only name collision in one directory: "
                "%s - a silent overwrite on case-sensitive CI and "
                "unresolvable for slug tools" % (rel, ", ".join(sorted(names))))
    findings.sort()
    for f in findings:
        print("  " + esc(f))
    print("filename_scan: %d files inspected; %d FN findings - hard "
          "(FN-01..06 filename hygiene; path segments are API - git, "
          "shells and the web platform all consume them; born tick-492 "
          "born-at-zero, 597 tracked files censused clean; see docstring)"
          % (n_files, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
