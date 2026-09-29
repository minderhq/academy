#!/usr/bin/env python3
"""Prerequisites field census (PQ-01..PQ-02) for PROJECT-OMEGA.

Prerequisites is the curriculum's learning-path backbone: on the
platform a dangling prerequisite is a lesson that can never be
unlocked. Tick-409 measured the corpus: 108 docs carry the field,
the name is uniform (0 variants), and values fall into four
shapes - 95 free-text "See module README", 4 "See
PREREQUISITES.md", 3 bare token lists (`TUTORIAL-001`,
`TUTORIAL-005, LAB-009`), 3 titled brackets (`[1201] Proxmox
Hypervisor SOP`, `[1101] ..., [1102] ...`), and 3 prose
sentences.

PQ-01  machine-parseable token resolves to ZERO files (dangling).
PQ-02  machine-parseable token resolves to MULTIPLE files
       (ambiguous).

HARD GATE on PQ-01/PQ-02 (KW-03 born-at-zero if measured 0 at
birth). Shape variance (free-text vs titled vs bare vs prose) is
inventory only: canonical linked shape is the bracketed bare-token
list, matching the Related field standard - a drain + PQ-03 shape
class is the queued next pass, mirroring tick-405/406.

Run over the whole corpus:
    python scripts/qa/prereq_census.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
PQ_FIELD = re.compile(r"^Prerequisites:(.*)$")
TOKEN = re.compile(r"\d{4}|\b(?:LAB|TUTORIAL)-\d{3}\b")
BRACKET_TOK = re.compile(r"\[(\d{4}|(?:LAB|TUTORIAL)-\d{3})\]")
FREE_TEXT = ("See module README", "See PREREQUISITES.md")


def pq_field(lines: list[str]) -> str | None:
    """Top-level Prerequisites value of one doc, or None."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = PQ_FIELD.match(raw)
                if m:
                    return m.group(1).strip()
            return None
    return None


def build_index(paths: list[Path], root: Path) -> dict[str, list[Path]]:
    """Token -> files, from filename prefixes (4-digit, LAB-NNN,
    TUTORIAL-NNN); other stems keyed by name."""
    index: dict[str, list[Path]] = defaultdict(list)
    for p in sorted(paths):
        m = re.match(r"^(\d{4}|(?:LAB|TUTORIAL)-\d{3})-", p.name)
        if m:
            index[m.group(1)].append(p)
        else:
            index[p.stem].append(p)
    return {k: [x.relative_to(root) for x in v] for k, v in index.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    paths = sorted(docs.rglob("*.md"))
    index = build_index(paths, args.root)

    findings: list[str] = []
    shapes = Counter()
    n_docs = 0
    n_tokens = 0
    targets_n = Counter()
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        val = pq_field(lines)
        if val is None:
            continue
        rel = path.relative_to(args.root).as_posix()
        n_docs += 1
        toks: list[str] = []
        if any(val.startswith(t) for t in FREE_TEXT):
            shapes["free-text"] += 1
        else:
            btoks = BRACKET_TOK.findall(val)
            if btoks:
                shapes["titled-brackets"] += 1
                toks = btoks
            else:
                ctoks = TOKEN.findall(val)
                # prose sentences may carry stray digits; treat as
                # machine-parseable only if every comma item is a
                # pure token or token list
                items = [s.strip() for s in val.split(",")]
                if ctoks and all(TOKEN.fullmatch(s) for s in items):
                    shapes["bare-list"] += 1
                    toks = ctoks
                else:
                    shapes["prose"] += 1
        for tok in toks:
            n_tokens += 1
            targets = index.get(tok, [])
            targets_n[len(targets)] += 1
            if not targets:
                findings.append(f"{rel}: PQ-01 dangling Prerequisite "
                                f"{tok!r} (no file)")
            elif len(targets) > 1:
                names = ", ".join(str(t) for t in targets)
                findings.append(f"{rel}: PQ-02 ambiguous Prerequisite "
                                f"{tok!r} ({len(targets)} files: {names})")

    pq01 = sum(1 for f in findings if " PQ-01 " in f)
    pq02 = sum(1 for f in findings if " PQ-02 " in f)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"prereq_census: docs={n_docs} tokens={n_tokens} "
          f"shapes={dict(shapes)} resolve0={targets_n[0]} "
          f"resolve1={targets_n[1]} resolveN={targets_n[2]} "
          f"PQ-01={pq01} PQ-02={pq02} "
          f"(hard gate PQ-01/02; shapes inventory, PQ-03 queued)")
    return 1 if (pq01 or pq02) else 0


if __name__ == "__main__":
    sys.exit(main())
