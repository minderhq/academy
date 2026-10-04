#!/usr/bin/env python3
"""Frontmatter quality linter for the Minder Academy curriculum corpus.

Scans docs/**/*.md and enforces the corpus frontmatter standard that every
curriculum document with a frontmatter block already follows (330/330 files
at introduction time):

  FM-01  every markdown file under docs/ must carry a frontmatter block
  FM-02  frontmatter must close and parse as a YAML mapping
  FM-03  required keys: Document ID, Title, Last Updated, Status, Difficulty
  FM-04  Status is the enum {Complete}
  FM-05  Difficulty is one of {Beginner, Intermediate, Advanced, Expert}
  FM-06  Last Updated is an ISO date (YYYY-MM-DD)
  FM-07  Document ID matches the numeric prefix of the file name (when the
         name starts with NNNN-)
  FM-08  Module matches the numeric prefix of the parent directory and
         Phase matches the numeric part of the phase directory (when the
         keys are present)
  FM-09  Title text appears in the document's first H1 (punctuation and
         case normalized)

Usage:
    python scripts/qa/frontmatter_lint.py [--root REPO_ROOT]

Exit codes: 0 = no findings, 1 = findings (CI-style gate).
Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # environment problem, not a doc problem
    print("frontmatter_lint: PyYAML is required for the frontmatter gate "
          "(uv add pyyaml / pip install pyyaml)")
    sys.exit(2)

REQUIRED_KEYS = ("Document ID", "Title", "Last Updated", "Status", "Difficulty")
STATUS_OK = {"Complete"}
DIFFICULTY_OK = {"Beginner", "Intermediate", "Advanced", "Expert"}
LESSON_FILE = re.compile(r"^(\d{4})-[^/]*\.md$")
MODULE_DIR = re.compile(r"^(\d{4})-")
PHASE_DIR = re.compile(r"^phase(\d+)-")


def norm(text: str) -> str:
    """Lowercase and collapse everything non-alphanumeric to single spaces."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


class Linter:
    def __init__(self) -> None:
        self.findings: list[tuple[str, str, str]] = []

    def report(self, rel: str, check: str, detail: str = "") -> None:
        self.findings.append((rel, check, detail))
        line = "%s: %s" % (rel, check)
        if detail:
            line += " - " + detail
        print(line.encode("ascii", "backslashreplace").decode("ascii"))

    def lint_file(self, root: Path, path: Path) -> None:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        base = path.name
        lesson = "/phases/" in rel and LESSON_FILE.match(base)

        if not text.startswith("---\n"):
            self.report(rel, "FM-01", "markdown file has no frontmatter")
            return
        end = text.find("\n---", 3)
        if end < 0:
            self.report(rel, "FM-02", "frontmatter never closes")
            return

        try:
            data = yaml.safe_load(text[4:end])
        except yaml.YAMLError as exc:
            first = str(exc).splitlines()[0].strip()
            self.report(rel, "FM-02", "YAML parse error: %s" % first)
            return
        if not isinstance(data, dict):
            self.report(rel, "FM-02", "frontmatter is not a mapping")
            return

        for key in REQUIRED_KEYS:
            if key not in data:
                self.report(rel, "FM-03", "missing key %r" % key)
        if self.findings and self.findings[-1][0] == rel \
                and self.findings[-1][1] == "FM-03":
            return  # further checks need the required keys

        if data["Status"] not in STATUS_OK:
            self.report(rel, "FM-04", "Status %r not in %s"
                        % (data["Status"], sorted(STATUS_OK)))
        if data["Difficulty"] not in DIFFICULTY_OK:
            self.report(rel, "FM-05", "Difficulty %r not in %s"
                        % (data["Difficulty"], sorted(DIFFICULTY_OK)))
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(data["Last Updated"])):
            self.report(rel, "FM-06", "Last Updated %r is not YYYY-MM-DD"
                        % (data["Last Updated"],))

        num_prefix = LESSON_FILE.match(base) or re.match(r"^(\d{4})-", base)
        if num_prefix and "Document ID" in data:
            doc_id = str(data["Document ID"])
            prefix = num_prefix.group(1)
            same = doc_id == prefix or (
                doc_id.isdigit() and int(doc_id) == int(prefix))
            if not same:
                self.report(rel, "FM-07", "Document ID %r != file prefix %s"
                            % (doc_id, prefix))

        parts = rel.split("/")
        if "Module" in data and MODULE_DIR.match(parts[-2]):
            if not str(data["Module"]).startswith(MODULE_DIR.match(parts[-2]).group(1)):
                self.report(rel, "FM-08", "Module %r != parent dir %s"
                            % (data["Module"], parts[-2]))
        if "Phase" in data:
            phase_dir = next((p for p in parts if PHASE_DIR.match(p)), None)
            if phase_dir and not str(data["Phase"]).startswith(
                    PHASE_DIR.match(phase_dir).group(1)):
                self.report(rel, "FM-08", "Phase %r != phase dir %s"
                            % (data["Phase"], phase_dir))

        h1 = next((l[2:].strip() for l in text.split("\n") if l.startswith("# ")),
                  None)
        if h1 is None:
            self.report(rel, "FM-09", "no H1 for Title cross-check")
        else:
            tn, hn = norm(str(data["Title"])), norm(h1)
            if tn and hn and tn not in hn and hn not in tn:
                self.report(rel, "FM-09",
                            "Title %r not reflected in H1 %r"
                            % (data["Title"], h1))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    args = parser.parse_args()

    linter = Linter()
    for path in sorted((args.root / "docs").rglob("*.md")):
        linter.lint_file(args.root, path)

    print("frontmatter_lint: %d findings across docs/" % len(linter.findings))
    return 1 if linter.findings else 0


if __name__ == "__main__":
    sys.exit(main())
