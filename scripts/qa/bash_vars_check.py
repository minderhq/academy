#!/usr/bin/env python3
"""Undefined shell variable gate (BB-02) for the Minder Academy
corpus.

The shell counterpart of PY-01: a plain $VAR or bare-braced
${VAR...} load inside a ```bash fence that is stored nowhere - not
in the fence, not in any other bash fence of the same document (the
established cross-fence fragment idiom), not a shell builtin or
positional - is reported. Stores are recognized as: assignments and
exports at a command-delimiter boundary (line start, after ; & |,
any indentation), for-in loop variables, the read/local/declare/
readonly/export/select family, systemd Environment= unit directives
(which populate the names they set), and the standard os-release
keys once a fence sources /etc/os-release.

BB-02  a bash-fence load of a shell variable that is undefined.

Scoped to the same name-slip class as PY-01/PY-02, not the fragment
flood: guarded default idiom (${VAR:-def}) tolerates absence by
design and is not reported; template placeholders - the corpus
convention sanctioned by BB-01's no-<placeholder> policy, where the
reader substitutes their own value - are absorbed as reasoned
(rel, name) accepts, as are nginx runtime variables in the
bash-labeled nginx config fragments (LAB-001, TUTORIAL-005 reverse
proxy) and reader-environment promises. Birth history: tick-335
census (plain-$ only: 697 fences, 22 distinct -> 2 drained) then
tick-336 full predicate adding bare-braced loads (38 distinct) -> 3
drained (two usage lines printing an undefined variable, one
compose env promise made fail-loud), os-release + systemd stores
recognized in-gate, 39 hits absorbed as accepts in the recorded FP
classes - locked baseline 0 at birth.

Out of scope: fence parseability (BB-01, bash -n), guarded idiom
(by design), <placeholder> form (BB-01 bans it). Lexical only - no
shell is invoked.

Run over the whole corpus:
    python scripts/qa/bash_vars_check.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^ {0,3}```(\w*)\s*$")

# assignment/export at a command-delimiter boundary (line start or
# after ; & |), any indentation - (?!=) keeps == comparisons out
STORE_ASSIGN = re.compile(
    r"(?:(?:^|[;&|])\s*)(?:export\s+)?"
    r"([A-Za-z_][A-Za-z0-9_]*)\+?=(?!=)")
STORE_FOR = re.compile(r"\bfor\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\b")
STORE_READ = re.compile(
    r"\b(?:read|local|declare|readonly|export|select)\s+"
    r"(?:-[a-zA-Z]+\s+)*([A-Za-z_][A-Za-z0-9_]*)")
# systemd unit directive: Environment="NAME=..." / Environment=NAME=
STORE_ENVDIR = re.compile(r"\bEnvironment=\\?\"?([A-Za-z_][A-Za-z0-9_]*)=")
# sourcing /etc/os-release populates its standard keys
OS_RELEASE_SOURCE = re.compile(
    r"(?:^|[\s(])(?:\.|source)\s+\S*os-release\b")
OS_RELEASE_KEYS = {
    "ID", "ID_LIKE", "NAME", "PRETTY_NAME", "VERSION", "VERSION_ID",
    "VERSION_CODENAME", "BUILD_ID", "VARIANT", "VARIANT_ID",
    "CPE_NAME", "HOME_URL", "SUPPORT_URL", "BUG_REPORT_URL",
    "ANSI_COLOR", "LOGO", "URL",
}

# (?![A-Za-z0-9_]) after the name blocks backtracking so a guarded
# ${NAME:-d} cannot shrink into a fake short plain-braced name
BRACED_GUARDED = re.compile(
    r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?![A-Za-z0-9_])[:?+=-]")
BRACED_PLAIN = re.compile(
    r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?![A-Za-z0-9_])(?![:?+=-])")
LOAD_PLAIN = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")

SPECIALS = {
    "?", "#", "@", "*", "$", "!", "-", "0", "1", "2", "3", "4", "5",
    "6", "7", "8", "9",
    "BASH", "BASH_VERSION", "BASH_VERSINFO", "BASHPID", "SHLVL",
    "PWD", "OLDPWD", "UID", "EUID", "HOME", "PATH", "USER", "SHELL",
    "TERM", "LANG", "LC_ALL", "HOSTNAME", "HOSTTYPE", "MACHTYPE",
    "OSTYPE", "SECONDS", "LINENO", "FUNCNAME", "REPLY", "IFS",
    "PPID", "RANDOM", "PS1", "PS2", "PS3", "PS4", "OPTARG", "OPTIND",
}

# (doc relpath, undefined name) -> accepted FP class, with reason.
# Groups share a reason; the flat dict stays the lookup form.
_NGINX = ("nginx runtime variable: bash-labeled nginx config "
          "fragment, not shell code (reverse-proxy sections)")
_TEMPLATE = ("template placeholder: reader substitutes their own "
             "value before running (BB-01 no-<placeholder> idiom)")
_ENVPROMISE = ("environment promise: reader exports their own value "
               "before running")

_GROUPS: list[tuple[str, str, str]] = [
    ("docs/learning-resources/labs/LAB-001-Docker-LLM.md", _NGINX,
     "remote_addr host proxy_add_x_forwarded_for"),
    ("docs/learning-resources/tutorials/"
     "TUTORIAL-005-Production-Deployment.md", _NGINX,
     "remote_addr host proxy_add_x_forwarded_for binary_remote_addr "
     "body_bytes_sent http_referer http_user_agent "
     "http_x_forwarded_for remote_user request status time_local "
     "request_uri scheme server_name"),
    ("docs/learning-resources/cheat-sheets/"
     "CHEAT-SHEET-001-Docker.md", _TEMPLATE,
     "CONTAINER_ID CONTAINER PORT"),
    ("docs/learning-resources/cheat-sheets/"
     "CHEAT-SHEET-003-Git.md", _TEMPLATE,
     "COMMIT_HASH MERGE_COMMIT_HASH HASH1 HASH2"),
    ("docs/learning-resources/cheat-sheets/"
     "CHEAT-SHEET-004-Linux.md", _TEMPLATE,
     "PID"),
    ("docs/learning-resources/troubleshooting/"
     "TROUBLESHOOTING-Common-Issues.md", _TEMPLATE,
     "PORT PID CONTAINER_NAME"),
    ("docs/learning-resources/tutorials/"
     "TUTORIAL-002-Docker-Essentials.md", _TEMPLATE,
     "PORT IMAGE IMAGE_ID CONTAINER_ID NAME"),
    ("docs/00-META/RESOURCES.md", _TEMPLATE,
     "REPO"),
    ("docs/phases/phase1-infra/1300-kubernetes/README.md", _TEMPLATE,
     "POD_NAME SERVICE_IP"),
    ("docs/phases/phase1-infra/1100-network/"
     "1101-Fiber-GPON-Modem.md", _ENVPROMISE,
     "VPS_IP WAN_IFACE"),
    ("docs/phases/phase1-infra/1200-virtualization/"
     "1202-TB3-UT3G-Passthrough.md", _TEMPLATE,
     "UUID"),
    ("docs/phases/phase6-rag/6400-vector-databases/"
     "6401-Qdrant-Setup.md", _TEMPLATE,
     "NAME"),
]
ACCEPTED: dict[tuple[str, str], str] = {
    (rel, n): reason
    for rel, reason, names in _GROUPS
    for n in names.split()
}


def fences(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_fence, label, buf, start = False, "", [], 0
    for i, line in enumerate(lines, 1):
        m = FENCE_OPEN.match(line)
        if not in_fence and m:
            in_fence, label, buf, start = True, m.group(1), [], i
        elif in_fence and re.match(r"^ {0,3}```", line):
            in_fence = False
            if label == "bash":
                yield start + 1, "\n".join(buf)
            buf = []
        elif in_fence:
            buf.append(line)


def stores_of(code: str) -> set[str]:
    s: set[str] = set()
    for line in code.splitlines():
        if line.lstrip().startswith("#"):
            continue
        for p in (STORE_ASSIGN, STORE_FOR, STORE_READ, STORE_ENVDIR):
            for m in p.finditer(line):
                s.add(m.group(1))
    return s


def loads_of(code: str) -> tuple[set[str], dict[str, int]]:
    """Plain-$ and bare-braced load names -> first line of each."""
    plain: set[str] = set()
    braced: dict[str, int] = {}
    for ln, line in enumerate(code.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        line = BRACED_GUARDED.sub("", line)
        for m in BRACED_PLAIN.finditer(line):
            braced.setdefault(m.group(1), ln)
        line = BRACED_PLAIN.sub("", line)
        for m in LOAD_PLAIN.finditer(line):
            plain.add(m.group(1))
    return plain, braced


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    n_bash = 0

    for path in sorted((args.root / "docs").rglob("*.md")):
        rel = path.relative_to(args.root).as_posix()
        fl = [(ln, c) for ln, c in fences(path) if c.strip()]
        if not fl:
            continue
        n_docs += 1
        doc_stores: set[str] = set()
        os_release = False
        parsed = []
        for lineno, code in fl:
            doc_stores |= stores_of(code)
            if OS_RELEASE_SOURCE.search(code):
                os_release = True
            parsed.append((lineno, code))
        n_bash += len(parsed)
        visible = doc_stores | SPECIALS
        if os_release:
            visible |= OS_RELEASE_KEYS

        for lineno, code in parsed:
            plain, braced = loads_of(code)
            for nm in sorted(plain | set(braced)):
                if nm in visible or (rel, nm) in ACCEPTED:
                    continue
                first = braced.get(nm)
                if first is None:
                    # plain $NAME - find its first non-comment line
                    first = next(
                        i + 1 for i, l in enumerate(code.splitlines())
                        if not l.lstrip().startswith("#")
                        and nm in LOAD_PLAIN.findall(
                            BRACED_GUARDED.sub("", l)))
                lines = code.splitlines()
                where = " | ".join(
                    lines[max(0, first - 2): first])[:90]
                findings.append(
                    f"BB-02 {rel}:{lineno} [BASH] '${nm}' is an "
                    f"undefined shell variable near: {where}")

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"bash_vars_check: {len(findings)} BB-02 finding(s) across "
          f"{n_docs} docs, {n_bash} bash fences in docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
