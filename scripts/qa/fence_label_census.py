#!/usr/bin/env python3
"""fence-label accuracy census (FLC-01) for Minder Academy.

A raw Dockerfile or nginx config block pasted into a bash/sh/shell
fence is a mislabel: the fence renders with shell highlighting and a
learner copying the block runs lines that are not shell. The correct
corpus idiom goes two ways - pure config gets its own label
(dockerfile/nginx), while config *written* from a shell script stays
bash inside a heredoc (cat > file << 'EOF'). This census separates
the two: a shell-labeled fence matching >= 4 Dockerfile directives
or >= 2 nginx directive markers with no shell tokens is a mislabel
candidate; fences carrying shell tokens count as correct embedded
generation.

Born from the tick-341 hygiene sweep that closed both backlog
relabel items as verified-clean: 4 nginx and 3 Dockerfile
bash-fence candidates were all heredoc-wrapped generation, and the
corpus already holds 12 nginx-labeled and 18 dockerfile-labeled
fences. Birth state - 699 shell-labeled fences, 0 dockerfile-raw,
0 nginx-raw, 3 dockerfile-embedded, 4 nginx-embedded - locked so a
future raw paste surfaces here.

Report mode - exit 0 by design; the census is an inventory, not a gate.

Run over the whole corpus:
    python scripts/qa/fence_label_census.py --root .

The fence parser is the tick-678 CommonMark canon state machine: the
opener's marker run is captured (f_char, f_len), a closer must repeat
the opener's character in a run at least as long, a different fence
character never closes, a non-closer marker line is fence content.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
SHELL_LABELS = {"bash", "sh", "shell"}

# any of these means the fence is a runnable shell script, not raw config
SHELL_TOKEN = re.compile(
    r"(^|\n)\s*(cat >|tee |<<\s*'EOF'|#!/bin/bash|#!/usr/bin/env bash"
    r"|sudo |docker |apt-get|apt install|pip install|uv pip|uv venv|uvx "
    r"|export |cd |mkdir |echo |curl |wget |source )", re.MULTILINE)

# Dockerfile directives matched at line start; >= 4 distinct = config
DOCKERF_RE = [re.compile(p, re.MULTILINE) for p in (
    r"^FROM\s+\S", r"^WORKDIR\s+", r"^COPY\s+", r"^RUN\s+",
    r"^ENV\s+\w+=", r"^EXPOSE\s+\d", r"^ENTRYPOINT\s",
    r"^CMD\s+\[", r"^ARG\s+\w")]

# nginx structural markers; >= 2 distinct = config
NGINX_RE = [re.compile(re.escape(m)) for m in
            ("server {", "location ", "proxy_pass", "upstream ",
             "http {")]


def fences(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_fence: tuple[str, int] | None = None
    label, buf, start = "", [], 0
    for i, line in enumerate(lines, 1):
        m = FENCE_OPEN.match(line)
        if m:
            f_char, f_len = m.group(1)[0], len(m.group(1))
            if in_fence:
                if f_char == in_fence[0] and f_len >= in_fence[1]:
                    in_fence = None  # true closer ends any block
                    if label in SHELL_LABELS:
                        yield start, label, buf
                    buf = []
                else:
                    buf.append(line)  # non-closer marker is content
            else:
                in_fence = (f_char, f_len)
                label, buf, start = m.group(2), [], i
        elif in_fence:
            buf.append(line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    df_raw = nx_raw = df_emb = nx_emb = 0
    n_sh = 0

    for path in sorted((args.root / "docs").rglob("*.md")):
        for _start, _label, buf in fences(path):
            joined = "\n".join(buf)
            if not joined.strip():
                continue
            n_sh += 1
            shell = bool(SHELL_TOKEN.search(joined))
            df = sum(1 for rx in DOCKERF_RE if rx.search(joined))
            nx = sum(1 for rx in NGINX_RE if rx.search(joined))
            if df >= 4:
                if shell:
                    df_emb += 1
                else:
                    df_raw += 1
            elif nx >= 2:
                if shell:
                    nx_emb += 1
                else:
                    nx_raw += 1

    print(f"fence_label_census (report): dockerfile-raw-in-shell "
          f"{df_raw}, nginx-raw-in-shell {nx_raw}, dockerfile-embedded "
          f"{df_emb}, nginx-embedded {nx_emb} across docs/ ({n_sh} "
          f"shell-labeled fences scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
