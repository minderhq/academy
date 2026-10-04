#!/usr/bin/env python3
"""Label-code parity (LP-01..05, HARD) for Minder Academy.

linkcheck proves a link's TARGET exists; link_case_scan proves its
CASING is portable - but nothing proved that the numeric code a
display label advertises belongs to the file or module the link
actually opens. A card reading `5302: Distributed Training` that
opens 5402-Model-Parallelism is a lie the learner clicks; a module
row reading `1201-1203` over a module that grew to 1204 teaches a
catalog that no longer exists. tick-604's rename drain surfaced
exactly this gap (stale display labels that no gate could see), so
this gate closes it on the same extraction semantics linkcheck
uses: fences skipped, inline code scrubbed, front matter exempt.

LP-01  a coded label (`NNNN:` or `NNNN-NNNN:`, optional `word/`
       prefix) over a file target whose stem starts with 4 digits:
       the stem must lie within the label's inclusive range.
LP-02  a coded label over a file target without a numeric stem
       (README, QUIZ, PRACTICE, PREREQUISITES, CHECKPOINT): the
       label's low code must equal the nearest ancestor directory
       carrying a 4-digit prefix.
LP-03  a coded label over a directory whose direct *.md children
       carry 4-digit stems: a single-code label must equal the
       directory's own 4-digit prefix (module identity), a range
       label must equal the (min, max) stem span exactly - a range
       over a grown module is stale, a range over a shrunk module
       advertises lessons that are gone.
LP-04  a coded label over a directory with no stemmed children
       (phase roots): the code must equal the directory's 4-digit
       token, or phaseN-* * 1000.
LP-05  an `EXP_NNNN:` label must target the experiments file whose
       name carries the same EXP_NNNN.

Unresolvable targets stay linkcheck's finding, not ours: parity is
only judged where the target exists. Uncoded labels are out of
scope. Born tick-605 from a census of docs/' 3361 internal
links (5794 raw, 2433 external out of scope): 1395 stemmed-file,
178 unstemmed-file, 59 dir and 110 EXP-coded labels, all clean
after a 13-edit drain (10 stale LEARNING-PATH module ranges, 1
lesson-code module label, 1 wrong file target on VOLUME-5, 1 EXP
label pointing at another experiment's file).

Run over the whole corpus:
    python scripts/qa/label_code_parity_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CODED = re.compile(r"^(?:[A-Za-z-]+/)?(\d{4})(?:-(\d{4}))?:")
EXP_CODED = re.compile(r"^EXP_(\d{4}):")
STEM = re.compile(r"^(\d{4})")
DIRCODE = re.compile(r"(\d{4})")
PHASE = re.compile(r"^phase(\d+)-")
EXP_FILE = re.compile(r"EXP_(\d{4})")
INLINE_CODE = re.compile(r"`[^`]+`")
FENCE = re.compile(r"^\s*(```|~~~)")
FM_CLOSE = re.compile(r"^---\s*$")


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


def dir_stems(d: Path) -> list[int]:
    return sorted({int(m.group(1)) for g in d.glob("*.md")
                   if (m := STEM.match(g.name))})


def ancestor_code(p: Path, root: Path) -> str | None:
    cur = p
    while cur != root and cur != cur.parent:
        m = DIRCODE.search(cur.name)
        if m:
            return m.group(1)
        cur = cur.parent
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()

    findings: list[str] = []
    n_links = n_docs = 0
    for path in sorted((root / "docs").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root).as_posix()
        infence = False
        for i, ln in enumerate(body_lines(text), 1):
            if FENCE.match(ln.strip()):
                infence = not infence
                continue
            if infence:
                continue
            for m in MD_LINK.finditer(INLINE_CODE.sub("", ln)):
                label, target = m.group(1), m.group(2)
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                em = EXP_CODED.match(label)
                if em:
                    p = (path.parent / target.split("#")[0])
                    fm = EXP_FILE.search(p.name) if p.suffix else None
                    if p.is_file() and fm and fm.group(1) != em.group(1):
                        findings.append(
                            "LP-05 %s:%d `%s` opens `%s` (EXP_%s)"
                            % (rel, i, label, target, fm.group(1)))
                    continue
                cm = CODED.match(label)
                if not cm:
                    continue
                n_links += 1
                lo = int(cm.group(1))
                hi = int(cm.group(2)) if cm.group(2) else lo
                p = (path.parent / target.split("#")[0])
                if not p.exists():
                    continue  # existence is linkcheck's finding
                if p.is_dir():
                    stems = dir_stems(p)
                    if stems:
                        if cm.group(2):
                            span = (stems[0], stems[-1])
                            if (lo, hi) != span:
                                findings.append(
                                    "LP-03 %s:%d `%s` opens `%s` "
                                    "(stem span %d-%d)"
                                    % (rel, i, label, target, *span))
                        else:
                            dm = DIRCODE.match(p.name) or DIRCODE.search(
                                p.name)
                            want = (int(dm.group(1)) if dm else stems[0])
                            if lo != want:
                                findings.append(
                                    "LP-03 %s:%d `%s` opens `%s` "
                                    "(module code %d)" % (rel, i, label,
                                                          target, want))
                    else:
                        dm = DIRCODE.match(p.name)
                        pm = PHASE.match(p.name)
                        want = (int(dm.group(1)) if dm else
                                int(pm.group(1)) * 1000 if pm else None)
                        if want is not None and lo != want:
                            findings.append(
                                "LP-04 %s:%d `%s` opens `%s` (code %d)"
                                % (rel, i, label, target, want))
                    continue
                sm = STEM.match(p.name)
                if not sm:
                    ac = ancestor_code(p.parent, root)
                    if ac and int(ac) != lo:
                        findings.append(
                            "LP-02 %s:%d `%s` opens `%s` (ancestor %s)"
                            % (rel, i, label, target, ac))
                    continue
                stem = int(sm.group(1))
                if not lo <= stem <= hi:
                    findings.append(
                        "LP-01 %s:%d `%s` opens `%s` (stem %d)"
                        % (rel, i, label, target, stem))
        n_docs += 1
    for f in findings:
        print("  " + esc(f))
    print("label_code_parity_scan: %d coded links in %d docs scanned; "
          "%d LP findings - all hard (label codes must belong to the "
          "files and module spans they open; born tick-605 from a "
          "3361-internal-link census, 13-edit drain)" % (n_links, n_docs,
                                                len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
