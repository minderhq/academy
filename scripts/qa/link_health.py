#!/usr/bin/env python3
r"""External link health for PROJECT-OMEGA (report-only listing tool).

The corpus carries ~640 clickable external URLs in prose (the link
gates verify only INTERNAL targets: anchor/file resolution). The
platform will render every one of these as a link a learner can
click - a dead arxiv ID, a taken-down YouTube video or a 404'd docs
page is exactly the kind of rot internal checks cannot see.

Scope: http(s) URLs in PROSE only (outside code fences) under
docs/ - fenced URLs are code examples (localhost, placeholders)
and are not learner-clickable. Obviously non-checkable hosts
(localhost, 127.0.0.0/8, example.com, *.local, <placeholders>)
are counted separately as not-checkable.

Classes:
  LIVES   2xx after redirects
  LIVES?  non-bot HTTP errors (5xx, odd 4xx) - spot-check queue
  DEAD    404 / 410 - real rot, the review queue
  GONE?   DNS failure / timeout / SSL error - possible rot; note
          that a CONNECTION reset on a DNS-resolving host (e.g.
          discord.gg invite links) is usually a bot/network block,
          not rot - verify invites in a browser before treating
          them as dead
  BLOCKED bot-wall statuses (403/406/429/999) - the page almost
          certainly exists, the bot is not let in; manual
          spot-check only

Report-only, exit 0 by design (a network check is nondeterministic
and must never gate a commit - same contract as date_cohort).
Run before a release or on a cadence, not per-commit:

    python scripts/qa/link_health.py --root .
    python scripts/qa/link_health.py --root . --workers 16 --timeout 10

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
import ssl
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(```|~~~)")  # CommonMark: <=3 leading spaces
URL = re.compile(r"https?://[^\s\)\]\`>'\"<]+")
FM_CLOSE = re.compile(r"^---\s*$")
NOT_CHECKABLE = re.compile(
    r"^https?://(localhost|127\.\d+\.\d+\.\d+"
    r"|(?:[^/]+\.)?example\.(com|org|net)"
    r"|[^/]*\.local|your-|<)", re.I)
BOT_STATUSES = {403, 406, 429, 999}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SSL_CTX = ssl.create_default_context()


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


def collect(root: Path) -> dict[str, tuple[str, int]]:
    """unique url -> first-seen (doc, line-no)"""
    seen: dict[str, tuple[str, int]] = {}
    for path in sorted((root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root).as_posix()
        infence = False
        for i, ln in enumerate(body_lines(text), 1):
            if FENCE.match(ln):
                infence = not infence
                continue
            if infence:
                continue
            for m in URL.finditer(ln):
                seen.setdefault(m.group(0).rstrip(".,;:!"),
                                (rel, i))
    return seen


def check(url: str, timeout: float) -> tuple[str, int | str]:
    req = urllib.request.Request(
        url, headers={"User-Agent": UA,
                      "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"},
        method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=SSL_CTX) as resp:
            return "LIVES", int(resp.status)
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return "DEAD", int(e.code)
        if e.code in BOT_STATUSES:
            return "BLOCKED", int(e.code)
        return "LIVES?", int(e.code)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        reason = getattr(e, "reason", e)
        return "GONE?", str(reason)[:60]
    except Exception as e:  # ssl.SSLError etc.
        return "GONE?", str(e)[:60]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--max-list", type=int, default=40,
                        help="cap per-class listing in the report")
    args = parser.parse_args()

    seen = collect(args.root)
    skip = {u: loc for u, loc in seen.items() if NOT_CHECKABLE.match(u)}
    todo = [u for u in seen if u not in skip]

    results: dict[str, tuple[str, int | str]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for url, res in zip(todo, pool.map(lambda u: check(u, args.timeout),
                                           todo)):
            results[url] = res

    classes: dict[str, list[str]] = defaultdict(list)
    for url, (cls, detail) in results.items():
        classes[cls].append(url)

    for cls in ("DEAD", "GONE?", "LIVES?", "BLOCKED"):
        urls = sorted(classes.get(cls, []))
        print(esc("--- %s: %d ---" % (cls, len(urls))))
        dom_count = Counter(re.match(r"https?://([^/]+)", u).group(1)
                            for u in urls)
        for d, n in dom_count.most_common(10):
            print("    %3d %s" % (n, d))
        for u in urls[:args.max_list]:
            rel, ln = seen[u]
            print(esc("  %s (%s:%d)" % (u[:90], rel, ln)))
        if len(urls) > args.max_list:
            print("    ... and %d more" % (len(urls) - args.max_list))

    print("link_health: %d prose urls (%d unique): LIVES %d, LIVES? %d, "
          "DEAD %d, GONE? %d, BLOCKED %d, not-checkable %d; "
          "report-only, exit 0 by design - network checks never gate "
          "a commit"
          % (len(seen), len(results),
             len(classes.get("LIVES", [])) + len(classes.get("LIVES?", [])) * 0,
             len(classes.get("LIVES?", [])),
             len(classes.get("DEAD", [])),
             len(classes.get("GONE?", [])),
             len(classes.get("BLOCKED", [])),
             len(skip)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
