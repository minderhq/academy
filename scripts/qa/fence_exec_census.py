#!/usr/bin/env python3
"""Smoke-execution census: actually run every ```python fence, per file.

The fourth rung of content testing - syntax (CB-01) proves a fence
parses, fence_import_check proves its imports resolve, fence_namecheck
proves its names resolve - this census asks whether the code RUNS.
Each markdown file's python fences execute top-to-bottom in one
namespace (the learner's exact experience), one subprocess per file
with a hard timeout, cwd a throwaway directory so file-writing fences
cannot touch the repo.

Report-mode census (exit 0 always). Children run with PYTHONUTF8=1 -
the learner baseline ENVIRONMENT-SETUP teaches (PEP 540 UTF-8 mode,
PEP 686's Python 3.15 default) - so emoji-print fences classify by
their real defects, not by a legacy cp1252 pipe. `--json-out PATH`
emits per-file machine entries (mtime/size + per-fence class rows)
for fence_exec_gate's baseline seeding; `--limit N` partitions the
corpus across parallel runs. Findings classify into:

  OK              ran clean
  CENSUS          NameError on a name the file's UN census already
                  accepts (fragment convention - expected, not signal)
  UN-LEAK         NameError outside the census (would contradict the
                  UN gate - investigate before believing)
  ENV-GAP         ModuleNotFoundError for a module the QA environment
                  does not install (sentence_transformers, trl, ...)
  SIDE-EFFECT     network / service / filesystem failures at runtime
                  (ConnectionError, OSError on real paths, qdrant
                  refused, ...) - the fence needs a server, not a fix
  INTERACTIVE     EOFError from input() with stdin closed
  EXIT-CALL       SystemExit / exit() in fence body
  TIMEOUT         file exceeded the subprocess timeout; the stderr
                  heartbeat (RUNNER prints `HB <line>` before every
                  fence) attributes the hang to the fence that was
                  mid-execution - typically a by-design server start
                  (uvicorn.run), a daemon loop (prometheus exporter),
                  a real multi-GB model load, or plt.show() holding
                  a GUI window; fences after the hang are unknown
  CODE-SIGNAL     any other exception (TypeError, ValueError,
  (numbered)      AttributeError, ...) - the gold class: example code
                  that is broken as written
  RUNNER-CRASH    the runner itself died mid-file (bad rc or non-JSON
                  stdout); the heartbeat attributes the last fence it
                  reached - the classic cause is a fence hijacking
                  sys.stdout and dying inside its own redirect, which
                  swallows the runner's final JSON print too

The classification pass turns this into the next born-at-zero gate's
accepted classes; drain the CODE-SIGNAL class first.

Adjudicated over the full corpus (260 files, tick-532): UN-LEAK is
almost never a gate contradiction - fence_namecheck and runtime agree.
The UN-LEAKs are downstream cascades of an upstream fence that died on
a missing optional package or a service call BEFORE binding the name
the later fence references (the death itself is often swallowed by the
fence's own try/except or hidden because ENV-GAP is not a signal line).
SIDE-EFFECT covers both the raw connection family and the service
exception types (OpenAIError, ResponseError, ResponseHandlingException,
ServiceUnavailable, NotFoundError, _InactiveRpcError): those fences
need an API key, an Ollama daemon, a Neo4j/Qdrant server or a GPU -
they are environment requirements, not code defects. The intentional
error-teaching demos (einsum/matmul shape traps in phase2's README,
etc.) land in CODE-SIGNAL; the born-at-zero gate accepts them through
adjudication notes in accepted_exec_census.json - the census cannot
read pedagogical intent.

    python scripts/qa/fence_exec_census.py --root .
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fence_namecheck import ACCEPTED  # single source of truth for the UN census

FENCE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")
PYTHON_LANGS = ("python", "py", "python3")
FILE_TIMEOUT = 90  # seconds; first torch import alone can take 10-20s

RUNNER = r'''
import json, sys
path = sys.argv[1]
FENCE = r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$"
import re
lines = open(path, encoding="utf-8").read().split("\n")
fences = []
in_fence = False
lang = ""
start = 0
body = []
for i, raw in enumerate(lines):
    m = re.match(FENCE, raw)
    if m:
        if in_fence:
            in_fence = False
            if lang in ("python", "py", "python3"):
                import textwrap
                src = textwrap.dedent("\n".join(body))
                if src.strip():
                    fences.append((start + 1, src))
            body = []
        else:
            in_fence = True
            lang = m.group(2).lower()
            start = i
            body = []
        continue
    if in_fence:
        body.append(raw)
ns = {"__name__": "__main__"}
out = []
for line_no, src in fences:
    print(f"HB {line_no}", file=sys.stderr, flush=True)
    try:
        exec(compile(src, f"fence@line{line_no}", "exec"), ns)
        out.append([line_no, "OK", "", ""])
    except SystemExit as e:
        out.append([line_no, "EXIT-CALL", str(e.code), ""])
    except BaseException as e:
        name = getattr(e, "name", "") or ""
        out.append([line_no, type(e).__name__, str(e)[:200], str(name)])
# sentinel prefix: a fence printing without a trailing newline (input()
# prompts do exactly that) glues its output onto this line - the parent
# must find the marker, not trust the last line
print("CENSUS_JSON:" + json.dumps(out))
'''


def has_python_fence(path: Path) -> bool:
    in_fence = False
    lang = ""
    for raw in path.read_text(encoding="utf-8", errors="replace").split("\n"):
        m = FENCE.match(raw)
        if m:
            if in_fence:
                if lang in PYTHON_LANGS:
                    return True
                in_fence = False
            else:
                in_fence = True
                lang = m.group(2).lower()
    return False


def classify(exc: str, detail: str, name: str, rel: str) -> str:
    if exc == "OK":
        return "OK"
    if exc == "EXIT-CALL":
        return "EXIT-CALL"
    if exc == "ModuleNotFoundError":
        return f"ENV-GAP:{name or detail}"
    if exc == "ImportError" and "pip install" in detail:
        # e.g. transformers' "pip install accelerate" style requirements -
        # the same environment-requirement class as a missing module
        return f"ENV-GAP:{(name or detail)[:60]}"
    if exc == "NameError":
        if name and name in ACCEPTED.get(rel, frozenset()):
            return "CENSUS"
        return "UN-LEAK"
    if exc in ("EOFError",):
        return "INTERACTIVE"
    if exc in ("ConnectionError", "TimeoutError", "OSError", "ConnectionRefusedError",
               "ConnectionAbortedError", "ConnectionResetError", "SocketError",
               "URLError", "HTTPError", "SSLError",
               "OpenAIError", "ResponseError", "ResponseHandlingException",
               "ServiceUnavailable", "NotFoundError", "_InactiveRpcError"):
        return "SIDE-EFFECT"
    return f"CODE-SIGNAL:{exc}"


def run_file(path: Path, rel: str, timeout: int, tmp: str) -> tuple[dict, list[str]]:
    """Execute one file's python fences in a throwaway-cwd subprocess.

    Returns the machine entry for the born-at-zero gate's baseline -
    {"mtime", "size", "rows": {fence-line: class}, with TIMEOUT /
    RUNNER-CRASH rows fence-anchored via the stderr heartbeat} - plus
    the report lines for its non-clean rows.
    """
    entry: dict = {"mtime": path.stat().st_mtime, "size": path.stat().st_size,
                   "rows": {}}
    report: list[str] = []
    proc = subprocess.Popen(
        [sys.executable, "-c", RUNNER, str(path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", errors="replace", cwd=tmp,
        stdin=subprocess.DEVNULL,
        env=dict(os.environ, PYTHONUTF8="1"),
    )  # PYTHONUTF8=1: the learner baseline ENVIRONMENT-SETUP teaches
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # tree-kill: a hung fence may have spawned children holding the
        # stdout pipe open; killing only the direct child would leave
        # communicate() blocked forever on Windows
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True)
        out, err = proc.communicate()
        timed_out = True
    if timed_out:
        # the RUNNER's heartbeat shows which fence was mid-execution
        hbs = [l for l in (err or "").split("\n") if l.startswith("HB ")]
        at = hbs[-1].split()[1] if hbs else "?"
        entry["rows"][at] = "TIMEOUT"
        report.append(f"  {rel}:{at}: TIMEOUT after {timeout}s")
        return entry, report
    try:
        # the sentinel may sit mid-line: a fence printing an input()
        # prompt without a trailing newline glues it in front
        jline = next(l for l in reversed((out or "").splitlines())
                     if "CENSUS_JSON:" in l)
        rows = json.loads(jline.split("CENSUS_JSON:", 1)[1])
    except (StopIteration, json.JSONDecodeError):
        # attribute via the heartbeat like TIMEOUT: rc=0 with no JSON
        # usually means a fence hijacked sys.stdout and died inside
        # its own redirect (LAB-004's CodeExecutorTool did exactly
        # that), so the last HB fence swallowed the runner's output
        hbs = [l for l in (err or "").split("\n") if l.startswith("HB ")]
        at = hbs[-1].split()[1] if hbs else "?"
        entry["rows"][at] = "RUNNER-CRASH"
        report.append(f"  {rel}:{at}: RUNNER-CRASH rc={proc.returncode}"
                      f" {(err or '').strip()[:200]}")
        return entry, report
    for line_no, exc, detail, name in rows:
        cls = classify(exc, detail, name, rel)
        entry["rows"][str(line_no)] = cls
        if cls not in ("OK", "CENSUS"):
            report.append(f"  {rel}:{line_no}: {cls} {detail}")
    return entry, report


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--timeout", type=int, default=FILE_TIMEOUT)
    parser.add_argument("--from-index", type=int, default=0,
                        help="skip the first N targets (resume after a killed run)")
    parser.add_argument("--limit", type=int, default=0,
                        help="process at most N targets from --from-index (partition runs)")
    parser.add_argument("--json-out", type=Path, default=None,
                        help="write per-file machine entries for the gate's baseline seeding"
                             " (rewritten after every file, so a killed run keeps its results)")
    args = parser.parse_args()
    args.root = args.root.resolve()  # children run with cwd=tmp: targets must be absolute
    docs = args.root / "docs"
    targets = [p for p in sorted(docs.rglob("*.md")) if has_python_fence(p)]
    if args.limit > 0:
        targets = targets[args.from_index:args.from_index + args.limit]
    elif args.from_index:
        targets = targets[args.from_index:]
    print(f"fence_exec_census: executing {len(targets)} files"
          f" (timeout {args.timeout}s each)", flush=True)
    tally: dict[str, int] = {}
    signal_files: list[str] = []
    entries: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="omega_exec_") as tmp:
        for n, path in enumerate(targets, 1):
            rel = path.relative_to(args.root).as_posix()
            entry, report = run_file(path, rel, args.timeout, tmp)
            entries[rel] = entry
            if args.json_out:
                args.json_out.write_text(
                    json.dumps(entries, indent=1), encoding="utf-8")
            for cls in entry["rows"].values():
                tally[cls] = tally.get(cls, 0) + 1
            if report:
                signal_files.extend(report)
                print("\n".join(report), flush=True)
            print(f"[{n}/{len(targets)}] {rel}: {len(entry['rows'])} fences"
                  f"{' BAD=' + str(len(report)) if report else ''}", flush=True)
    print("--- signals ---")
    for line in signal_files:
        print(line)
    print("--- tally ---")
    for cls, count in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"{cls}: {count}")
    if args.json_out:
        print(f"fence_exec_census: {len(entries)} entries written to {args.json_out}")
    print("fence_exec_census: report-mode census (exit 0 by design)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
