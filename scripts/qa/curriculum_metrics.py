#!/usr/bin/env python3
"""Curriculum metrics report for the PROJECT-OMEGA corpus.

Answers the loop question "ger\u00e7ekten e\u011fitim kalitesi ne seviyede?"
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
import json
import re
import statistics
import sys
from datetime import date
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
    """Prose words (outside fences) + in-fence code words + fence counts,
    structure_lint's CommonMark length-aware model. Code-heavy lessons
    (a full implementation in one fence) are dense, not thin - so the
    thin-review queue weighs prose + code together, not prose alone."""
    words = 0
    code_words = 0
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
            code_words += len(ln.split())
            continue
        words += len(ln.split())
        if H2.match(ln):
            h2s += 1
        links += len(REL_LINK.findall(ln))
    return {"words": words, "code_words": code_words, "py": py, "bash": bash,
            "h2": h2s, "links": links}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    parser.add_argument("--out", type=Path, default=None,
                        help="additionally write the report as a JSON snapshot "
                             "to this file (same feed idiom as manifest_export "
                             "and quiz_export --out)")
    args = parser.parse_args()
    root = args.root

    lessons = []
    modules = []
    phases_root = root / "docs" / "phases"
    phase_dirs = (sorted(d for d in phases_root.iterdir()
                         if d.is_dir() and PHASE_DIR.match(d.name))
                  if phases_root.is_dir() else [])
    for pdir in phase_dirs:
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

    if not lessons:
        print("curriculum_metrics: SKIP - no lessons found, nothing to analyze")
        return 0

    words = sorted(s["words"] for s in lessons)
    content = sorted(s["words"] + s["code_words"] for s in lessons)
    # A thin lesson is thin on CONTENT (prose + code), not prose alone:
    # code-heavy lessons put a full implementation in one fence and are
    # dense. Prose-only flagging was a false positive class (caught live
    # on 7102/7103, two ~300-prose-word lessons with 400+ lines of code).
    thin = sorted((s for s in lessons if s["words"] + s["code_words"] < 800),
                  key=lambda s: s["words"] + s["code_words"])
    qmod = [m for m in modules if m["questions"]]
    print("PROJECT-OMEGA curriculum metrics")
    print("=" * 72)
    print("corpus: %d lessons, %d modules, %d phases"
          % (len(lessons), len(modules),
             len({m["dir"].split("/")[2] for m in modules})))
    print("lesson content words (prose + code): total %d, median %d, "
          "mean %d, min %d, max %d"
          % (sum(content), statistics.median(content),
             round(statistics.mean(content)), min(content), max(content)))
    print("prose share: total %d prose / %d code words "
          "(%.0f%% prose)"
          % (sum(words), sum(s["code_words"] for s in lessons),
             100 * sum(words)
             / max(1, sum(words) + sum(s["code_words"] for s in lessons))))
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
    print("thinnest lessons (<800 content words incl. code; index/README-"
          "style files are naturally thin - a review queue, not a failure):")
    for s in thin[:10]:
        print("  %4d content words  %s"
              % (s["words"] + s["code_words"], esc(s["path"])))
    if len(thin) > 10:
        print("  ... and %d more" % (len(thin) - 10))
    if not thin:
        print("  none - every lesson clears the 800-word content floor")
    # Same false-positive lesson as the thin list: a 2-lesson focused unit
    # (tensor+backprop, tool-calling+code-interpreter) can carry a full
    # module, so the sparse list shows unit content next to the count -
    # the count alone is never the verdict (measured live: the five
    # flagged modules span 2,767-4,442 content words vs a ~3,700
    # two-lesson corpus expectation).
    mcontent = {}
    for s in lessons:
        mdir = "/".join(s["path"].split("/")[:4])
        mcontent[mdir] = mcontent.get(mdir, 0) + s["words"] + s["code_words"]
    sparse = sorted((m for m in modules if m["lessons"] < 3),
                    key=lambda m: mcontent.get(m["dir"], 0))
    print("modules with <3 lessons (unit content shown - a 2-lesson "
          "focused unit can carry a full module): %s"
          % (", ".join("%s (%d lessons, %d content words)"
                       % (esc(m["dir"].split("/")[3]), m["lessons"],
                          mcontent.get(m["dir"], 0))
                       for m in sparse)
             if sparse else "none"))
    if args.out:
        # Same feed idiom as manifest_export/quiz_export --out: the whole
        # report as one JSON snapshot (generated date, tool, distributions,
        # and per-lesson stats) so content totals accumulate into a trend
        # across ticks instead of scrolling away in stdout.
        snapshot = {
            "generated": date.today().isoformat(),
            "tool": "curriculum_metrics.py",
            "corpus": {"lessons": len(lessons), "modules": len(modules),
                       "phases": len({m["dir"].split("/")[2] for m in modules})},
            "content_words": {"total": sum(content),
                              "median": statistics.median(content),
                              "mean": round(statistics.mean(content)),
                              "min": min(content), "max": max(content)},
            "prose_words": sum(words),
            "code_words": sum(s["code_words"] for s in lessons),
            "fences": {"python": sum(s["py"] for s in lessons),
                       "bash": sum(s["bash"] for s in lessons)},
            "assessments": {"modules_with_quiz": len(qmod),
                            "questions": sum(m["questions"] for m in modules)},
            "thin": [{"path": s["path"], "content": s["words"] + s["code_words"]}
                     for s in thin],
            "sparse_modules": [{"dir": m["dir"], "lessons": m["lessons"],
                                "content": mcontent.get(m["dir"], 0)}
                               for m in sparse],
            "lessons": [{"path": s["path"], "words": s["words"],
                         "code_words": s["code_words"],
                         "content": s["words"] + s["code_words"],
                         "py": s["py"], "bash": s["bash"],
                         "h2": s["h2"], "links": s["links"]}
                        for s in lessons],
        }
        args.out.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print("curriculum_metrics: snapshot written to %s" % args.out)
    print("curriculum_metrics: %d lessons analyzed, report only -> PASS" % len(lessons))
    return 0


if __name__ == "__main__":
    sys.exit(main())
