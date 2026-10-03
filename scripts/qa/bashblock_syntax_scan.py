#!/usr/bin/env python3
"""bashblock_syntax_scan - every ```bash fence must parse as shell (BB-01).

Policy: a fence labeled bash is a promise that the block is runnable shell.
This gate checks every non-empty bash-labeled fence with `bash -n` (parse
only, nothing executes) and fails on any block that does not parse.

Placeholder convention: doc placeholders inside shell commands use the
runnable ${VAR_NAME} form (e.g. docker logs ${CONTAINER_ID}), NOT the
man-page <name> style - angle brackets are input redirection in shell and
break copy-paste execution. The gate therefore expects zero <placeholder>
tokens in bash fences.

Non-shell content (keyboard shortcuts, benefit bullets, debugger sessions,
Prometheus queries, config file listings) lives in an honest fence label:
```text, ```promql, ```yaml, etc.

Implementation: dumps each bash fence to a temp file, runs one `bash -n`
pass over all of them in a single bash invocation (requires bash on PATH;
on Windows this means Git Bash), then maps failures back to document
locations.

Output: one finding per failing block, then a summary line:
    bashblock_syntax_scan: N findings across docs/
Exit code: 0 if N == 0, else 1.
"""
import argparse
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

FENCE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]),
                    help="repo root (default: two levels up)")
    args = ap.parse_args()
    docs = Path(args.root) / "docs"

    workdir = Path(tempfile.mkdtemp(prefix="bashgate_"))
    findings = []
    blocks = 0
    try:
        index = []
        for path in sorted(docs.rglob("*.md")):
            rel = path.relative_to(docs).as_posix()
            lines = path.read_text(encoding="utf-8").split("\n")
            in_fence = False
            lang = ""
            start = 0
            body = []
            for i, raw in enumerate(lines):
                m = FENCE.match(raw)
                if m:
                    if in_fence:
                        if lang == "bash":
                            src = textwrap.dedent("\n".join(body))
                            if src.strip():
                                blocks += 1
                                name = "%05d.sh" % blocks
                                (workdir / name).write_text(
                                    src, encoding="utf-8", newline="\n")
                                index.append((name, rel, start + 1))
                        in_fence = False
                        body = []
                    else:
                        in_fence = True
                        lang = m.group(2).lower()
                        start = i + 1
                        body = []
                    continue
                if in_fence:
                    body.append(raw)

        if not index:
            print("bashblock_syntax_scan: SKIP - no bash fences, nothing to check")
            return 0
        (workdir / "index.tsv").write_text(
            "\n".join("%s\t%s\t%d" % r for r in index), encoding="utf-8")

        # one bash invocation loops bash -n over every dumped block
        probe = (
            "for f in [0-9]*.sh; do\n"
            "  err=$(bash -n \"$f\" 2>&1) || "
            "printf 'FAIL|%s|%s\\n' \"$f\" "
            "\"$(printf '%s' \"$err\" | head -n 1)\"\n"
            "done\n"
        )
        r = subprocess.run(["bash", "-c", probe], cwd=workdir,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        for line in r.stdout.splitlines():
            if not line.startswith("FAIL|"):
                continue
            name, detail = line.split("|", 2)[1:]
            # strip the "<name>.sh: line N: " prefix bash prepends
            detail = re.sub(r"^[^:]+:\s*(line \d+:\s*)?", "", detail)
            findings.append((name, detail))

        lookup = dict((n, (rel, ln)) for n, rel, ln in index)
        for name, detail in findings:
            rel, ln = lookup[name]
            print("%s:%d: BB-01 bash fence does not parse: %s"
                  % (rel, ln, detail.encode("ascii", "backslashreplace")
                     .decode("ascii")))
    finally:
        for f in workdir.iterdir():
            f.unlink()
        workdir.rmdir()

    print("bashblock_syntax_scan: %d findings across docs/ (%d bash blocks checked)"
          % (len(findings), blocks))
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
