#!/usr/bin/env python3
"""volume_checklist_scan (VC-01/VC-02): every checklist item in a volume
guide must resolve to a real file, and its short title must match what
that file actually is.

Why: the VOLUME-*.md checklists are the learner-facing "do this next"
surface. tick-454 found three mislabeled items in VOLUME-7 (an item said
"7201: AutoGen vs LangGraph" while pointing at the 7303 file) - a dead
or mislabeled checklist entry is a direct platform UX bug.

Checks:
  VC-01  the item's ID resolves to no file in the corpus
  VC-02  the item's title shares zero keywords with the resolved file
         (filename suffix OR front-matter Title - filenames can lag the
         doc's real title, e.g. 7301-Orchestration.md is titled
         "Collaborative Tasking")

Item shapes parsed: "NNNN: Title", "TUTORIAL-NNN: Title", "LAB-NNN:
Title", "EXP_NNNN: Title". Anything else (Project A/B/C, prose goals)
is a curricular choice, not a file reference - skipped.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

STOPWORDS = {"and", "the", "for", "vs", "of", "in", "to", "with", "from"}


def tokens(text: str) -> set[str]:
    return {
        tok
        for tok in re.findall(r"[a-z0-9]+", text.lower())
        if len(tok) >= 3 and tok not in STOPWORDS
    }


def section_body(text: str, title_re: str) -> str:
    m = re.search(r"^### " + title_re + r"\s*$", text, re.M)
    if m is None:
        return ""
    rest = text[m.end():]
    stop = re.search(r"^### |^## ", rest, re.M)
    return rest[: stop.start()] if stop else rest


ITEM_RE = re.compile(r"^- \[ \] \*\*(.+?)\*\*", re.M)
ID_RES = [
    (re.compile(r"^(\d{4}): (.+)$"), "lesson"),
    (re.compile(r"^TUTORIAL-(\d+): (.+)$"), "tutorial"),
    (re.compile(r"^LAB-(\d+): (.+)$"), "lab"),
    (re.compile(r"^EXP_(\d+): (.+)$"), "experiment"),
]


def build_index(root: Path) -> dict[str, dict[str, list[Path]]]:
    idx: dict[str, dict[str, list[Path]]] = {
        "lesson": {},
        "tutorial": {},
        "lab": {},
        "experiment": {},
    }
    scan_roots = [root / "docs", root / "experiments"]
    for scan_root in scan_roots:
        if not scan_root.is_dir():
            continue
        for p in scan_root.rglob("*.md"):
            name = p.stem
            m = re.match(r"^(\d{4})-", name)
            if m:
                idx["lesson"].setdefault(m.group(1), []).append(p)
                continue
            m = re.match(r"^TUTORIAL-(\d+)-", name)
            if m:
                idx["tutorial"].setdefault(m.group(1), []).append(p)
                continue
            m = re.match(r"^LAB-(\d+)-", name)
            if m:
                idx["lab"].setdefault(m.group(1), []).append(p)
                continue
            m = re.match(r"^EXP_(\d+)_", name)
            if m:
                idx["experiment"].setdefault(m.group(1), []).append(p)
    return idx


def fm_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").split("\n", 20):
        m = re.match(r'^Title: "(.*)"\s*$', line)
        if m:
            return m.group(1)
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args()

    idx = build_index(args.root)
    findings: list[str] = []

    for vol_path in sorted((args.root / "docs" / "volumes").glob("VOLUME-*.md")):
        vt = vol_path.read_text(encoding="utf-8")
        body = "\n".join(
            section_body(vt, t)
            for t in (r"Core Content \(Required\)", r"Advanced Content \(Optional\)")
        )
        for item in ITEM_RE.finditer(body):
            text = item.group(1).strip()
            line_no = vt[: vt.index(text)].count("\n") + 1
            for id_re, kind in ID_RES:
                m = id_re.match(text)
                if m is None:
                    continue
                doc_id, title = m.group(1), m.group(2).strip()
                matches = idx[kind].get(doc_id, [])
                if not matches:
                    findings.append(
                        "%s:%d: VC-01 checklist references missing %s %s -"
                        " no file in the corpus (%r)"
                        % (vol_path.name, line_no, kind, doc_id, title)
                    )
                    break
                want = tokens(title)
                fname_ok = any(tokens(p.stem) & want for p in matches)
                title_ok = any(tokens(fm_title(p)) & want for p in matches)
                if not (fname_ok or title_ok):
                    findings.append(
                        "%s:%d: VC-02 checklist says %r but %s resolves to"
                        " %s - title matches nothing on disk"
                        % (
                            vol_path.name,
                            line_no,
                            title,
                            doc_id,
                            matches[0].name,
                        )
                    )
                break

    for f in findings:
        print(f)
    print(
        "volume_checklist_scan: %d findings (VC-01 missing reference,"
        " VC-02 title mismatch) across docs/volumes/"
        % len(findings)
    )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
