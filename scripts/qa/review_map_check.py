#!/usr/bin/env python3
"""Need to Review map integrity gate (RM) for Minder Academy.

Every assessment/QUIZ.md ships a "## Need to Review?" map linking each
question to its closest lesson (the AS-12 review-map drain, ticks ~514-529,
33/33 banks). That drain was hand-audited; this gate locks the discipline
in mechanically so future quiz edits cannot silently break it.

Per bank it checks:
  RM-01  the map section exists with the intro line
  RM-02  every bullet's question coverage parses (singles and A-B ranges)
  RM-03  the union of covered questions is exactly 1..N, each once
  RM-04  bullets are ordered by first covered question (strictly increasing)
  RM-05  every bullet carries at least one markdown link
  RM-06  every linked target resolves on disk relative to the quiz file

Exit 0 when all banks pass; exit 1 otherwise.
    python scripts/qa/review_map_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

H2_MAP_RE = re.compile(r"^## Need to Review\?\s*$", re.MULTILINE)
INTRO_RE = re.compile(r"^Each question maps", re.MULTILINE)
BULLET_RE = re.compile(r"^- \*\*(?:Questions?|Q)\s+([0-9,\s\-]+?):?\*\*", re.MULTILINE)
RANGE_RE = re.compile(r"(\d+)\s*-\s*(\d+)")
SINGLE_RE = re.compile(r"^\d+$")
KEY_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|", re.MULTILINE)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ANSWER_KEY_H2 = "## Answer Key"


def parse_coverage(label: str) -> list[int] | None:
    """Expand a bullet's question label into its covered numbers, or None."""
    nums: list[int] = []
    for token in (t.strip() for t in label.split(",")):
        if not token:
            return None
        rng = RANGE_RE.fullmatch(token)
        if rng:
            lo, hi = int(rng.group(1)), int(rng.group(2))
            if lo > hi:
                return None
            nums.extend(range(lo, hi + 1))
        elif SINGLE_RE.match(token):
            nums.append(int(token))
        else:
            return None
    return nums


def check_bank(quiz: Path) -> list[str]:
    text = quiz.read_text(encoding="utf-8")
    findings: list[str] = []

    key_start = text.find(ANSWER_KEY_H2)
    if key_start == -1:
        return ["RM-00 no Answer Key section"]
    key_body = text[key_start:]
    key_qs = [int(m) for m in KEY_ROW_RE.findall(key_body)]
    n = max(key_qs) if key_qs else 0
    if sorted(key_qs) != list(range(1, n + 1)):
        findings.append(f"RM-00 answer key rows are not 1..{n}: {sorted(key_qs)}")

    map_match = H2_MAP_RE.search(text)
    if not map_match:
        findings.append("RM-01 no '## Need to Review?' section")
        return findings
    tail = text[map_match.end():]
    next_h2 = re.search(r"\n## ", tail)
    map_body = tail[:next_h2.start()] if next_h2 else tail
    if not INTRO_RE.search(map_body):
        findings.append("RM-01 map section lacks the intro line")

    bullets = BULLET_RE.findall(map_body)
    if not bullets:
        findings.append("RM-02 no parseable coverage bullets")
        return findings

    covered: list[int] = []
    firsts: list[int] = []
    for label in bullets:
        nums = parse_coverage(label)
        if nums is None:
            findings.append(f"RM-02 unparseable coverage label: {label!r}")
            continue
        covered.extend(nums)
        firsts.append(nums[0])
    if firsts != sorted(firsts) or len(set(firsts)) != len(firsts):
        findings.append(f"RM-04 bullets not strictly ordered by first question: {firsts}")

    # Hybrid banks (e.g. 2300) map MC answers 1..K plus coding questions K+1..N
    # that have no answer-key rows, so N extends to the highest mapped question.
    if covered:
        n = max(n, max(covered))
    expected = list(range(1, n + 1))
    if sorted(covered) != expected:
        missing = sorted(set(expected) - set(covered))
        extra = sorted(set(covered) - set(expected))
        dupes = sorted({q for q in covered if covered.count(q) > 1})
        findings.append(
            f"RM-03 coverage != 1..{n} exactly-once"
            f" (missing={missing} extra={extra} dupes={dupes})"
        )

    bullet_spans = [(m.start(), m.end()) for m in BULLET_RE.finditer(map_body)]
    for i, (start, _label_end) in enumerate(bullet_spans):
        block_end = bullet_spans[i + 1][0] if i + 1 < len(bullet_spans) else len(map_body)
        block = map_body[start:block_end]
        links = LINK_RE.findall(block)
        if not links:
            findings.append(f"RM-05 bullet without any link: {block[:60]!r}...")
            continue
        for rel in links:
            if rel.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if not (quiz.parent / rel).exists():
                findings.append(f"RM-06 broken map link {rel!r}")
    return findings


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="curriculum root containing docs/phases")
    args = parser.parse_args()
    root = Path(args.root)

    banks = sorted(root.glob("docs/phases/*/*/assessment/QUIZ.md"))
    if not banks:
        print("review_map_check: no QUIZ.md banks found under docs/phases")
        return 1

    failing = 0
    for quiz in banks:
        findings = check_bank(quiz)
        rel = quiz.relative_to(root)
        if findings:
            failing += 1
            print(f"FAIL {rel}")
            for f in findings:
                print(f"     {f}")
        else:
            print(f"ok   {rel}")

    total = len(banks)
    print(
        f"review_map_check: {total} banks, {total - failing} clean, {failing} failing"
        f" -> {'PASS' if failing == 0 else 'FAIL'}"
    )
    return 0 if failing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
