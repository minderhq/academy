#!/usr/bin/env python3
"""feed-parity gate for the PROJECT-OMEGA platform feeds.

The platform load step consumes three JSON feeds - manifest_export
(corpus map), quiz_export (question bank) - plus curriculum_metrics.
Each feed is internally consistent by construction, but nothing
locked the CONTRACT between them: if one exporter's classification
drifts (a module the manifest sees that the quiz bank does not, a
lesson in the hierarchy that documents[] lost), the platform loads
the pair silently broken. This gate runs both exporters for real
(the exact public interface a platform load step would use), loads
the JSON they wrote, and locks the cross-feed invariants:

  FP-00  an exporter failed or wrote no loadable JSON
  FP-01  manifest hierarchy module set == quiz bank module set
  FP-02  manifest counts section vs its own arrays
  FP-03  hierarchy lessons == documents[type=lesson] (both
         directions; duplicates included)
  FP-04  every quiz-bank module file exists as a manifest document
  FP-05  quiz bank internal consistency (question_count / per-type
         counts / totals vs the question records)
  FP-06  manifest assessment.quiz flag set == quiz bank module set

Content totals (660 questions, 114 lessons) are deliberately NOT
pinned here - they are the living baseline recorded in memory, and
pinning them would break this gate on every content pass. The gate
locks consistency, not content.

Hard gate (exit 1 on findings): baseline 0 on the clean corpus.

Run over the whole corpus:
    python scripts/qa/feed_parity_check.py --root .
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

FEEDS = ("manifest_export.py", "quiz_export.py")
Q_TYPES = ("mcq", "coding", "open")


def load_feed(root: Path, script: str, out_dir: Path, findings: list[str]):
    """Run one exporter with --out and load the JSON it wrote."""
    out = out_dir / script.replace(".py", ".json")
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / script),
         "--root", str(root), "--out", str(out)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    data = None
    if proc.returncode != 0:
        findings.append("FP-00 %s exited %d - its own gate output is above "
                        "in the scorecard; cross-feed checks still ran on "
                        "what it wrote" % (script, proc.returncode))
    if out.exists():
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            findings.append("FP-00 %s wrote no parseable JSON" % script)
    else:
        findings.append("FP-00 %s wrote no output file" % script)
    return data


def check_feeds(manifest: dict, bank: dict, findings: list[str]) -> dict:
    """Cross-feed invariants. Returns a small stats map for the summary."""
    stats = {"phases": 0, "modules": 0, "lessons": 0, "documents": 0,
             "questions": 0}

    mcounts = manifest["counts"]
    h_modules: list[str] = []
    h_quiz: set[str] = set()
    h_lessons: list[str] = []
    for p in manifest["phases"]:
        stats["phases"] += 1
        for m in p["modules"]:
            name = m["dir"].split("/")[-1]
            stats["modules"] += 1
            h_modules.append(name)
            if m["assessment"]["quiz"]:
                h_quiz.add(name)
            h_lessons.extend(m["lessons"])
    stats["lessons"] = len(h_lessons)
    stats["documents"] = len(manifest["documents"])

    # FP-02 the counts section must match the arrays it summarizes
    for key, actual in (("documents", len(manifest["documents"])),
                        ("lessons", len(h_lessons)),
                        ("modules", stats["modules"]),
                        ("phases", stats["phases"])):
        if mcounts.get(key) != actual:
            findings.append("FP-02 manifest counts.%s=%r but the arrays hold "
                            "%d" % (key, mcounts.get(key), actual))

    # FP-03 hierarchy lessons == documents[type=lesson]
    d_lessons = [d["path"] for d in manifest["documents"]
                 if d["type"] == "lesson"]
    dupes = sorted({p for p in h_lessons if h_lessons.count(p) > 1})
    for p in dupes:
        findings.append("FP-03 lesson listed more than once in the hierarchy: "
                        "%s" % p)
    h_set, d_set = set(h_lessons), set(d_lessons)
    for p in sorted(h_set - d_set):
        findings.append("FP-03 hierarchy lesson missing from documents: %s" % p)
    for p in sorted(d_set - h_set):
        findings.append("FP-03 documents lesson missing from the hierarchy: %s"
                        % p)

    # FP-01 / FP-06 module-set and quiz-flag parity with the bank
    b_modules = bank.get("modules", [])
    b_names = {m["module"] for m in b_modules}
    h_names = set(h_modules)
    for n in sorted(h_names - b_names):
        findings.append("FP-01 manifest module with no quiz-bank record: %s"
                        % n)
    for n in sorted(b_names - h_names):
        findings.append("FP-01 quiz-bank module not in the manifest "
                        "hierarchy: %s" % n)
    for n in sorted(h_quiz ^ b_names):
        findings.append("FP-06 assessment.quiz flag disagrees with the quiz "
                        "bank on module %s" % n)

    # FP-04 every bank module file is a manifest document
    d_paths = {d["path"] for d in manifest["documents"]}
    for m in b_modules:
        if m.get("file") not in d_paths:
            findings.append("FP-04 quiz-bank file not a manifest document: %s"
                            % m.get("file"))

    # FP-05 bank internal consistency
    totals = {t: 0 for t in Q_TYPES}
    for m in b_modules:
        qs = m.get("questions", [])
        stats["questions"] += len(qs)
        if m.get("question_count") != len(qs):
            findings.append("FP-05 %s question_count=%r but %d records"
                            % (m["module"], m.get("question_count"), len(qs)))
        for q in qs:
            if q.get("type") not in Q_TYPES:
                findings.append("FP-05 %s question %r has unknown type %r"
                                % (m["module"], q.get("n"), q.get("type")))
            elif q["type"] in totals:
                totals[q["type"]] += 1
        mcounts_ = m.get("counts", {})
        record_counts = {t: sum(1 for q in qs if q.get("type") == t)
                         for t in Q_TYPES}
        if {t: mcounts_.get(t, 0) for t in Q_TYPES} != record_counts:
            findings.append("FP-05 %s counts map disagrees with its records"
                            % m["module"])
    btotals = bank.get("totals", {})
    if {t: btotals.get(t, 0) for t in Q_TYPES} != totals:
        findings.append("FP-05 bank totals %r disagree with the records %r"
                        % ({t: btotals.get(t) for t in Q_TYPES}, totals))
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    stats = {"phases": 0, "modules": 0, "lessons": 0, "documents": 0,
             "questions": 0}
    with tempfile.TemporaryDirectory(prefix="feed_parity_") as tmp:
        out_dir = Path(tmp)
        manifest = load_feed(args.root, "manifest_export.py", out_dir,
                             findings)
        bank = load_feed(args.root, "quiz_export.py", out_dir, findings)
        if manifest is not None and bank is not None:
            stats = check_feeds(manifest, bank, findings)

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print("feed_parity_check: %d findings (%d phases, %d modules, "
          "%d lessons, %d documents, %d questions cross-checked)"
          % (len(findings), stats["phases"], stats["modules"],
             stats["lessons"], stats["documents"], stats["questions"]))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
