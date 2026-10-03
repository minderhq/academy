#!/usr/bin/env python3
"""census adjudication-note hygiene gate for the PROJECT-OMEGA curriculum.

The execution census's _meta contract says every non-clean outcome must be
adjudicated in the baseline before fence_exec_gate runs; this gate makes the
contract mechanical. A baseline row without a note is an unexplained
acceptance (the next reviewer re-litigates it), and a note without a row is
a stale annotation (it documents a fence that no longer fails) - 3501@162's
TIMEOUT row shipped with an empty note for many ticks until a hand audit
filled it, so born tick-544 with baseline 0/0.

CN-01  bad row with no note, or a note whose text strips to empty
CN-02  note key that references no bad row (orphan annotation)

Exit 0 when zero findings; exit 1 otherwise. Run over the whole baseline:
    python scripts/qa/census_note_gate.py --root .
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASELINE = "scripts/qa/accepted_exec_census.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    baseline = args.root / BASELINE
    if not baseline.exists():
        print("census_note_gate: SKIP - scripts/qa/accepted_exec_census.json not found, nothing to check")
        return 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    findings: list[str] = []
    rows = notes = 0
    for rel, entry in sorted(data.get("files", {}).items()):
        bad = entry.get("bad", {})
        note_map = entry.get("notes", {})
        rows += len(bad)
        notes += len(note_map)
        for line in sorted(bad):
            text = note_map.get(line, "").strip()
            if not text:
                findings.append(
                    f"{rel}:{line}: CN-01 accepted row [{bad[line]}] carries no "
                    "adjudication note - state why the census accepts it")
        for line in sorted(note_map):
            if line not in bad:
                findings.append(
                    f"{rel}:{line}: CN-02 orphan note documents no accepted row "
                    f"[{note_map[line][:60]}] - the row drained; drop the note")
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    n_files = len({f.rsplit(":", 2)[0] for f in findings})
    print(f"census_note_gate: {len(findings)} findings in {n_files} files "
          f"({rows} accepted rows / {notes} notes across "
          f"{len(data.get('files', {}))} baseline files)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
