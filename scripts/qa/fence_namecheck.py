#!/usr/bin/env python3
"""undefined-name scanner for python fences (report mode).

The langchain-modernization epic documented a census blind spot: fences
that USE names never imported or defined raise NameError at runtime but
have no broken import line to flag (UC-003: 8 latent NameErrors; 7401:
3 fences using datetime without importing it). codeblock_syntax_scan
proves the fence PARSES; this scanner asks whether the names it uses are
bound anywhere.

Model per .md file, two passes: pass 1 collects every name bound by ANY
python fence in the document (import asnames, assignments, defs, params,
for/with/except/comprehension targets); pass 2 sorts every unbound Load
name into two codes (2026-09-29 triage: 794 findings / 99 files / 462
distinct names split into 2 real module accesses, 38 placeholder idiom
and 754 teaching fragments):

  NC-01  module access without import - `name.attr` where name is a
         known module name (stdlib + the installed ML stack) and no
         fence in the document imports it. Always a real NameError for
         the student who runs the fence: asyncio.gather without
         `import asyncio`, uuid.uuid4 without `import uuid`. The two
         findings the original scanner had buried under its own noise.
  NC-02  fragment idiom - any other unbound name. Accepted by design:
         the corpus teaches with usage snippets whose setup lives in an
         earlier (or no) fence - `model.to(device)` sketches, agent-UI
         placeholders like Agent(...)/Tool(...), pseudo-code. A lesson
         may show usage before setup; only module access is a certain
         NameError, everything else is teaching texture.

Wildcard imports keep making their fence opaque (check skipped);
non-Python content that happens to parse as Python is an honest-label
finding, not ours. Report-only: exit 0 always.

    python scripts/qa/fence_namecheck.py --root .
    python scripts/qa/fence_namecheck.py --root . --names   # triage:
        aggregate uses by name (epic scoping; skips per-line output)
    python scripts/qa/fence_namecheck.py --root . --names --name model
        drill down: per-file distribution of one name's unbound uses
"""
from __future__ import annotations

import argparse
import ast
import builtins
import re
import sys
from collections import Counter
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

BUILTINS = set(dir(builtins))
IGNORED = BUILTINS | {"__file__", "__doc__", "__annotations__", "__package__",
                      "self", "cls", "args", "kwargs"}

# Names that are modules, not teaching variables: `name.attr` on one of
# these without an import is NC-01 (certain NameError). Kept as a flat
# set - a lesson variable genuinely named `json` or `np` teaching itself
# would be the rarer content.
MODULE_NAMES = frozenset("""
abc argparse array asyncio ast base64 bisect builtins calendar cmath
collections concurrent contextlib contextvars copy csv ctypes dataclasses
datetime decimal difflib dis email enum errno faulthandler fileinput
fnmatch fractions ftplib functools gc getpass gettext glob gzip hashlib
heapq hmac html http importlib inspect io ipaddress itertools json keyword
linecache locale logging math mimetypes multiprocessing numbers operator os
pathlib pickle platform plistlib pprint profile pstats pyclbr queue random
re secrets select selectors shelve shutil signal site smtplib socket
sqlite3 ssl statistics string struct subprocess sys sysconfig tarfile
tempfile textwrap threading time timeit tkinter token tokenize tomllib
trace tracemalloc types typing unicodedata unittest urllib uuid warnings
wave weakref webbrowser xml zipfile zlib zoneinfo
np pd plt sns tf keras torch nn F einsum datasets transformers peft trl
accelerate bitsandbytes langchain langgraph langsmith litellm openai
anthropic qdrant_client sentence_transformers sklearn scipy PIL cv2
tiktoken chromadb faiss autogen crewai pydantic yaml tomli tqdm rich
httpx aiohttp requests pyarrow polars duckdb nltk spacy gensim
""".split())


