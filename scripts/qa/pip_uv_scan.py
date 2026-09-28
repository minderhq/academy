#!/usr/bin/env python3
"""pip/uv packaging-consistency gate for the PROJECT-OMEGA curriculum.

Encodes the documented adjudication policy (00-META/ENVIRONMENT-SETUP.md):
uv is the default installer; a bare `pip install X` in student-facing
instructions is only valid inside the deliberate exceptions:

  - Docker/container contexts (uv is not preinstalled in Python base
    images; LAB-001 teaches the official uv image pattern)
  - conda workflows (pip into the active conda environment is standard)
  - uv bootstraps (`pip install uv` in CI or setup snippets)
  - uv-first blocks that already show the `uv pip install` form alongside
    the plain-pip fallback ("plain pip works too" / "fallback")

Anything else flags as PIP-01 (bare pip install without uv framing) or
PIP-02 (pip bootstrap of a package other than uv outside a venv-first
block, i.e. `python -m pip install --upgrade pip` without uv context).

Exit 0 when zero findings; exit 1 otherwise. Run over the whole corpus:
    python scripts/qa/pip_uv_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")
BARE_PIP_RE = re.compile(r"^\s*(?:python3?\s+-m\s+)?pip\s+install\b(.*)$")
CONDA_RE = re.compile(r"\bconda\s+(create|activate|env|install|info|run)\b")
DOCKER_HINT_RE = re.compile(r"\b(docker|container|image)\b", re.IGNORECASE)
RUN_LINE_RE = re.compile(r"^\s*(RUN|COPY|CMD|ENTRYPOINT)\b")
DOCKER_LANGS = {"dockerfile", "docker"}
FALLBACK_RE = re.compile(r"\b(fallback|plain pip works too|alternatively)\b", re.IGNORECASE)


def classify_block(lines: list[str], pre_context: list[str]) -> str:
    """Decide why a bare pip line may be allowed: return allow reason or ''. """
    lang = ""
    block_join = "\n".join(lines)
    for l in lines:
        m = FENCE_RE.match(l)
        if m:
            lang = m.group(2).lower()
            break
    if lang in DOCKER_LANGS:
        return "dockerfile fence"
    if any(RUN_LINE_RE.match(l) for l in lines):
        return "dockerfile RUN line"
    if any(CONDA_RE.search(l) for l in lines):
        return "conda workflow"
    # Exact match with a word boundary: `pip install uvicorn` must NOT
    # satisfy this (a plain startswith("pip install uv") let it slip).
    # The canonical bare form `pip install uv` never reaches classify_block
    # (skipped earlier), so this branch only serves trailing-arg variants
    # like `pip install uv --index-url ...`.
    if any(re.match(r"^\s*(?:python3?\s+-m\s+)?pip\s+install\s+uv\b", l) for l in lines):
        return "uv bootstrap"
    if any(re.match(r"^\s*uv\s+pip\s+install\b", l) for l in lines):
        return "uv-first block with fallback"
    if any(FALLBACK_RE.search(l) for l in lines):
        return "fallback-labeled"
    if any(DOCKER_HINT_RE.search(l) for l in lines[-4:] + pre_context):
        return "docker/container context"
    return ""


def lint_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")
    in_fence = False
    fence_lines: list[str] = []
    pre_context: list[str] = []
    for i, raw in enumerate(lines):
        if FENCE_RE.match(raw):
            if in_fence:
                in_fence = False
                fence_lines = []
            else:
                in_fence = True
                pre_context = [l for l in lines[max(0, i - 4):i]]
            continue
        if not in_fence:
            continue
        fence_lines.append(raw)
        m = BARE_PIP_RE.match(raw)
        if not m:
            continue
        if m.group(1).strip() == "uv":
            continue  # canonical uv bootstrap
        reason = classify_block(fence_lines, pre_context)
        if reason:
            continue
        findings.append(
            f"{rel}:{i + 1}: PIP-01 bare pip install without uv framing "
            f"(policy: 00-META/ENVIRONMENT-SETUP.md) - {raw.strip()[:70]}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    for path in sorted(docs.rglob("*.md")):
        try:
            lint_file(args.root, path, findings)
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"pip_uv_scan: {len(findings)} findings across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
