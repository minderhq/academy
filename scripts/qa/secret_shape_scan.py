#!/usr/bin/env python3
"""secret-shape gate for the Minder Academy corpus.

SS-01  a ```python fence must not carry a credentialed-shaped string
       literal: a constant whose value matches a provider key shape
       (OpenAI / Anthropic ``sk-`` + 20+, GitHub ``ghp_/gho_/ghu_/ghs_/
       ghr_`` + 30+, GitHub fine-grained ``github_pat_`` + 22+, AWS
       ``AKIA`` + 16, Google ``AIza`` + 35, Slack ``xox[baprs]-`` + 10+)
       is either a leaked real credential or a reader template that
       looks exactly like one - the repo is publish-bound and GitHub's
       own secret scanning flags these shapes on push, so the corpus
       must never carry them. The affirmative form is the corpus's own
       idiom: read credentials from the environment
       (``os.environ["OPENAI_API_KEY"]``, ``os.getenv(...)``), never
       embed them.

Out of the class by construction:

  - environment reads (``os.environ[...]``, ``os.getenv(...)``) - the
    taught idiom; the walk matches ``ast.Constant`` string values only,
    a Name/Attribute/Subscript lookup never carries the shape.
  - placeholder literals (``"YOUR_API_KEY"``, ``"sk-xxx"``,
    ``"change-me-in-production"``) - the shape's own prefix + tail
    demands do the partition: no provider prefix matches, and every
    shape demands a long random tail (20+ / 30+ / 22+ / 16 / 35 / 10+
    chars) so short stand-ins stay silent. No allowlist needed - a
    placeholder cannot be shaped like a real key by construction.
  - prose mentions and md anchor slugs
    (``#task-specific-recommendations``) never reach the walk (AST over
    python fences only), and the ``\\b`` anchor keeps any in-fence
    ``"task-specific-..."``-style string silent too: the ``s`` of the
    embedded ``sk-`` sits between word characters, so no boundary.
  - f-string constant parts still land (a real shape typed inside an
    f-string is a Constant node of the JoinedStr) - deliberate: the
    shape is on the page either way.
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, any line) is deliberate
    danger-teaching, the sibling unsafe_*/interp/crypto escape.
  - non-python fences (yaml / shell / dockerfile / json) are outside
    the python universe; a shell ``export API_KEY=sk-...`` is the
    bash_vars_check universe (BB-family).
  - fences that do not parse (SyntaxError) are silently skipped, the
    sibling-gate convention; codeblock_syntax_scan owns fence
    compilability.
  - notebooks (.ipynb) are outside the md universe.

Hard gate (exit 1 on findings): born census tick-664 read every string
constant in every md python fence fence-aware = 0 credentialed shapes
across 1861 fences - the corpus teaches the env-var idiom everywhere
(the one key-ish assignment in the corpus is the obvious placeholder
``JWTAuth(secret="change-me-in-production")`` at TUTORIAL-013, silent
by the tail-demand partition). Zero-drain, hard from birth, no md
edits, no drain, no census churn (the US-02/RT-02/insecure_temp/
crypto preemptive-ownership shape).

Run over the whole corpus:
    python scripts/qa/secret_shape_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

DANGER_MARKER_RE = re.compile(r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)

# Credentialed shapes - each anchored so embedded-word look-alikes
# (``task-specific``) cannot match, each demanding a provider prefix
# plus a long random tail a placeholder cannot accidentally satisfy.
SECRET_SHAPES = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),            # OpenAI / Anthropic / DeepSeek
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),       # GitHub classic tokens
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}"),     # GitHub fine-grained PATs
    re.compile(r"\bAKIA[A-Z0-9]{16}"),                 # AWS access key ids
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}"),            # Google API keys
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),     # Slack tokens
)

FINDING = (" SS-01 credentialed-shaped string literal (provider key "
           "shape) - read it from the environment instead "
           "(os.environ / os.getenv); GitHub secret scanning flags "
           "these shapes on push")


def _scan_fence(rel: str, start: int, fence_lines: list[tuple[int, str]],
                findings: list[str]) -> None:
    src = "\n".join(raw for _, raw in fence_lines)
    if DANGER_MARKER_RE.search(src):
        return
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    base = start  # fence content line 1 == fence-open line + 1

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if any(p.search(node.value) for p in SECRET_SHAPES):
                findings.append(f"{rel}:{base + node.lineno}: SS-01{FINDING}")


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    in_fence = False
    lang = ""
    start = 0
    fence_lines: list[tuple[int, str]] = []
    for ln, raw in enumerate(lines, 1):
        if FENCE_RE.match(raw):
            if in_fence and lang == "python" and fence_lines:
                _scan_fence(rel, start, fence_lines, findings)
            in_fence = not in_fence
            lang = "" if not in_fence else FENCE_RE.match(raw).group(2).lower()
            start = ln if in_fence else 0
            fence_lines = []
            continue
        if in_fence:
            fence_lines.append((ln, raw))
    if in_fence and lang == "python" and fence_lines:
        _scan_fence(rel, start, fence_lines, findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    n_files: set[str] = set()
    for path in sorted(docs.rglob("*.md")):
        try:
            before = len(findings)
            scan_file(args.root, path, findings)
            if len(findings) > before:
                n_files.add(path.relative_to(args.root).as_posix())
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"secret_shape_scan: {len(findings)} findings "
          f"(SS-01 credentialed-shaped string literals - provider key "
          f"shapes sk-/ghp_/github_pat_/AKIA/AIza/xox) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