def bound_names(tree: ast.AST) -> set[str]:
    """All names this fence binds, at any nesting level (two-pass input)."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            for a in node.names:
                if a.name == "*":
                    continue  # wildcard: handled as fence opacity
                names.add(a.asname or a.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.Global) or isinstance(node, ast.Nonlocal):
            names.update(node.names)
    return names


def used_names(tree: ast.AST) -> set[tuple[str, int]]:
    """(name, lineno) for every Load-context Name."""
    return {(n.id, n.lineno) for n in ast.walk(tree)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def module_loads(tree: ast.AST) -> set[tuple[str, int]]:
    """(name, lineno) for Load Names used as `name.attr` - module access.

    Only the outermost name of a chain counts (`a.b` adds a, not b),
    which is exactly where module names live.
    """
    return {(n.value.id, n.lineno) for n in ast.walk(tree)
            if isinstance(n, ast.Attribute)
            and isinstance(n.value, ast.Name)
            and isinstance(n.value.ctx, ast.Load)}


def python_fences(lines: list[str]) -> list[tuple[int, str]]:
    """(fence_start_line, source) for every ```python fence."""
    fences: list[tuple[int, str]] = []
    in_fence = False
    lang = ""
    fence_start = 0
    fence_src: list[str] = []
    for i, raw in enumerate(lines):
        m = FENCE_RE.match(raw)
        if m:
            if in_fence and lang == "python":
                fences.append((fence_start, "\n".join(fence_src)))
            in_fence = not in_fence
            lang = "" if not in_fence else m.group(2).lower()
            if in_fence:
                fence_start = i + 1
                fence_src = []
            continue
        if in_fence:
            fence_src.append(raw)
    return fences


def check_file(root: Path, path: Path, findings: list[str],
               records: list[tuple[str, str, str]] | None = None) -> None:
    """Append NC-01/NC-02 findings; with `records`, (name, rel, code) triples."""
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")

    # pass 1: every name any python fence binds, regardless of position
    doc_bound: set[str] = set()
    trees: list[tuple[int, str, ast.AST, bool]] = []  # (start, src, tree, wildcard)
    for start, src in python_fences(lines):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue  # codeblock_syntax_scan owns syntax findings
        wildcard = any(isinstance(n, ast.ImportFrom) and
                       any(a.name == "*" for a in n.names)
                       for n in ast.walk(tree))
        doc_bound |= bound_names(tree)
        trees.append((start, src, tree, wildcard))

    # pass 2: sort unbound Load names into NC-01 (module access without
    # import - certain NameError) vs NC-02 (fragment idiom - accepted)
    for start, src, tree, wildcard in trees:
        if wildcard:
            continue  # opaque: can't know what a wildcard import binds
        mod_loads = module_loads(tree)
        for name, ln in sorted(used_names(tree)):
            if (name not in IGNORED and name not in doc_bound):
                usage = src.splitlines()[ln - 1].strip()[:60]
                if name in MODULE_NAMES and (name, ln) in mod_loads:
                    code = "NC-01"
                    text = (f"NC-01 module access without import: "
                            f"'{name}' used as `{name}.` but no fence in "
                            f"this document imports it - {usage}")
                else:
                    code = "NC-02"
                    text = (f"NC-02 fragment idiom (accepted): name "
                            f"'{name}' used but never bound in this "
                            f"document's python fences - {usage}")
                if records is not None:
                    records.append((name, rel, code))
                findings.append(f"{rel}:{start + ln}: {text}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--names", action="store_true",
                        help="triage: aggregate NC-01 uses by name instead of "
                             "printing per-line findings")
    parser.add_argument("--name", metavar="NAME",
                        help="drill-down for --names: per-file distribution "
                             "of one name's unbound uses")
    args = parser.parse_args()
    if args.name:
        args.names = True  # drill-down implies triage mode
    docs = args.root / "docs"
    findings: list[str] = []
    records: list[tuple[str, str, str]] = []
    for path in sorted(docs.rglob("*.md")):
        try:
            check_file(args.root, path, findings,
                       records if args.names else None)
        except (UnicodeDecodeError, OSError, SyntaxError, ValueError):
            continue
    if args.names:
        if args.name:
            files = Counter(rel for name, rel, _ in records
                            if name == args.name)
            print(f"fence_namecheck drill: {sum(files.values())} unbound uses of "
                  f"'{args.name}' in {len(files)} files")
            for rel, n in files.most_common(40):
                print(f"  {n:4d}  {rel}")
        else:
            counts = Counter(name for name, _, _ in records)
            print(f"fence_namecheck triage: {sum(counts.values())} uses of "
                  f"{len(counts)} distinct unbound names (top 60)")
            for name, n in counts.most_common(60):
                print(f"  {n:4d}  {name}")
    for f in ([] if args.names else findings):
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    n_nc01 = sum(1 for f in findings if "NC-01" in f)
    n_nc02 = sum(1 for f in findings if "NC-02" in f)
    n_files = len({f.split(":", 1)[0] for f in findings})
    print(f"fence_namecheck: {n_nc01} NC-01 module-access findings, "
          f"{n_nc02} NC-02 fragment findings (accepted) in {n_files} files "
          f"across docs/ (report mode - exit 0 by design)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
