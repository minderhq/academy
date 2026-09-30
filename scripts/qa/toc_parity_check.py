"""TOC-parity check (TP-01, tick-433): for every doc with a
Table-of-Contents section, every H2 heading that is neither chrome
nor already linked must have a TOC bullet - the missing-entry
direction (a TOC entry pointing at no heading is anchor_check's
job, TP-02).  Matching is HREF-level: a bullet counts for the
heading whose anchor_check gh_slug equals its href, which covers
shortened TOC texts (IND 'Part 1' style) and emoji-prefix slugs
(VOLUME statistics/next-steps style).  A TOC never links to its
own heading, so 'Table of Contents' is dropped from the missing
set.  Triage verdict: chrome sections (next steps, references,
abstract, ...) are accepted as outside-the-TOC texture - their
counts are informational only; a content gap (a real body section
with no TOC bullet) is a platform-nav defect with baseline 0 as of
tick-433 (18 files / 25 bullets drained); any content gap on a
future tick is a review signal, fix by merge-only-add next to the
slug-nearest existing bullet.  Same length-aware fence model as
the other census gates.  Report mode - exit 0 by design.  ASCII
prints only."""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "docs"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from anchor_check import gh_slug  # noqa: E402  (slug parity)

FENCE_RE = re.compile(r"^\s*(?:>\s*)?(`{3,})([\w+-]*)\s*$")
HEAD_RE = re.compile(r"^(#{1,6}) (.+?)\s*$")
BULLET_RE = re.compile(r"^\s*[-*] \[([^\]]+)\]\(#([^)]*)\)")
CHROME = {
    "table of contents", "learning objectives", "abstract",
    "summary", "references", "related documents", "related topics",
    "next steps", "assessment", "experiment", "experiments",
    "prerequisites",
}

n_files_with_toc = 0
n_content_gap = 0
chrome_hist: Counter[str] = Counter()
rows: list[tuple[str, str, list[str], int]] = []

for path in sorted(ROOT.rglob("*.md")):
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except (UnicodeDecodeError, OSError):
        continue
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    state = 0
    h2s: list[str] = []
    hrefs: set[str] = set()
    in_toc = False
    for raw in lines[start:]:
        m = FENCE_RE.match(raw)
        if m:
            ticks, lang = len(m.group(1)), m.group(2)
            if state and not lang and ticks >= state:
                state = 0
            elif not state:
                state = ticks
            continue
        if state:
            continue
        hm = HEAD_RE.match(raw)
        if hm:
            level, text = len(hm.group(1)), hm.group(2).strip()
            in_toc = ("table of contents" in text.lower()
                      and level <= 3)
            if level == 2:
                h2s.append(text)
            continue
        if in_toc:
            bm = BULLET_RE.match(raw)
            if bm:
                hrefs.add(bm.group(2).strip())
    if not h2s or not hrefs:
        continue
    n_files_with_toc += 1
    head_slugs = {gh_slug(t) for t in h2s}
    missing = [t for t in h2s
               if gh_slug(t) not in hrefs
               and t.lower() != "table of contents"]
    content = [t for t in missing if t.lower() not in CHROME]
    chrome = [t for t in missing if t.lower() in CHROME]
    for t in chrome:
        chrome_hist[t.lower()] += 1
    if content:
        n_content_gap += 1
        rel = path.relative_to(ROOT).as_posix()
        cls = ("lesson" if re.match(r"^\d{4}-", path.name)
               else "readme" if path.name.upper() == "README.MD"
               else "meta-resource" if rel.startswith("00-META")
               else "other")
        rows.append((rel, cls, content, len(chrome)))

print(f"toc_parity_check: files-with-TOC={n_files_with_toc} "
      f"content-gaps={n_content_gap} "
      f"(TP-01: every non-chrome H2 has a TOC bullet, href-level; "
      f"chrome sections are accepted outside-the-TOC texture - "
      f"counts informational; baseline content-gaps=0 since "
      f"tick-433, a content gap on a future tick is a review "
      f"signal - fix merge-only-add next to the slug-nearest "
      f"existing bullet) across docs/")
print("chrome-gap histogram (accepted texture, informational):")
for k, v in sorted(chrome_hist.items(), key=lambda kv: -kv[1]):
    print(f"  {v:4d}  {k}")
for rel, cls, content, nch in rows:
    print(f"[{cls}] {rel}: CONTENT {content} (+{nch} chrome)")
if n_content_gap == 0:
    print("toc_parity_check: 0 content gaps -> PASS")
