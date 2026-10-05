#!/usr/bin/env python3
"""brand-term consistency census (TC-01/TC-02) for Minder Academy.

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

TC-02  bare lowercase "ollama" in PROSE - outside fences, inline
       code, frontmatter (tag vocabulary is lowercase by design,
       TV-01 guards it), and quoted spans ("..." / '...' carry
       terminal error text like "Command not found: ollama", a CLI
       literal, not a brand mention). Code forms are legal and
       expected - `ollama pull`, `ollama serve`, FROM ollama/ollama,
       python module names. Canonical prose fix: "Ollama". HARD
       since 2026-09-30: born at zero once the legal-literal classes
       moved from the audit queue into the predicate.

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

History: born tick-400 (f9a9575) as report-mode census measuring
66 TC-01 across the corpus. Drain tick-401: all 66 fixed in 37
files to canonical "Hugging Face" (per-file expected-count
asserts; front-matter bumped), plus the 1 real TC-02 prose site
(TROUBLESHOOTING-QUICKSTART heading) and one bare command
reference backticked in 1401. TC-01 is now a HARD GATE - exit 1
if any bare "HuggingFace" token returns, so the 55/45 split can
never regrow. TC-02 went hard 2026-09-30: its four report rows
were all legal-literal classes (quoted terminal error text, FM
tag-list entries like ['infrastructure', 'ollama', 'vllm'],
quoted binary-name headings); those moved into the predicate
(frontmatter skip + quoted-span strip), zero doc edits, and any
future bare prose "ollama" is a real finding. tick-689: the fence
model lands the shared CommonMark canon (tick-678) - the old
exact-3 toggle never opened a 4-run super-fence and let its inner
pairs toggle TC-02's gate through the outer interior; TC-01 stays
fence-independent by design (a bare HuggingFace token is a brand
violation inside code too).

Run over the whole corpus:
    python scripts/qa/term_consistency_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# tick-678 CommonMark canon (tick-689): run-length openers with
# char/run capture, tilde fences included; a true closer repeats the
# opener character in a run at least as long, a different fence
# character never closes, a non-closer marker line is fence content.
FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")

# bare token: no identifier continuation (H4, Embeddings, TB, _client);
# TC-02 also excludes the ollama.com domain spelling
TC01_RE = re.compile(r"HuggingFace(?![A-Za-z0-9_-])")
TC02_RE = re.compile(r"(?<![A-Za-z0-9_/.-])ollama(?![A-Za-z0-9_.-])")

INLINE_CODE = re.compile(r"`[^`\n]+`")
QUOTED = re.compile(r'"[^"\n]*"|\'[^\'\n]*\'')
FM_CLOSE = re.compile(r"^---\s*$")


def scan_file(root: Path, path: Path, findings: list[str],
              total: list[int]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    in_fence: tuple[str, int] | None = None
    in_fm = bool(lines) and lines[0].strip() == "---"
    for i, raw in enumerate(lines, 1):
        if in_fm:
            if FM_CLOSE.match(raw):
                in_fm = False
            continue
        m = FENCE_OPEN.match(raw)
        if m:
            f_char, f_len = m.group(1)[0], len(m.group(1))
            if in_fence:
                if f_char == in_fence[0] and f_len >= in_fence[1]:
                    in_fence = None  # true closer ends any block
            else:
                in_fence = (f_char, f_len)
            continue
        # strip inline code spans so `ollama` in backticks stays legal,
        # then quoted spans so terminal error text stays legal
        prose = QUOTED.sub("", INLINE_CODE.sub("", raw))
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
          f"{len(n_files)} files across docs/ (both HARD; canonical "
          f"'Hugging Face' / 'Ollama'; TC-02 outside FM/fences/code/"
          f"quotes, hard since 2026-09-30)")
    return 1 if (total[0] or total[1]) else 0


if __name__ == "__main__":
    sys.exit(main())
