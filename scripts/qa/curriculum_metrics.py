#!/usr/bin/env python3
"""Curriculum metrics report for the PROJECT-OMEGA corpus.

Answers the loop question "gerçekten eğitim kalitesi ne seviyede?"
with numbers, continuously: lesson length distribution, code density,
heading structure, and quiz coverage per module. Report-only tool -
exit 0 by design; a thin lesson is a review queue, not a failure
(same stance as fm_staleness).

Models are borrowed for parity, not reinvented: the phase/module/
lesson classification matches quality_report's corpus line (a lesson
is a 4-digit file under docs/phases/phaseN-*/NNNN-*/ at any depth),
and the fence model is structure_lint's CommonMark length-aware
toggle. Quiz counts re-parse QUIZ.md through quiz_export.export_quiz.

Usage:
    python scripts/qa/curriculum_metrics.py [--root REPO_ROOT]

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quiz_export import export_quiz  # noqa: E402

# Same classification as quality_report's corpus line.
PHASE_DIR = re.compile(r"^phase(\d+)-")
MODULE_DIR = re.compile(r"^(\d{4})-")
LESSON_FILE = re.compile(r"^(\d{4})-[^/]*\.md$")

FENCE = re.compile(r"^(\s*)(`{3,})([\w+-]*)\s*$")
H2 = re.compile(r"^## \S")
REL_LINK = re.compile(r"\]\([^)#h][^)]*\)")


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def lesson_stats(lines):
    """Prose words (outside fences) + fence counts, structure_lint model."""
    words = 0
    py = bash = 0
    h2s = 0
    links = 0
    state = 0
    for ln in lines:
        m = FENCE.match(ln)
        if m:
            ticks, lang = len(m.group(2)), m.group(3)
            if state and not lang and ticks >= state:
                state = 0
            elif not state:
                state = ticks
                if lang in ("python", "py"):
                    py += 1
                elif lang in ("bash", "sh", "shell"):
                    bash += 1
            continue
        if state:
            continue
        words += len(ln.split())
        if H2.match(ln):
            h2s += 1
        links += len(REL_LINK.findall(ln))
    return {"words": words, "py": py, "bash": bash, "h2": h2s, "links": links}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    args = parser.parse_args()
    root = args.root

    lessons = []
    modules = []
    for pdir in sorted(d for d in (root / "docs" / "phases").iterdir()
                       if d.is_dir() and PHASE_DIR.match(d.name)):
        for mdir in sorted(d for d in pdir.iterdir()
                           if d.is_dir() and MODULE_DIR.match(d.name)):
            mod_lessons = sorted(p for p in mdir.rglob("*.md")
                                 if LESSON_FILE.match(p.name))
            quiz_findings = []
            qn = 0
            quiz = mdir / "assessment" / "QUIZ.md"
            if quiz.exists():
                lines = quiz.read_text(encoding="utf-8").split("\n")
                rel = quiz.relative_to(root).as_posix()
                _, questions = export_quiz(rel, lines, quiz_findings)
                qn = len(questions)
            modules.append({"dir": mdir.relative_to(root).as_posix(),
                            "lessons": len(mod_lessons), "questions": qn})
            for p in mod_lessons:
                rel = p.relative_to(root).as_posix()
                lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
                st = lesson_stats(lines)
                st["path"] = rel
                lessons.append(st)

    words = sorted(s["words"] for s in lessons)
    thin = sorted((s for s in lessons if s["words"] < 300),
                  key=lambda s: s["words"])
    qmod = [m for m in modules if m["questions"]]
    print("PROJECT-OMEGA curriculum metrics")
    print("=" * 72)
    print("corpus: %d lessons, %d modules, %d phases"
          % (len(lessons), len(modules),
             len({m["dir"].split("/")[2] for m in modules})))
    print("lesson prose words: total %d, median %d, mean %d, min %d, max %d"
          % (sum(words), statistics.median(words),
             round(statistics.mean(words)), min(words), max(words)))
    print("code density: %d python + %d bash fences across %d lessons "
          "(%.1f fences/lesson)"
          % (sum(s["py"] for s in lessons), sum(s["bash"] for s in lessons),
             len(lessons),
             (sum(s["py"] for s in lessons) + sum(s["bash"] for s in lessons))
             / len(lessons)))
    print("structure: H2/lesson median %d, rel-links/lesson median %d"
          % (statistics.median([s["h2"] for s in lessons]),
             statistics.median([s["links"] for s in lessons])))
    print("assessments: %d/%d modules with a parsed quiz, %d questions total "
          "(%.1f questions/module)"
          % (len(qmod), len(modules), sum(m["questions"] for m in modules),
             sum(m["questions"] for m in modules) / len(modules)))
    print()
    print("thinnest lessons (<300 prose words; index/README-style files are "
          "naturally thin - a review queue, not a failure):")
    for s in thin[:10]:
        print("  %4d words  %s" % (s["words"], esc(s["path"])))
    if len(thin) > 10:
        print("  ... and %d more" % (len(thin) - 10))
    sparse = sorted((m for m in modules if m["lessons"] < 3),
                    key=lambda m: m["lessons"])
    print("modules with <3 lessons: %s"
          % (", ".join(esc(m["dir"].split("/")[3]) for m in sparse)
             if sparse else "none"))
    print("curriculum_metrics: %d lessons analyzed, report only -> PASS" % len(lessons))
    return 0


if __name__ == "__main__":
    sys.exit(main())
