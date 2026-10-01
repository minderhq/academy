#!/usr/bin/env python3
"""fence_exec_gate: the execution census hardened into a born-at-zero gate.

The content-testing chain's contract closes here: syntax (CB-01),
imports, names (fence_namecheck) and now EXECUTION. Every non-clean
outcome the census can produce must be adjudicated in
scripts/qa/accepted_exec_census.json BEFORE this gate runs; anything
new - a fence that newly raises, hangs, crashes the runner, or dies on
the environment - fails the run.

Fast path: the baseline stores each file's mtime/size, so an unchanged
corpus is stat-only; the full corpus executes only during baseline
seeding and after content edits.

Acceptance model (baseline "bad" rows, each adjudicated):

  OK / CENSUS          clean (CENSUS = accepted fragment-convention NameError)
  ENV-GAP:*            optional package the QA environment does not install
  SIDE-EFFECT          needs a service / network / API key / docker / GPU
  INTERACTIVE          input() demo with stdin closed
  EXIT-CALL            intentional sys.exit demo
  TIMEOUT              by-design hang (server start, multi-GB model load,
                       GUI hold, daemon loop) or a disk-bound file
  CODE-SIGNAL:*        triaged through "notes" - the genuine defect classes
                       were drained (ticks 535-536: stdout hijack, infinite
                       chunk loop, retired pipeline tasks); what remains is
                       documented, e.g. intentional error-teaching demos
  UN-LEAK              downstream cascade of an upstream env-gap death
                       (runtime otherwise agrees with fence_namecheck)

FLAKY_FAMILY {TIMEOUT, CODE-SIGNAL:RuntimeError}: the disk-bound
datasets-writer fences flip between a fast RuntimeError (os error 112)
and a timeout run to run; the two are interchangeable at an accepted
line.

Policies:
  - one retry: a fresh TIMEOUT or RUNNER-CRASH re-runs the file once
    before failing (load-flake protection)
  - improvements pass: an accepted row that no longer reproduces is
    reported, not failed; refresh the baseline with --update
  - --update re-blesses dirty files (mtime/size + bad rows), keeps
    notes whose row still holds, and prunes stale entries; run it
    deliberately, after reviewing what changed

    python scripts/qa/fence_exec_gate.py --root .             # check
    python scripts/qa/fence_exec_gate.py --root . --update    # re-bless
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fence_exec_census as census  # noqa: E402

BASELINE = Path(__file__).resolve().parent / "accepted_exec_census.json"

# machine-load-sensitive family: the disk-bound datasets-writer fences
# flip between fast RuntimeError (os error 112) and TIMEOUT run to run
FLAKY_FAMILY = {"TIMEOUT", "CODE-SIGNAL:RuntimeError"}
CLEAN = ("OK", "CENSUS")
HANGS = ("TIMEOUT", "RUNNER-CRASH")


def is_bad(cls: str) -> bool:
    return cls not in CLEAN


def same_accepted(new: str, old: str) -> bool:
    return new == old or (new in FLAKY_FAMILY and old in FLAKY_FAMILY)


def bad_rows(entry: dict) -> dict:
    return {line: cls for line, cls in entry["rows"].items() if is_bad(cls)}


def sort_key(line: str):
    return (len(line), line)  # numeric-ish order for fence-line keys


def seed(parts: list[str]) -> int:
    """Merge census --json-out partition files into the baseline."""
    files: dict = {}
    for part in parts:
        for rel, entry in json.loads(Path(part).read_text(encoding="utf-8")).items():
            files[rel] = {
                "mtime": entry["mtime"], "size": entry["size"],
                "bad": {l: c for l, c in entry["rows"].items() if is_bad(c)},
            }
    baseline = {
        "_meta": {
            "contract": "every non-clean execution outcome must be adjudicated "
                        "here before fence_exec_gate runs; new rows fail",
            "family_equivalence": sorted(FLAKY_FAMILY),
            "children": "census subprocesses run with PYTHONUTF8=1 (the "
                        "learner baseline ENVIRONMENT-SETUP teaches)",
        },
        "files": dict(sorted(files.items())),
    }
    BASELINE.write_text(json.dumps(baseline, indent=1), encoding="utf-8")
    bad_total = sum(len(f["bad"]) for f in files.values())
    print(f"fence_exec_gate: seeded {len(files)} files,"
          f" {bad_total} accepted rows -> {BASELINE.name}")
    print(f"fence_exec_gate: baseline seeded ({len(files)} files);"
          f" adjudicate the rows in its notes next")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--timeout", type=int, default=census.FILE_TIMEOUT)
    parser.add_argument("--update", action="store_true",
                        help="re-bless dirty files into the baseline")
    parser.add_argument("--force-file", action="append", default=[],
                        metavar="REL",
                        help="re-execute this file even if unchanged (repeatable)")
    parser.add_argument("--seed", nargs="+", metavar="PART.json",
                        help="merge census --json-out files into the baseline, exit")
    args = parser.parse_args()
    if args.seed:
        return seed(args.seed)
    args.root = args.root.resolve()

    if not BASELINE.exists():
        print(f"fence_exec_gate: baseline missing: {BASELINE.name}")
        print("fence_exec_gate: seed with census partition runs (--json-out)"
              " then fence_exec_gate --seed")
        return 1
    base = json.loads(BASELINE.read_text(encoding="utf-8")).get("files", {})
    docs = args.root / "docs"
    live = {p.relative_to(args.root).as_posix(): p
            for p in sorted(docs.rglob("*.md")) if census.has_python_fence(p)}

    dirty = [rel for rel, p in live.items()
             if rel in args.force_file
             or rel not in base
             or base[rel].get("mtime") != p.stat().st_mtime
             or base[rel].get("size") != p.stat().st_size]
    stale = sorted(rel for rel in base if rel not in live)

    violations: list[str] = []
    improvements: list[str] = []
    reblessed: dict = {}
    with tempfile.TemporaryDirectory(prefix="omega_gate_") as tmp:
        for rel in dirty:
            path = live[rel]
            old = base.get(rel, {})
            old_bad = old.get("bad", {})
            entry, _ = census.run_file(path, rel, args.timeout, tmp)
            new_bad = bad_rows(entry)
            # one-retry flake policy: a hang the baseline does not accept
            # gets a second chance before failing
            fresh_hangs = [l for l, c in new_bad.items()
                           if c in HANGS
                           and not (l in old_bad and same_accepted(c, old_bad[l]))]
            if fresh_hangs:
                entry, _ = census.run_file(path, rel, args.timeout, tmp)
                new_bad = bad_rows(entry)
            for line, cls in sorted(new_bad.items(), key=lambda kv: sort_key(kv[0])):
                old_cls = old_bad.get(line)
                if old_cls is not None and same_accepted(cls, old_cls):
                    continue
                if old_cls is None:
                    violations.append(f"VIOLATION {rel}:{line}: {cls} (new)")
                else:
                    violations.append(f"CHANGE {rel}:{line}: {old_cls} -> {cls}")
            for line, cls in sorted(old_bad.items(), key=lambda kv: sort_key(kv[0])):
                now = entry["rows"].get(line)
                if now is not None and now in CLEAN:
                    improvements.append(f"IMPROVED {rel}:{line}: {cls}"
                                        " no longer reproduces")
            reblessed[rel] = {
                "mtime": entry["mtime"], "size": entry["size"], "bad": new_bad,
            }
            notes = {l: t for l, t in old.get("notes", {}).items()
                     if new_bad.get(l) == old_bad.get(l)}
            if notes:
                reblessed[rel]["notes"] = notes

    if args.update:
        # prune stale entries: a baseline file whose markdown is gone
        # (or no longer fences python) has nothing left to accept
        files = {rel: base[rel] for rel in base
                 if rel in live and rel not in reblessed}
        files.update(reblessed)
        baseline = {"_meta": json.loads(BASELINE.read_text(encoding="utf-8"))["_meta"],
                    "files": dict(sorted(files.items()))}
        BASELINE.write_text(json.dumps(baseline, indent=1), encoding="utf-8")

    for v in violations:
        print(v)
    for i in improvements:
        print(i)
    action = "re-blessed" if args.update else "re-executed (not blessed)"
    print(f"fence_exec_gate: {len(live)} fence files, {len(dirty)} dirty"
          f" ({action}), {len(stale)} stale baseline entries")
    if violations:
        print(f"fence_exec_gate: FAIL {len(violations)} new/changed defect(s)"
              " - born-at-zero violated; fix the content or adjudicate in"
              " accepted_exec_census.json")
        return 1
    tail = f", {len(improvements)} improved" if improvements else ""
    print(f"fence_exec_gate: PASS - 0 new defects{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
