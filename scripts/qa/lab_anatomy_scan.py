#!/usr/bin/env python3
"""Lab-file anatomy (LA-01..06, HARD) for Minder Academy.

Each docs/learning-resources/labs/LAB-*.md is a self-contained
hands-on unit the platform will render with its own metadata card
and completion ritual. Three anatomy rules hold corpus-wide:

LA-01  the frontmatter carries an "Estimated Time:" claim - the
       platform shows it on the lab card; labs without one force
       the learner to guess the commitment.
LA-02  the claim matches the derived effort: ceil(sum of part
       durations / 60) hours, where parts are the "## N: Title
       (NN minutes)" headers and "Final Challenge"/"optional"
       headers are excluded (they are stretch work, not the core
       path). Convention validated against the two labs that
       already carried the field: LAB-006 420 core-min -> 7 hours,
       LAB-010 330 core-min -> 6 hours.
LA-03  the file has a "## ...Completion Checklist..." section with
       at least 3 real "- [ ]" checkbox items - the per-lab
       completion ritual. Census tick-481: LAB-001..005 kept their
       checklists inside a fenced ```text block (invisible to
       markdown rendering, no real checkboxes), LAB-006 had no
       checklist section at all; drained the same tick (13 labs
       also gained their Estimated Time line).

LA-04  the checklist section header is exactly "## Lab Completion
       Checklist" - the platform links it from the lab card's
       completion ritual; bare or emoji-led variants fragment the
       anchor and the ToC.
LA-05  the overview section header is exactly "## Lab Overview"
       (title modulo emoji/case must not be the bare "Overview").
LA-06  no H1-H4 header line starts with an emoji (tick-485 canon,
       matching the tick-482 no-emoji decision for structure
       headers; census: 125 emoji-led headers across 13 labs,
       drained the same tick - 006/010 were already plain and are
       the corpus vote). Fence-aware: bash "# " comments inside
       code fences are not headers.

Born tick-481 (LA-01..03), born-at-zero after the same-tick drain;
LA-04..06 born tick-485, born-at-zero after the header-canonization
drain. Run over the whole corpus:

    python scripts/qa/lab_anatomy_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sys
from pathlib import Path

DUR = re.compile(r"\((\d+)\s*(?:-\s*(\d+)\s*)?(min|minutes?)\)", re.IGNORECASE)
EST_TIME = re.compile(r"^Estimated Time:\s*(\d+)\s*hour", re.MULTILINE)
CHECKBOX = re.compile(r"^\s*-\s+\[[ x]\]")
SKIP_HEADER = re.compile(r"challenge|optional", re.IGNORECASE)
FENCE = re.compile(r"^(```|~~~)")
EMOJI = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200d]")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def core_minutes(text: str) -> int:
    """Sum part durations in ##/### headers, excluding challenge/optional."""
    total = 0
    for ln in text.split("\n"):
        if re.match(r"^#{2,3}\s", ln) and not SKIP_HEADER.search(ln):
            m = DUR.search(ln)
            if m:
                hi = int(m.group(2)) if m.group(2) else int(m.group(1))
                total += hi
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    labs_dir = args.root / "docs" / "learning-resources" / "labs"
    findings: list[str] = []
    n_labs = 0
    for f in sorted(labs_dir.glob("LAB-*.md")):
        n_labs += 1
        rel = os.path.relpath(f, args.root).replace("\\", "/")
        text = f.read_text(encoding="utf-8", errors="replace")

        # LA-01: Estimated Time frontmatter claim exists
        em = EST_TIME.search(text)
        if em is None:
            findings.append("LA-01 %s: no 'Estimated Time:' line in the "
                            "frontmatter" % rel)

        # LA-02: the claim matches the derived core-path effort
        derived = math.ceil(core_minutes(text) / 60)
        if em is not None and int(em.group(1)) != derived:
            findings.append("LA-02 %s: Estimated Time claims %s hours, "
                            "derived core-path effort is %d hours "
                            "(ceil(part-durations/60), challenge/optional "
                            "excluded)" % (rel, em.group(1), derived))

        # LA-03: a ## Completion Checklist section with >=3 real items.
        # Section boundary is the next "^## " header - subsections
        # ("### ...") inside the checklist do NOT terminate it.
        cm = re.search(r"^## [^\n]*Completion Checklist[^\n]*\n", text,
                       re.MULTILINE | re.IGNORECASE)
        if cm is None:
            findings.append("LA-03 %s: no '## ...Completion Checklist' "
                            "section" % rel)
        else:
            n_items = 0
            for ln in text[cm.end():].split("\n"):
                if ln.startswith("## "):
                    break
                if CHECKBOX.match(ln):
                    n_items += 1
            if n_items < 3:
                findings.append("LA-03 %s: Completion Checklist carries %d "
                                "real '- [ ]' items - below the 3-item "
                                "floor" % (rel, n_items))

            # LA-04: the checklist header is the exact canonical form
            if cm.group(0).strip() != "## Lab Completion Checklist":
                findings.append("LA-04 %s: checklist header is %r - the "
                                "canonical form is '## Lab Completion "
                                "Checklist'" % (rel, esc(cm.group(0).strip())))

        # LA-05: the overview header is the exact canonical form
        for ln in text.split("\n"):
            if ln.startswith("## "):
                title = EMOJI.sub("", ln[3:]).strip()
                if title.lower() in ("overview", "lab overview") \
                        and ln.strip() != "## Lab Overview":
                    findings.append("LA-05 %s: overview header is %r - the "
                                    "canonical form is '## Lab Overview'"
                                    % (rel, esc(ln.strip())))

        # LA-06: no emoji-led H1-H4 header (fence-aware; bash "# "
        # comments inside code fences are not headers)
        fence = False
        for ln in text.split("\n"):
            if FENCE.match(ln.strip()):
                fence = not fence
                continue
            if fence:
                continue
            hm = re.match(r"^#{1,4}\s*", ln)
            if hm and hm.end() < len(ln) and EMOJI.match(ln[hm.end()]):
                findings.append("LA-06 %s: emoji-led header %r - structure "
                                "headers are plain text (tick-482 canon)"
                                % (rel, esc(ln.strip()[:40])))

    for f in findings:
        print("  " + esc(f))
    print("lab_anatomy_scan: %d lab files; %d findings - all hard "
          "(LA-01 no Estimated Time claim / LA-02 claim mismatches the "
          "derived core-path effort / LA-03 no Completion Checklist "
          "section or below the 3-checkbox floor / LA-04 non-canonical "
          "checklist header / LA-05 non-canonical overview header / "
          "LA-06 emoji-led header; LA-01..03 born tick-481, LA-04..06 "
          "born tick-485 after the 125-header canonization drain)"
          % (n_labs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
