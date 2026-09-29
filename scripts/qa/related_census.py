#!/usr/bin/env python3
"""Related-field link integrity census (RL-01..RL-02) for PROJECT-OMEGA.

The platform's cross-reference navigation rides on the front-matter
Related field. Tick-405 measured the corpus: 110 docs carry Related,
in three shapes - "See module README" / "See References" free text,
bare comma lists (TUTORIAL-007: `LAB-003, 5101, 5102`), and bracketed
lists (phase1 lessons: `[1102, 1103, 1201]`).

RL-01  Related token resolves to ZERO files (dangling pointer).
       Tokens are 4-digit lesson IDs (filename prefix), or
       LAB-NNN / TUTORIAL-NNN resource prefixes.
RL-02  Related token resolves to MULTIPLE files (ambiguous).

HARD GATE - exit 1 on any finding (KW-03 born-at-zero: birth
inventory tick-405 measured 110 docs / 35 tokens, all resolving
exactly one file, RL-01=0 RL-02=0). Free-text shapes ("See module
README", "See References") and bare-vs-bracketed list variance are
inventory only - a candidate standardization class, not gated.

Run over the whole corpus:
    python scripts/qa/related_census.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
RELATED_FIELD = re.compile(r"^Related:(.*)$")
TOKEN = re.compile(r"\d{4}|\b(?:LAB|TUTORIAL)-\d{3}\b")

FREE_TEXT = ("See module README", "See References")


def related_field(lines: list[str]) -> str | None:
    """Top-level Related value of one doc, or None if no front matter."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = RELATED_FIELD.match(raw)
                if m:
                    return m.group(1).strip()
            return None
    return None


def build_index(paths: list[Path], root: Path) -> dict[str, list[Path]]:
    """Token -> files, from filename prefixes only (4-digit, LAB-NNN,
    TUTORIAL-NNN). First token wins; a second token in one basename
    (e.g. a slug later containing digits) is ignored."""
    index: dict[str, list[Path]] = defaultdict(list)
    for p in sorted(paths):
        name = p.name
        m = re.match(r"^(\d{4}|(?:LAB|TUTORIAL)-\d{3})-", name)
        if m:
            index[m.group(1)].append(p)
        else:
            index[Path(name).stem].append(p)
    return {k: [x.relative_to(root) for x in v] for k, v in index.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    paths = sorted(docs.rglob("*.md"))
    index = build_index(paths, args.root)

    ambiguous_tokens = {k: v for k, v in index.items() if len(v) > 1}

    findings: list[str] = []
    n_docs = 0
    n_tokens = 0
    shapes = Counter()
    token_targets = Counter()
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        rel_field = related_field(lines)
        if rel_field is None:
            continue
        rel = path.relative_to(args.root).as_posix()
        n_docs += 1
        if any(rel_field.startswith(t) for t in FREE_TEXT):
            shapes["free-text"] += 1
            continue
        if rel_field.startswith("["):
            shapes["bracketed"] += 1
        else:
            shapes["bare"] += 1
        for tok in TOKEN.findall(rel_field):
            n_tokens += 1
            targets = index.get(tok, [])
            token_targets[len(targets)] += 1
            if not targets:
                findings.append(f"{rel}: RL-01 dangling Related token "
                                f"{tok!r} (no file)")
            elif len(targets) > 1:
                names = ", ".join(str(t) for t in targets)
                findings.append(f"{rel}: RL-02 ambiguous Related token "
                                f"{tok!r} ({len(targets)} files: {names})")

    rl01 = sum(1 for f in findings if " RL-01 " in f)
    rl02 = sum(1 for f in findings if " RL-02 " in f)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    amb = (f"; ambiguous index keys: "
           f"{sorted(ambiguous_tokens)!r}" if ambiguous_tokens else "")
    print(f"related_census: docs={n_docs} tokens={n_tokens} "
          f"shapes={dict(shapes)} resolve0={token_targets[0]} "
          f"resolve1={token_targets[1]} "
          f"resolveN={token_targets[2]} "
          f"RL-01={rl01} RL-02={rl02} "
          f"(hard gate; shapes {dict(shapes)})")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
