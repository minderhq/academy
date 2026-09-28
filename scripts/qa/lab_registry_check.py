#!/usr/bin/env python3
"""lab identity gate: every `LAB-0NN: Topic` label must match its lab file.

Lab ids are the corpus's cross-document navigation layer (progress
trackers, learning paths, volume guides, bridges, lesson cross-refs),
but nothing checked them - so labels drifted from the labs they point
at. The 2026-09-29 census (301 labels corpus-wide) found three wrong
identities: PROGRESS-TRACKER credited DPO Alignment to LAB-005 (which
is GraphRAG; DPO is LAB-010) and LEARNING-PATHS-DETAILED invented
"LAB-004: Custom Quantization" twice (no such lab exists; LAB-004 is
ReAct Agents). Numbers-claims gates cannot see this class: the labels
carry no counts, only identities.

Registry = the labs' own frontmatter Titles on disk (LAB-000..014).
A label is checked when it carries a topic: `LAB-0NN: <topic>` (the
dash/space split between LAB-001..006 and LAB-007+ files is accepted
on both sides; a trailing `(...)` duration is stripped; labels without
a topic can't be checked - the claims-gate idiom of skipping unmatched
patterns on purpose).

Matching is word-based, tolerant of legitimate short forms (the census
showed they are the norm: "Docker & LLM" for "Docker & LLM
Fundamentals", "Agent Fleet" for "Multi-Agent Fleet", "Train Model
from Scratch" for "Train a Small Language Model from Scratch") and of
verb-form bridges ("Add knowledge graphs", "Fine-tune with QLoRA").
Each lab's signal words are its Title words plus a small extension
table; a topic scores against every lab, the best scorer must be the
labelled lab, and two findings:

  LB-01  wrong identity - the topic belongs to a different lab than
         the one labelled (the census class: certain navigation break)
  LB-02  unknown/ambiguous topic - no lab, or two labs, tie for best
         match; either teach the signal table the new short form or
         fix the label (change the copy -> teach the gate)
  LR-01  label points at a lab id that has no file on disk (the
         registry defines which ids exist)

    python scripts/qa/lab_registry_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LABEL_RE = re.compile(r"\bLAB[ -](\d{3}):\s+([^`|\]*.]+)")
DURATION_RE = re.compile(r"\s+\([^()]*\)\s*$")

LABS_DIR = Path("docs") / "learning-resources" / "labs"

# A topic outside this word-count band is prose wearing a label shape
# ("For LAB-000: Yes." is an FAQ answer, not a label) - skipped on
# purpose, the claims-gate idiom.
TOPIC_WORDS = (2, 8)

# Signal words beyond the lab's own Title words. Verb-form bridges and
# domain synonyms the Titles do not carry ("Add knowledge graphs" never
# says GraphRAG; "Fine-tune with QLoRA" never says LoRA verbatim).
EXTRA_SIGNALS: dict[str, set[str]] = {
    "LAB-000": {"docker", "verify", "installation"},
    "LAB-001": {"containerized", "deployment"},
    "LAB-002": {"retrieval"},
    "LAB-003": {"fine", "tune", "tuning", "qlora"},
    "LAB-004": {"agent"},
    "LAB-005": {"knowledge", "graph", "graphs"},
    "LAB-007": {"rag"},
    "LAB-008": {"agent", "fleet"},
    "LAB-010": {"align"},
    "LAB-011": {"multimodal", "vision"},
    "LAB-013": {"tool", "tools"},
}


def norm(text: str) -> set[str]:
    return set(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def load_registry(root: Path) -> dict[str, set[str]]:
    """LAB-0NN -> signal words, built from each lab file's Title."""
    registry: dict[str, set[str]] = {}
    for path in sorted((root / LABS_DIR).glob("LAB-*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'^Title:\s*"(.*)"\s*$', text, re.M)
        lab_id_m = re.match(r"LAB[ -](\d{3})", path.stem)
        if m is None or lab_id_m is None:
            continue
        lab_id = f"LAB-{lab_id_m.group(1)}"
        title = m.group(1)
        # Title carries its own "LAB 001:" prefix - keep only the topic
        title = re.sub(r"^LAB[ -]\d{3}:\s*", "", title)
        registry[lab_id] = norm(title) | EXTRA_SIGNALS.get(lab_id, set())
    return registry


def best_match(topic: str, registry: dict[str, set[str]]) -> list[str]:
    words = norm(topic)
    scores = {lab_id: len(words & signals)
              for lab_id, signals in registry.items()}
    top = max(scores.values(), default=0)
    if top == 0:
        return []
    return sorted(lab_id for lab_id, s in scores.items() if s == top)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    registry = load_registry(args.root)
    if not registry:
        print("LR-00 no lab Titles found under %s" % LABS_DIR.as_posix())
        return 1

    findings: list[str] = []
    checked = 0
    for path in sorted((args.root / "docs").rglob("*.md")):
        rel = path.relative_to(args.root).as_posix()
        for ln, line in enumerate(path.read_text(encoding="utf-8",
                                                 errors="replace").split("\n"), 1):
            for m in LABEL_RE.finditer(line):
                lab_id, topic = f"LAB-{m.group(1)}", DURATION_RE.sub("", m.group(2)).strip()
                n_words = len(topic.split())
                if not TOPIC_WORDS[0] <= n_words <= TOPIC_WORDS[1]:
                    continue  # prose wearing a label shape, not a label
                checked += 1
                if lab_id not in registry:
                    findings.append(
                        "%s:%d: LR-01 label points at unknown lab %s - %s"
                        % (rel, ln, lab_id, topic))
                    continue
                winners = best_match(topic, registry)
                if not winners:
                    findings.append(
                        "%s:%d: LB-02 unknown topic for %s - teach the "
                        "signal table or fix the label - %s"
                        % (rel, ln, lab_id, topic))
                elif len(winners) > 1:
                    findings.append(
                        "%s:%d: LB-02 ambiguous topic for %s (matches %s "
                        "equally) - teach the signal table or fix the "
                        "label - %s" % (rel, ln, lab_id,
                                        "/".join(winners), topic))
                elif winners[0] != lab_id:
                    findings.append(
                        "%s:%d: LB-01 wrong lab identity: '%s' is %s's "
                        "topic, not %s's - %s"
                        % (rel, ln, topic, winners[0], lab_id, topic))

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print("lab_registry_check: %d findings (%d labels checked against %d "
          "labs)" % (len(findings), checked, len(registry)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
