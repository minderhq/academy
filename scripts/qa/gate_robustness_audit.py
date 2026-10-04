#!/usr/bin/env python3
"""Gate robustness audit: no QA gate may die ugly on hostile input.

The tick-637 lesson generalized. casecheck.py crashed with a bare
IndexError when a href segment was swallowed by OS path normalization -
the hard gate went down exactly when it was most needed and the fleet
printed 'no summary line'. Every other gate carries the same exposure:
a malformed fixture (unclosed fence, ragged table, invalid UTF-8,
absent corpus structure) reaching an unguarded parse path turns a
quality signal into a traceback.

Contract: each audited gate runs against a synthetic malformed tree
built in a temp dir (see FIXTURES). A gate under audit may
  - exit 0 (clean), or
  - exit nonzero WITH a diagnostic (it found hostile input and said so
    - the desired behavior), but it must NEVER
  - print a traceback (CRASH finding), or
  - hang (TIMEOUT finding).

Roster: every scripts/qa/*.py automatically (new gates join without
edits here), minus EXCLUDE:
  - quality_report.py      the orchestrator itself (would recurse)
  - feed_parity_check.py   spawns manifest_export child, output contract
  - fence_exec_gate.py     execute tree fences; runtime is minutes and
  - fence_exec_census.py   the synthetic tree is not an exec corpus
  - link_rot_check.py      network-dependent (external URL checks)
  - script_hygiene_scan.py audits the repo's own scripts dir, not a
                           content tree - out of contract by design
  - stale_fm_report.py     requires git history (git log), a temp dir
                           has none - out of contract by design
Gates whose argparse demands extra required args cannot be exercised
and are reported as argerror (a coverage hole, not a robustness
failure); EXTRA_ARGS maps known ones to their minimal invocation.

Exit 0 = every audited gate survived the hostile tree (no crash, no
timeout). Exit 1 = at least one CRASH/TIMEOUT finding, each named.

Usage:
    python scripts/qa/gate_robustness_audit.py [--root ROOT]
                                               [--scripts-dir DIR]
                                               [--timeout SECONDS]

Output is ASCII-escaped so it is safe on cp1254 consoles. Stdlib only.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

OWN_NAME = "gate_robustness_audit.py"

EXCLUDE = {
    "quality_report.py",
    "feed_parity_check.py",
    "fence_exec_gate.py",
    "fence_exec_census.py",
    "link_rot_check.py",
    "script_hygiene_scan.py",
    "stale_fm_report.py",
}

# Gates that need more than --root to run at all; minimal extra args.
EXTRA_ARGS = {}

# ---------------------------------------------------------------- fixtures
# Every fixture is hostile on purpose: it exercises an unguarded parse
# shape somewhere in the fleet. All embedded code is INERT (syntax
# errors, echo) - fixtures must never execute anything dangerous.

README = b"# probe\n\nA minimal entry doc so link-structure gates have an anchor.\n"

BROKEN_FM = (
    b"---\n"
    b"title: [unclosed\n"
    b"status: draft\n"
    # no closing --- : unterminated frontmatter block
    b"\nBody after an unterminated frontmatter block.\n"
)

RAGGED_TABLE = (
    b"# ragged\n\n"
    b"| a | b | c |\n"
    b"|---|---|\n"          # separator shorter than header
    b"| 1 | 2 |\n"          # row shorter than header
    b"| 1 | 2 | 3 | 4 |\n"  # row longer than header
    b"| only |\n"
)

UNCLOSED_FENCE = (
    b"# unclosed\n\n"
    b"```python\n"
    b"print('fence never closes')\n"
    b"# and the file just ends here\n"
)

WEIRD_LINKS = (
    b"# weird links\n\n"
    b"- [bare paren](()\n"
    b"- [bad escape](%zz.md)\n"
    b"- [space](a b.md)\n"
    b"- [up up](../..//x.md)\n"
    b"- [backslash](nested\\deep.md)\n"
    b"- [dotdot name](.../x.md)\n"
    b"- [trailing dot](name..md)\n"
    b"- [anchor only](#no-such-anchor)\n"
)

CRLF_FILE = b"# crlf\r\n\r\nWindows line endings, deliberately.\r\n"

EMPTY_FILE = b""

NO_NEWLINE = b"# no trailing newline, file ends mid-byte"

HEADINGS = (
    b"# top\n\n"
    b"### skipped level (H1 -> H3 jump)\n\n"
    b"## duplicate\n\n"
    b"text\n\n"
    b"## duplicate\n\n"
    b"##\n\n"  # empty heading
)

BAD_MERMAID = (
    b"# bad mermaid\n\n"
    b"```mermaid\n"
    b"graph TD\n"
    b"    A -->\n"       # edge with no target
    b"    --> B\n"
    b"```\n"
)

BAD_PY = (
    b"# bad python\n\n"
    b"```python\n"
    b"def broken(:\n"    # syntax error, inert - never executed here
    b"```\n"
)

BAD_HTML = (
    b"# bad html\n\n"
    b"<div><span>unclosed raw tags\n"
    b"<img src=\"\">\n"
)

INVALID_UTF8 = (
    b"# invalid utf-8\n\n"
    b"\xff\xfe stray bytes that break utf-8 decoding\n"
)

DEEP = (
    b"# deep\n\n"
    b"- [gone](gone.md)\n"
    b"- [nothing](#absent)\n"
    b"- [escape](../../outside.md)\n"
)

FIXTURES = {
    "README.md": README,
    "broken_fm.md": BROKEN_FM,
    "ragged_table.md": RAGGED_TABLE,
    "unclosed_fence.md": UNCLOSED_FENCE,
    "weird_links.md": WEIRD_LINKS,
    "crlf.md": CRLF_FILE,
    "empty.md": EMPTY_FILE,
    "no_newline.md": NO_NEWLINE,
    "headings.md": HEADINGS,
    "bad_mermaid.md": BAD_MERMAID,
    "bad_py.md": BAD_PY,
    "bad_html.md": BAD_HTML,
    "invalid_utf8.md": INVALID_UTF8,
    os.path.join("nested", "deep.md"): DEEP,
}


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def build_tree(root: str) -> None:
    for rel, data in FIXTURES.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path) or root, exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)


def roster(scripts_dir: str) -> list:
    names = sorted(
        n for n in os.listdir(scripts_dir)
        if n.endswith(".py") and n not in EXCLUDE and n != OWN_NAME
    )
    return names


def audit_gate(scripts_dir: str, root: str, name: str, timeout: int) -> dict:
    """Run one gate against the hostile tree; classify the outcome."""
    script = os.path.join(scripts_dir, name)
    cmd = [sys.executable, script, "--root", root] + EXTRA_ARGS.get(name, [])
    try:
        proc = subprocess.run(
            cmd, cwd=root, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "detail": "no output in %ds" % timeout}
    err = proc.stderr.decode("utf-8", errors="replace")
    out = proc.stdout.decode("utf-8", errors="replace")
    if "Traceback" in err:
        tail = [ln for ln in err.splitlines() if ln.strip()]
        # name the crash: last traceback frame + the error line
        frames = [ln for ln in tail if ln.startswith("  File ")]
        error_ln = tail[-1] if tail else "?"
        detail = (frames[-1].strip() + " | " + error_ln) if frames else error_ln
        return {"status": "CRASH", "detail": detail}
    if proc.returncode == 0:
        return {"status": "PASS", "detail": ""}
    if err.lstrip().startswith("usage:") and "error:" in err:
        first = [ln for ln in err.splitlines() if "error:" in ln]
        return {"status": "ARGERROR", "detail": first[0].strip() if first else "argparse"}
    first = [ln for ln in (out + err).splitlines() if ln.strip()]
    return {"status": "DIAG", "detail": first[0][:100] if first else "rc=%d" % proc.returncode}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # The fleet runner passes --root to EVERY gate; the audit is a gate
    # too, so it must accept it (its own ARGERROR lesson, fleet smoke).
    parser.add_argument("--root", type=str, default=None,
                        help="repo root; scripts dir derives from it "
                             "unless --scripts-dir overrides")
    parser.add_argument("--scripts-dir", type=str, default=None,
                        help="gate scripts dir (default: <root>/scripts/qa "
                             "or alongside this script)")
    parser.add_argument("--timeout", type=int, default=90,
                        help="per-gate timeout in seconds (default 90)")
    args = parser.parse_args()
    if args.scripts_dir:
        scripts_dir = os.path.abspath(args.scripts_dir)
    else:
        candidate = (os.path.join(os.path.abspath(args.root), "scripts", "qa")
                     if args.root else None)
        scripts_dir = (candidate if candidate and os.path.isdir(candidate)
                       else os.path.dirname(os.path.abspath(__file__)))

    counts = {"PASS": 0, "DIAG": 0, "ARGERROR": 0, "CRASH": 0, "TIMEOUT": 0}
    findings = []
    roster_names = roster(scripts_dir)
    print(esc("gate_robustness_audit: %d gates on the hostile tree" % len(roster_names)))
    with tempfile.TemporaryDirectory(prefix="academy_robustness_") as tmp:
        build_tree(tmp)
        for name in roster_names:
            res = audit_gate(scripts_dir, tmp, name, args.timeout)
            counts[res["status"]] += 1
            marker = {"PASS": ".", "DIAG": "d", "ARGERROR": "a",
                      "CRASH": "C", "TIMEOUT": "T"}[res["status"]]
            print(marker, end="", flush=True)
            if res["status"] in ("CRASH", "TIMEOUT"):
                findings.append((name, res["status"], res["detail"]))
    print()
    print()
    print(esc("=== ROBUSTNESS FINDINGS (traceback or hang = the gate died ugly): %d ==="
              % len(findings)))
    for name, status, detail in findings:
        print(esc(" - %s  %s  %s" % (name, status, detail)))
    print()
    print(esc("pass=%d diag=%d argerror=%d crash=%d timeout=%d  (roster %d, excluded %d)"
              % (counts["PASS"], counts["DIAG"], counts["ARGERROR"],
                 counts["CRASH"], counts["TIMEOUT"],
                 len(roster_names), len(EXCLUDE))))
    ok = not findings
    print("gate_robustness_audit: %d gates audited, %d crash, %d timeout -> %s"
          % (len(roster_names), counts["CRASH"], counts["TIMEOUT"],
             "PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
