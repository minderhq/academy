#!/usr/bin/env python3
"""External link rot check for the PROJECT-OMEGA corpus (report-only).

Complements linkcheck.py, which covers relative targets on disk. This tool
takes the http/https subset of the SAME link model (linkcheck's MD_LINK,
naive fence toggle, inline-code scrub - the fence-sangham lesson: reuse the
gates' exact extraction, never an ad-hoc one) and probes each unique URL
over the network.

Why report-only and NOT registered in quality_report GATES: the scorecard
is the fast offline answer ("where does the corpus stand today?"); a
network probe makes it slow and flaky. Run this ad hoc / on a schedule:

    python scripts/qa/link_rot_check.py            # full corpus
    python scripts/qa/link_rot_check.py --limit 10 # smoke test

Classes:
    OK        2xx final status after redirects
    REDIRECT  final status ok but the URL moved (informational)
    DEAD      404/410 - the rot this tool exists to find
    DENIED    403/429/999 - bot-walls; retried with a browser UA (httpx,
              then curl's TLS stack - walls fingerprint TLS, not just the
              UA); only stays DENIED when every retry is denied too
    SERVER    5xx - server-side trouble, retry later
    ERROR     network/DNS/timeout after one retry
    TEMPLATE  placeholder/example idiom URLs (your-username, your-org,
              yourapp.com) - they resolve once the repo is published or
              are deliberate teaching placeholders, so not rot

mailto:, anchors and local/example URLs (localhost, 127.0.0.1,
example.com/org/net, *.test, *.local) are out of scope. Exit 0 always.

Bare URLs (tick-241 lesson): linkcheck's MD_LINK model only sees
``[text](url)``; plain URLs in prose are invisible - which is how 3
stale ollama.com/docs refs survived earlier sweeps. Harvest now also
takes bare http(s) URLs outside MD_LINK spans (same fence toggle and
inline-code scrub; fenced code stays out of model, per the gates'
contract). URL-adjacent trailing punctuation is stripped.

Baseline (2026-09-28, first run): see the summary line this prints.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import httpx

SKIP_DIRS = {".git", "node_modules"}
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BARE_URL = re.compile(r"https?://[^\s<>()\[\]`\"']+")
TRAILING_PUNCT = ".,;:!?"
INLINE_CODE = re.compile(r"`[^`]+`")
FENCE = re.compile(r"^\s*(```|~~~)")
LOCAL_URL = re.compile(
    r"(localhost|127\.0\.0\.1|0\.0\.0\.0|example\.(?:com|org|net)|\.test[/:]|\.local[/:])",
    re.IGNORECASE,
)
UA = "PROJECT-OMEGA-link-rot-check/1.0 (curriculum QA; contact: repo owner)"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
PLACEHOLDER_IDIOMS = ("your-username", "your-org", "yourapp.com")
DEAD = {404, 410}
DENIED = {401, 403, 429, 999}


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def md_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)


def harvest(root):
    """url -> [rel:line] using linkcheck's exact extraction model."""
    refs = defaultdict(list)
    for src in md_files(root):
        in_fence = False
        try:
            with open(src, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if FENCE.match(line):
                        in_fence = not in_fence
                        continue
                    if in_fence:
                        continue
                    for m in MD_LINK.finditer(INLINE_CODE.sub("", line)):
                        url = m.group(1)
                        if url.startswith(("http://", "https://")) and not LOCAL_URL.search(url):
                            rel = os.path.relpath(src, root).replace("\\", "/")
                            refs[url].append(f"{rel}:{i}")
                    # bare URLs (tick-241 lesson): skip matches inside MD_LINK spans
                    scrubbed = INLINE_CODE.sub("", line)
                    spans = [m.span() for m in MD_LINK.finditer(scrubbed)]
                    for m in BARE_URL.finditer(scrubbed):
                        if any(a <= m.start() < b for a, b in spans):
                            continue
                        url = m.group(0).rstrip(TRAILING_PUNCT)
                        if not LOCAL_URL.search(url):
                            rel = os.path.relpath(src, root).replace("\\", "/")
                            refs[url].append(f"{rel}:{i}")
        except (OSError, UnicodeDecodeError):
            continue
    return refs


def _curl_probe(url: str) -> int | None:
    """Last-resort bot-wall check through curl's TLS stack.

    tick-244 measured that httpx with a browser UA still gets 403 where
    curl with the SAME headers gets 200 (wikipedia, pytorch, realpython):
    these walls fingerprint the TLS stack, not just the UA. curl ships
    with Windows 10+ and every dev environment; if it is absent or
    fails, return None and the URL stays DENIED (report-only - never
    invents a verdict it cannot measure).
    """
    curl = shutil.which("curl")
    if not curl:
        return None
    try:
        out = subprocess.run(
            [curl, "-s", "-o", os.devnull, "-w", "%{http_code}",
             "-A", BROWSER_UA, "-L", "--max-time", "20", url],
            capture_output=True, timeout=25)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    try:
        return int(out.stdout.decode("ascii", "ignore").strip()[-3:])
    except ValueError:
        return None


def _denied_second_chance(client: httpx.Client, url: str) -> tuple[str, str] | None:
    """Bot-wall retry: browser UA over httpx, then curl (İKİNCİ-KANAÇ).

    tick-242 proved pytorch/realpython/docker 403 under the tool UA while
    the same URLs answered 200 to curl with browser headers - a tool-UA
    403 is a bot-wall far more often than it is rot, and a reader's
    browser is the thing the link must work for. Returns (class, note)
    when a retry changed the verdict, None to keep DENIED.
    """
    code, final = None, ""
    try:
        timeout = client.timeout.read or 10.0
        with httpx.Client(headers={"User-Agent": BROWSER_UA},
                          timeout=timeout, follow_redirects=True) as bc, \
                bc.stream("GET", url) as r:
            code, final = r.status_code, str(r.url)
    except (httpx.TransportError, httpx.HTTPError):
        pass
    if code in DEAD:
        return "DEAD", f"HTTP {code} under browser UA"
    if code is not None and code < 400:
        note = f"bot-wall under tool UA; browser-UA HTTP {code}"
        if final.rstrip("/") != url.rstrip("/"):
            note += f" (moved to {final})"
        return "OK", note
    ccode = _curl_probe(url)
    if ccode is not None and ccode in DEAD:
        return "DEAD", f"HTTP {ccode} under curl browser UA"
    if ccode is not None and ccode < 400:
        return "OK", f"bot-wall under tool UA; cleared via curl (HTTP {ccode})"
    return None


def probe(client: httpx.Client, url: str) -> tuple[str, str]:
    """Return (class, note) for one URL. GET streamed: status without the body."""
    if any(p in url for p in PLACEHOLDER_IDIOMS):
        return "TEMPLATE", "placeholder/example idiom"
    for attempt in (1, 2):
        try:
            with client.stream("GET", url) as r:
                code = r.status_code
                if r.has_redirect_location and r.next_request is None and 300 <= code < 400:
                    pass
                final = str(r.url)
            if code in DEAD:
                return "DEAD", ""
            if code in DENIED:
                second = _denied_second_chance(client, url)
                if second is not None:
                    return second  # bot-wall cleared (or really dead) under browser UA
                return "DENIED", f"HTTP {code} (browser-UA retry too)"
            if 500 <= code:
                if attempt == 1:
                    continue
                return "SERVER", f"HTTP {code}"
            if code != 200:
                return "OK", f"HTTP {code}"  # non-200 2xx/3xx terminal: informational
            if final.rstrip("/") != url.rstrip("/"):
                return "REDIRECT", final
            return "OK", ""
        except (httpx.TransportError, httpx.HTTPError) as e:
            if attempt == 1:
                continue
            reason = type(e).__name__
            detail = str(e)[:60]
            return ("TIMEOUT" if isinstance(e, httpx.TimeoutException) else "ERROR",
                    f"{reason}: {detail}" if detail else reason)
    return "ERROR", "unreachable"  # pragma: no cover


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=str, default=None)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--concurrency", type=int, default=12)
    parser.add_argument("--limit", type=int, default=0,
                        help="probe only the first N unique urls (smoke test)")
    args = parser.parse_args()
    root = args.root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    refs = harvest(root)
    urls = sorted(refs, key=lambda u: (-len(refs[u]), u))
    if args.limit:
        urls = urls[: args.limit]

    counts = defaultdict(int)
    notes = {}  # url -> (class, note)
    with httpx.Client(
        timeout=httpx.Timeout(args.timeout),
        follow_redirects=True,
        headers={"User-Agent": UA, "Accept": "*/*"},
    ) as client:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            for url, (cls, note) in zip(urls, pool.map(lambda u: probe(client, u), urls)):
                counts[cls] += 1
                if cls != "OK":
                    notes[url] = (cls, note)

    order = ["DEAD", "ERROR", "TIMEOUT", "SERVER", "DENIED", "REDIRECT", "TEMPLATE"]
    for cls in order:
        bucket = [(u, notes[u]) for u in urls if notes.get(u, ("", ""))[0] == cls]
        if not bucket:
            continue
        print(f"\n== {cls} ({len(bucket)}) ==")
        for url, (_, note) in bucket:
            locs = ", ".join(refs[url][:3]) + (" ..." if len(refs[url]) > 3 else "")
            print(f"  {url}" + (f"  [{note}]" if note else ""))
            print(f"      {locs}")

    print(
        "\nlink_rot_check: %d external urls, %d ok, %d redirect, %d dead, "
        "%d denied, %d server, %d error, %d timeout, %d template -> REPORT (exit 0)"
        % (len(urls), counts["OK"], counts["REDIRECT"], counts["DEAD"],
           counts["DENIED"], counts["SERVER"], counts["ERROR"], counts["TIMEOUT"],
           counts["TEMPLATE"])
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
