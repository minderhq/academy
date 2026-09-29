#!/usr/bin/env python3
"""brand-term consistency census (TC-01/TC-02) for PROJECT-OMEGA.

Platform search, TOC quality and prose credibility depend on one
canonical spelling per brand. The tick-400 ad-hoc sweep found the
corpus split between the two Hugging Face spellings: 66 bare
"HuggingFace" tokens against 54 "Hugging Face" - roughly 55/45, so a
learner sees both forms for the same vendor. The official brand is
two-word "Hugging Face" in prose.

TC-01  bare "HuggingFace" token (not an identifier continuation).
       CamelCase class and org names are excluded by construction:
       the match requires no following [A-Za-z0-9_-], so
       HuggingFaceEmbeddings, HuggingFaceH4/zephyr, HuggingFaceTB
       and friends stay legal. Canonical fix: "Hugging Face".

TC-02  bare lowercase "ollama" in PROSE (outside fences and inline
       code). Code forms are legal and expected - `ollama pull`,
       `ollama serve`, FROM ollama/ollama, python module names - so
       only fence/backtick-free prose hits are findings. Canonical
       prose fix: "Ollama".

Census scope note: "TensorFlow", "LangChain", "PyTorch", "OpenAI"
were swept in the same tick-400 pass and are already consistent (0
mis-cased variants corpus-wide), so only these two classes are
tracked. Birth state (tick-400): 66 TC-01 across the corpus; TC-02
measures 6, of which 1 is real prose (TROUBLESHOOTING-QUICKSTART
"running ollama") and 5 are legal-literal classes - lowercase
token entries in front-matter-style tag lists (same convention as
'vllm'/'tgi'), quoted terminal error text ("Command not found:
ollama"), and bare binary-name references (ollama ps). Fence
detection follows the corpus idiom including list-indented fences
("   ```bash" inside numbered steps) and skips inline `code` spans.
Report mode - exit 0 by design; the census is an inventory for
batched drains, not a gate.

Run over the whole corpus:
    python scripts/qa/term_consistency_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^\s*```(\w*)\s*$")

# bare token: no identifier continuation (H4, Embeddings, TB, _client);
# TC-02 also excludes the ollama.com domain spelling
TC01_RE = re.compile(r"HuggingFace(?![A-Za-z0-9_-])")
TC02_RE = re.compile(r"(?<![A-Za-z0-9_/.-])ollama(?![A-Za-z0-9_.-])")

INLINE_CODE = re.compile(r"`[^`\n]+`")


def scan_file(root: Path, path: Path, findings: list[str],
              total: list[int]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    in_fence = False
    for i, raw in enumerate(lines, 1):
        m = FENCE_OPEN.match(raw)
        if m:
            in_fence = not in_fence
            continue
        # strip inline code spans so `ollama` in backticks stays legal
        prose = INLINE_CODE.sub("", raw)
        n01 = len(TC01_RE.findall(prose))
        n02 = 0 if in_fence else len(TC02_RE.findall(prose))
        if n01:
            total[0] += n01
            findings.append(
                f"{rel}:{i}: TC-01 bare HuggingFace (x{n01}) - "
                f"{raw.strip()[:90]}")
        if n02:
            total[1] += n02
            findings.append(
                f"{rel}:{i}: TC-02 prose lowercase ollama (x{n02}) - "
                f"{raw.strip()[:90]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    total = [0, 0]
    n_files: set[str] = set()
    for path in sorted(docs.rglob("*.md")):
        try:
            scan_file(args.root, path, findings, total)
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    for f in findings:
        n_files.add(f.split(":", 1)[0])
    print(f"term_consistency_scan: {total[0]} TC-01 bare-HuggingFace "
          f"and {total[1]} TC-02 prose-ollama findings in "
          f"{len(n_files)} files across docs/ (report mode; canonical "
          f"'Hugging Face' / 'Ollama')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
