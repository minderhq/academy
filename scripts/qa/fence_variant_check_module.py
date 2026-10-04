#!/usr/bin/env python3
"""Module-level variant near-miss gate (PY-02) for the Minder Academy
corpus.

PY-01 v1's declared out-of-scope region: bare names LOADED at module
level (outside any function/class/lambda body). A module-level load
that is defined nowhere - not in the fence, not in any other python
fence of the same document (the established cross-fence fragment
idiom), not a builtin - is reported WHEN it is a lexical variant of a
name that IS in scope: case-insensitive equal, length-aware
levenshtein (<=2 for len>=5, <=1 for len>=3), or underscore-word
prefix. The same PY-01 predicate, applied to the module top level.

PY-02  a module-level loaded name is an undefined variant of an
       in-scope name.

The region is fragment-densest: the tick-332 birth census also
counted 296 distinct bare non-variant undefined names, accepted by
design (fragment idiom), so this gate locks ONLY the variant class at
baseline 0. Birth history (tick-332 census: 35 hits -> tick-333 drain
13 fixed across 7 docs in 153efb0 + 1 reclassified FP) left 16 hits
in 6 recorded FP classes, each absorbed as a reasoned (rel, name)
accept below:
  - ambient import classes (Agent/Model/Trainer where the lowercase
    sibling variable is what is in scope),
  - wrong/right pedagogical placeholders (train() vs train_loss,
    model_a/model_b vs model),
  - attention notation (Q/K/V math symbols vs the Q_chunk slice var),
  - the documented __main__ fragment (its own comment states epochs
    come from the surrounding training script),
  - loop-sibling shape (for name, module in model.named_modules():
    `module` is the loop var, `model` is the walked object),
  - placeholder pipeline functions (chunk_documents matched the
    `chunk` loop var via word-prefix; grep confirms no def exists,
    so renaming would have been wrong - tick-333 reclassification).

Out of scope: bare non-variant module-level names (fragment idiom,
accepted by design), function/class bodies (PY-01 owns those), and
imports (fence_import_check IC-01). Syntax-error fences are skipped:
codeblock_syntax_scan owns parseability.

Run over the whole corpus:
    python scripts/qa/fence_variant_check_module.py --root .
"""
from __future__ import annotations

