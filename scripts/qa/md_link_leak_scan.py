#!/usr/bin/env python3
"""Markdown-link leakage gate for the Minder Academy corpus.

ML-01  a quote-delimited string whose entire visible content is a
       markdown link (``"[https://host/path](https://host/path)"``)
       is not a URL - it is markdown link syntax that leaked into a
       string literal, almost always a URL value inside a code fence.
       A reader copying the fence gets a string whose value is the
       literal bracket-parenthesis text: the OAuth authorize url, the
       redirect_uri, the token endpoint - every consumer of the value
       receives garbage and the failure surfaces downstream at the
       provider, far from the copied line. No gate owned the class:
       the fences compile (they are ordinary string constants), the
       AST family walks calls and kwargs, not string contents, the
       fence-walking family could not see the drain lines past the
       inner example-fence parity flip, and linkcheck read the
       shapes as valid markdown links (a wrapped url resolves as a
       self-link) - syntactically legal everywhere, defect-owned
       nowhere, while sitting in a shipped OAuth example.

The scan is fence-agnostic by design: the leak class is defined by
the quote-wrapped shape itself, not by fence position, because the
corpus ships prompt/response examples where an inner ```` ```python ````
marker flips a sequential fence scanner's parity and hides exactly
these lines (UC-002's example-in-example shape is the drain site -
born census tick-675 read the whole corpus = exactly 3 sites, all in
that one OAuth example, all leaks; drained the same tick by stripping
the wrappers to the plain urls, zero line shift).

Out of the class by construction:

  - unquoted prose markdown links ``[https://host](https://host)`` -
    the QUICK-START link-list idiom, 46 sites, valid markdown; only a
    quote-delimited string enters the class.
  - plain url strings ``"https://host/path"`` - the affirmative form
    the corpus teaches everywhere.
  - labelled prose links ``[text](url)`` - normal markdown, no quote.
  - strings that CONTAIN a markdown link among other text - the regex
    demands quote, full link, quote; a partial wrapper stays silent
    (v1 partition, documented).
  - markdown link syntax with a non-http scheme (mailto:, ftp:, or a
    relative path) - the http(s) demand keeps the class at url leaks.
  - notebooks (.ipynb) are outside the md universe.

No danger-marker escape: the sibling unsafe_*/crypto escapes cover
deliberate danger teaching, but this class has no legitimate form -
a quoted markdown link is a leak in every context, teaching or not.

Hard gate (exit 1 on findings): born-at-zero after the tick-675 drain,
frozen hard from the rule's naming (the SS-01 zero-drain shape).

Run over the whole corpus:
    python scripts/qa/md_link_leak_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# a quote, a full http(s) markdown link, the same quote - the leak shape.
LEAK_RE = re.compile(r"(['\"])\[(https?://[^\]\s]+)\]\([^)]+\)\1")

FINDING = (": ML-01 markdown link syntax inside a quoted string - the "
           "value is not a URL, it is the literal [url](url) text; "
           "strip the wrapper and keep the plain url")


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    for ln, raw in enumerate(lines, 1):
        if LEAK_RE.search(raw):
            findings.append(f"{rel}:{ln}{FINDING}")


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
    print(f"md_link_leak_scan: {len(findings)} findings "
          f"(ML-01 markdown link syntax inside a quoted string) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
