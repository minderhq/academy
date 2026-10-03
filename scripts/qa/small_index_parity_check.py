#!/usr/bin/env python3
"""small index parity gate for PROJECT-OMEGA.

MASTER-INDEX.md carries six small resource tables beside the big
locked ones (Labs, Tutorials, Notebooks, Cheat Sheets, Projects):
Career Guides, Comparisons, Industry Applications, Use Cases,
Solutions and Diagrams. Born tick-557 at 21 findings: every one of
the 21 row description cells abbreviated or paraphrased away the
front-matter Title ("Comparison index" against "Technology
Comparisons", "Healthcare" against "IND-001: Healthcare AI
Applications", "Enterprise Knowledge Base" against "SOL-001:
Enterprise Knowledge Base - Complete Implementation") - the same
abbreviation drift the lab lock called findings.

The title mirror here is deliberately prefix-free: this fleet's
title conventions are heterogeneous (CP-NNN:/IND-NNN:/UC-NNN:/
SOL-NNN: prefixes on four tables, mixed forms on the guides, and
natural "Title: Subtitle" shapes on the diagrams where a generic
prefix strip would eat real title text), so the one honest lock is
the front-matter Title verbatim, quotes stripped. The "Bridges &
Additional Resources" table is out of scope on purpose: it lists
directories, not files.

SG-01  id-set parity per table: every .md in the table's directory
       has a row and every row's link resolves to a file in that
       directory (either direction alone is a finding).
SG-02  link-text parity: every row's link text names its own target
       (text equals the target stem or the stem starts with
       "text-"; a wrong-but-existing link resolves cleanly for
       linkcheck yet misroutes the learner).
SG-03  the section header's "(N files)" count equals the row count,
       per table.
SG-04  description parity: the row's second cell equals the
       front-matter Title verbatim (quotes stripped).

Hard gate (exit 1 on findings): born tick-557 at 21 findings, all
SG-04, drained in the same tick - all 21 cells mirrored to
front-matter truth.

Run over the whole corpus:
    python scripts/qa/small_index_parity_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TABLES = [
    ("Career Guides", "docs/learning-resources/guides"),
    ("Comparisons", "docs/comparisons"),
    ("Industry Applications", "docs/industry"),
    ("Use Cases", "docs/use-cases"),
    ("Solutions", "docs/enterprise-solutions"),
    ("Diagrams", "docs/diagrams"),
]
MI_HEADER = re.compile(r"^### ([A-Za-z &]+) \((\d+) files?\)", re.M)
MI_ROW = re.compile(r"^\|\s*\*\*\[([^\]]+)\]\(([^)]+)\)\*\*")
FM_TITLE = re.compile(r"^Title:\s*(.+)$", re.M)


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def fm_title(path: Path) -> str | None:
    m = FM_TITLE.search(path.read_text(encoding="utf-8"))
    if not m:
        return None
    return m.group(1).strip().strip('"').strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []

    master = args.root / "docs" / "00-META" / "MASTER-INDEX.md"
    if not master.exists():
        print("small_index_parity_check: SKIP - docs/00-META/MASTER-INDEX.md not found, nothing to check")
        return 0
    mi = master.read_text(encoding="utf-8")

    n_rows = 0
    for name, rel_dir in TABLES:
        table_dir = args.root / rel_dir
        disk: dict[str, str] = {}  # stem -> title
        for p in sorted(table_dir.glob("*.md")):
            t = fm_title(p)
            if t is None:
                findings.append("%s/%s: SG-01 front matter missing Title"
                                % (rel_dir, p.name))
                continue
            disk[p.stem] = t

        hdr = re.search(r"^### " + re.escape(name)
                        + r" \((\d+) files?\)", mi, re.M)
        sec = re.search(r"^### " + re.escape(name) + r" \(", mi, re.M)
        rows: dict[str, tuple[str, str]] = {}  # target stem -> (text, mirror)
        if sec:
            rest = mi[sec.end():]
            # stop at the next ## OR ### heading - the Diagrams table is
            # followed by the ## Meta Documentation table, whose rows are
            # the same link-row shape (the gate's own first hour caught
            # this: a bare "^### " stop ran 10 foreign rows into Diagrams)
            stop = re.search(r"^##+ ", rest, re.M)
            body = rest[:stop.start()] if stop else rest
            for line in body.split("\n"):
                m = MI_ROW.match(line)
                if not m:
                    continue
                cells = line.split("|")
                mirror = cells[2].strip() if len(cells) > 2 else ""
                target = m.group(2).rstrip("/").rsplit("/", 1)[-1]
                rows[Path(target).stem] = (m.group(1).strip(), mirror)

        if hdr and int(hdr.group(1)) != len(rows):
            findings.append("SG-03 %s: header says %s files but the table "
                            "carries %d rows"
                            % (name, hdr.group(1), len(rows)))

        for stem in sorted(disk.keys() - rows.keys()):
            findings.append("SG-01 %s: file %s.md exists but has no "
                            "MASTER-INDEX %s row" % (name, stem, name))
        for stem in sorted(rows.keys() - disk.keys()):
            findings.append("SG-01 %s: MASTER-INDEX row but no file "
                            "%s.md in %s" % (name, stem, rel_dir))
        for stem in sorted(disk.keys() & rows.keys()):
            text, mirror = rows[stem]
            if text != stem and not stem.startswith(text + "-"):
                findings.append("SG-02 %s: link text %r does not name its "
                                "own target %s.md" % (name, text, stem))
            want = disk[stem]
            if mirror != want:
                findings.append("SG-04 %s: description drift - "
                                "MASTER-INDEX %r vs title %r"
                                % (name, mirror, want))
        n_rows += len(rows)

    for f in findings:
        print(esc(f))
    print("small_index_parity_check: %d findings (SG-01 id-set parity, "
          "SG-02 link-text parity, SG-03 header count, SG-04 description "
          "parity) across %d tables / %d MASTER-INDEX rows"
          % (len(findings), len(TABLES), n_rows))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