import argparse
import ast
import builtins
import re
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^ {0,3}```(\w*)\s*$")
BUILTINS = set(dir(builtins))

# (doc relpath, undefined name) -> accepted FP class, with reason
ACCEPTED: dict[tuple[str, str], str] = {
    ("docs/comparisons/CP-001-RAG-vs-FineTuning-vs-Agents.md",
     "Agent"):
        "ambient import class: `agent = Agent(...)` is the corpus idiom",
    ("docs/phases/phase2-foundations/README.md", "Model"):
        "ambient import class in the DDP wrong/right pitfall "
        "(Model().cuda())",
    ("docs/phases/phase3-transformers/README.md", "Q"):
        "attention notation: Q/K/V math symbols vs the Q_chunk slice var",
    ("docs/phases/phase4-quantization/4300-quantization-aware-training/"
     "4305-Quantization-Configuration.md", "model"):
        "loop sibling: `for name, module in model.named_modules()` - "
        "`module` is the loop var, `model` the walked object",
    ("docs/phases/phase5-finetuning/5300-synthetic/"
     "5301-Knowledge-Distillation.md", "teacher_a"):
        "commented cross-section promise: teachers are built in the "
        "Data Generation section below",
    ("docs/phases/phase5-finetuning/5300-synthetic/"
     "5301-Knowledge-Distillation.md", "teacher_b"):
        "commented cross-section promise: teachers are built in the "
        "Data Generation section below",
    ("docs/phases/phase5-finetuning/5400-distributed-training/"
     "assessment/PRACTICE.md", "epochs"):
        "documented __main__ fragment: own comment states epochs come "
        "from the surrounding training script",
    ("docs/phases/phase5-finetuning/README.md", "train"):
        "wrong/right pitfall placeholder: train() as pipeline step vs "
        "the train_loss result var",
    ("docs/phases/phase5-finetuning/README.md", "Trainer"):
        "ambient HF Trainer usage in the learning-rate pitfall",
    ("docs/volumes/VOLUME-6-Data-Nexus.md", "chunk_documents"):
        "placeholder pipeline function: word-prefix matched the "
        "`chunk` loop var; no def exists, renaming would be wrong "
        "(tick-333 reclassification)",
    ("docs/volumes/VOLUME-6-Data-Nexus.md", "model_a"):
        "wrong/right pitfall placeholder: model_a/model_b encode the "
        "embedding-mismatch lesson",
    ("docs/volumes/VOLUME-6-Data-Nexus.md", "model_b"):
        "wrong/right pitfall placeholder: model_a/model_b encode the "
        "embedding-mismatch lesson",
}


def lev(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 2:
        return 99
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def words(s: str) -> list[str]:
    return [w for w in re.split(r"[_\d]+", s.lower()) if w]


def is_variant(a: str, b: str) -> bool:
    if a.lower() == b.lower():
        return True
    short = min(len(a), len(b))
    cap = 2 if short >= 5 else (1 if short >= 3 else 0)
    if cap and lev(a, b) <= cap:
        return True
    wa, wb = words(a), words(b)
    if wa and wb and wa[0] == wb[0] and (len(wa) == 1 or len(wb) == 1):
        return True
    return False


def best_variant(name: str, defined: set[str]) -> str | None:
    # bestd starts above lev()'s 99 cap so word-prefix matches (whose
    # edit distance may exceed the lev guard) still report
    best, bestd = None, 100
    for d in sorted(defined):
        if d == name:
            continue
        if is_variant(name, d):
            d2 = lev(name, d)
            if d2 < bestd:
                best, bestd = d, d2
    return best


def fences(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_fence, label, buf, start = False, "", [], 0
    for i, line in enumerate(lines, 1):
        m = FENCE_OPEN.match(line)
        if not in_fence and m:
            in_fence, label, buf, start = True, m.group(1), [], i
        elif in_fence and re.match(r"^ {0,3}```", line):
            in_fence = False
            if label == "python":
                yield start + 1, "\n".join(buf)
            buf = []
        elif in_fence:
            buf.append(line)


def defined_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(tree):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)):
            names.add(child.name)
        elif isinstance(child, ast.Import):
            for a in child.names:
                names.add((a.asname or a.name).split(".")[0])
        elif isinstance(child, ast.ImportFrom):
            for a in child.names:
                if a.name != "*":
                    names.add(a.asname or a.name)
        elif isinstance(child, ast.Name) and isinstance(child.ctx,
                                                        ast.Store):
            names.add(child.id)
    return names


def own_loads(node: ast.AST) -> list[ast.Name]:
    """Loads in this subtree, not descending into nested
    function/class/lambda scopes (module-level means exactly that)."""
    out: list[ast.Name] = []
    stack = list(ast.iter_child_nodes(node))
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            out.append(n)
        stack.extend(ast.iter_child_nodes(n))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    n_py = 0

    for path in sorted((args.root / "docs").rglob("*.md")):
        rel = path.relative_to(args.root).as_posix()
        fl = list(fences(path))
        if not fl:
            continue
        n_docs += 1
        doc_names: set[str] = set()
        trees = []
        for lineno, code in fl:
            try:
                tree = ast.parse(code)
            except SyntaxError:
                continue  # codeblock_syntax_scan owns parseability
            n_py += 1
            trees.append((lineno, code, tree))
            doc_names |= defined_names(tree)

        for lineno, code, tree in trees:
            mod = defined_names(tree)
            for top in tree.body:
                if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef,
                                    ast.ClassDef)):
                    continue
                for sub in own_loads(top):
                    nm = sub.id
                    if (nm in mod or nm in doc_names
                            or nm in BUILTINS):
                        continue
                    if (rel, nm) in ACCEPTED:
                        continue
                    v = best_variant(nm, mod)
                    if v:
                        ln = sub.lineno
                        lines = code.splitlines()
                        where = " | ".join(
                            lines[max(0, ln - 2): ln + 1])[:90]
                        findings.append(
                            f"PY-02 {rel}:{lineno} [ML] '{nm}' is an "
                            f"undefined variant of '{v}' near: {where}")

    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"fence_variant_check_module: {len(findings)} PY-02 "
          f"finding(s) across {n_docs} docs, {n_py} python fences "
          f"in docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
