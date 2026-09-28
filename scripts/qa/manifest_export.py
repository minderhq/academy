#!/usr/bin/env python3
"""Corpus manifest feed for the future PROJECT-OMEGA platform.

Exports the corpus as one machine-readable JSON document: every
frontmatter-carrying doc under docs/ with its metadata, plus the
phase/module/lesson hierarchy and counts. Not a gate - report-only
feed, exits 0 by design. Pairs with quiz_export (the question bank)
so a platform load step never has to re-parse markdown.

Extraction models are borrowed, not reinvented: the naive
frontmatter key/value model comes from quiz_export.parse_frontmatter,
and the lesson/module/phase classification is the same one
quality_report uses for its corpus line.

Output is deterministic (path-sorted) so diffs stay meaningful.
stdout by default; --out writes UTF-8 JSON to a file.

Usage:
    python scripts/qa/manifest_export.py [--root REPO_ROOT] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quiz_export import parse_frontmatter  # noqa: E402

# Same classification as quality_report's corpus line.
PHASE_DIR = re.compile(r"^phase(\d+)-")
MODULE_DIR = re.compile(r"^(\d{4})-")
LESSON_FILE = re.compile(r"^(\d{4})-[^/]*\.md$")

FM_KEYS = {"Document ID": "id", "Title": "title", "Last Updated": "last_updated",
           "Status": "status", "Difficulty": "difficulty",
           "Module": "module", "Phase": "phase"}


def doc_entry(root: Path, path: Path) -> dict:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    fm = parse_frontmatter(lines)
    # Parity rule: "lesson" means a 4-digit file under a 4-digit module dir at
    # any depth - exactly what quality_report's module rglob counts (index
    # docs like 00-META/0000-LEARNING-PATH.md match the filename but are meta).
    rel_parts = rel.split("/")
    in_module = (len(rel_parts) >= 5 and rel_parts[1] == "phases"
                 and PHASE_DIR.match(rel_parts[2])
                 and MODULE_DIR.match(rel_parts[3]))
    is_lesson = bool(LESSON_FILE.match(path.name)) and in_module
    entry = {"path": rel, "type": "lesson" if is_lesson else "meta"}
    for src, dst in FM_KEYS.items():
        entry[dst] = fm.get(src)
    phase_no = re.search(r"/phase(\d+)-", "/" + rel)
    entry["phase_no"] = int(phase_no.group(1)) if phase_no else None
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    parser.add_argument("--out", type=Path, default=None,
                        help="write JSON to this file instead of stdout")
    args = parser.parse_args()
    root = args.root

    docs = sorted((root / "docs").rglob("*.md"))
    documents = [doc_entry(root, p) for p in docs]

    phases = []
    for pdir in sorted(d for d in (root / "docs" / "phases").iterdir()
                       if d.is_dir() and PHASE_DIR.match(d.name)):
        modules = []
        for mdir in sorted(d for d in pdir.iterdir()
                           if d.is_dir() and MODULE_DIR.match(d.name)):
            lessons = sorted(
                m.relative_to(root).as_posix()
                for m in mdir.rglob("*.md") if LESSON_FILE.match(m.name))
            modules.append({
                "dir": mdir.relative_to(root).as_posix(),
                "lessons": lessons,
                "assessment": {
                    "quiz": (mdir / "assessment" / "QUIZ.md").exists(),
                    "practice": (mdir / "assessment" / "PRACTICE.md").exists(),
                },
            })
        phases.append({"dir": pdir.relative_to(root).as_posix(),
                       "modules": modules})

    manifest = {
        "generator": "scripts/qa/manifest_export.py",
        "counts": {
            "documents": len(documents),
            "lessons": sum(len(m["lessons"]) for p in phases for m in p["modules"]),
            "modules": sum(len(p["modules"]) for p in phases),
            "phases": len(phases),
        },
        "documents": documents,
        "phases": phases,
    }
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"manifest_export: wrote {args.out} "
              f"({manifest['counts']['documents']} documents, "
              f"{manifest['counts']['lessons']} lessons, "
              f"{manifest['counts']['modules']} modules, "
              f"{manifest['counts']['phases']} phases)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
