#!/usr/bin/env python3
"""Import-resolution gate for every ```python fence in the corpus.

Generalizes langchain_census (LC-01, langchain-family only) to every
import in every python fence: an import line that does not resolve
against the kurulu-stack means a learner following the lesson hits
ModuleNotFoundError, i.e. the lesson teaches code that cannot run.

IC-01  import does not resolve (module missing or name absent)

Design, inherited from the gates this generalizes:
- the fence universe is codeblock_syntax_scan's exactly (CommonMark
  fence-length parsing since tick-679: the opener's marker run captured,
  a closer repeats the opener's character at equal-or-longer length,
  non-closer marker lines are content; python/py/python3 labels,
  textwrap.dedent before parsing), so the two gates always see the same
  blocks - and CB-01's baseline-0 parse guarantee means ast.parse never
  fails here
- fences are parsed with ast, so multi-line paren imports, semicolon
  one-liners and `as` aliases all resolve - the blind spots
  langchain_census documents away are simply gone here
- stdlib always resolves; from-import names fall back to importing the
  dotted submodule (the `from os import path` idiom) before flagging -
  a bare `import module` has not loaded submodules yet
- first-party teaching modules and deliberate references to packages
  outside the stack surface are accepted classes (ACCEPTED_PREFIXES),
  the census->classify->lock path every gate took
- conditional `try: import x / except ImportError:` graceful-degradation
  teaching texture is still found (the import line exists as written)
- relative imports (from . import x) have no package context inside a
  fence fragment - skipped and counted, not findings

Hard gate since tick-325: the tick-323/324 census (429 findings -> 424
after the dotted-submodule-fallback fix and two real drains) classified
every finding into two accepted classes, locked as ACCEPTED_PREFIXES
below - alternative/optional third-party stacks the lessons reference
deliberately, and lesson-local fragment modules the lesson defines
itself. A failing import outside those classes means a learner hits
ModuleNotFoundError as written: exit 1. The accepted census stays in
the summary line for visibility.

Run over the whole corpus:
    python scripts/qa/fence_import_check.py --root .
"""
from __future__ import annotations

import argparse
import ast
import importlib
import re
import sys
import textwrap
from pathlib import Path

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)\s*$")
PYTHON_LANGS = ("python", "py", "python3")

for _pkg in ("torch", "pydantic"):
    try:
        importlib.import_module(_pkg)
    except ImportError:  # environment problem, not a doc problem
        print(f"fence_import_check: {_pkg} not importable in this "
              "interpreter - the census resolves lesson imports against "
              "the kurulu-stack; run the scorecard with that python "
              "(see ENVIRONMENT-SETUP.md)")
        sys.exit(2)

# The accepted-census allowlist (hard gate since tick-325): a failing
# import whose dotted chain hits one of these prefixes belongs to a
# census class classified in the tick-323/324 pass (429 findings -> 424
# -> 190 distinct module strings -> 0 unclassified). Two classes:
# - alternative / optional third-party stacks the lessons deliberately
#   reference without requiring installation (quant/finetune
#   alternatives, vector-db comparisons, PII / telemetry / eval
#   tooling, agent demos, platform-specific stdlib)
# - lesson-local fragment modules the lesson defines itself in an
#   earlier fence (`# File: tensor.py`, src/... project layouts)
# The walk is per dotted segment, so `torch.utils.tensorboard` is
# accepted without weakening `torch` itself.
ACCEPTED_PREFIXES = frozenset({
    # alternative / optional third-party stacks (deliberate, not installed)
    "TTS", "auto_gptq", "autogen", "awq", "bitsandbytes", "boto3",
    "chromadb", "cohere", "crewai", "cv2", "deepspeed",
    "e2b_code_interpreter", "evaluate", "exllamav2", "faster_whisper",
    "flash_attn", "flwr", "gensim", "gymnasium", "jax", "jira",
    "jupyter_client", "kubernetes", "librosa", "lightning",
    "lion_pytorch", "llama_cpp",
    # tick-718 deliberate same-commit extension: the mamba-ssm CUDA kernel
    # package (3404 teaches selective_scan_fn; ENV-GAP:mamba_ssm)
    "mamba_ssm", "mem0",
    # tick-717 deliberate same-commit extension: the MCP Python SDK joins
    # the optional-stack class - 7203 teaches server and client fences
    # against `pip install mcp` (ENV-GAP:mcp in the accepted exec census)
    "mcp", "mlflow", "node2vec", "opacus",
    "opentelemetry", "optimum", "phonenumbers", "pinecone",
    "presidio_analyzer", "presidio_anonymizer", "pyannote", "pyaudio",
    "pymilvus", "pynvml", "ragas", "rank_bm25", "restrictedpython",
    "resource", "rouge", "rouge_score", "sacrebleu", "seaborn",
    "segment_anything", "sentence_transformers",
    # tick-719 deliberate same-commit extension: the SGLang serving
    # framework (1405 teaches Engine + frontend DSL; ENV-GAP:sglang)
    "sglang", "spacy",
    "speechbrain", "stable_baselines3", "structlog", "tavily",
    "tensorflow", "torch.utils.tensorboard", "torchviz",
    "transformer_engine", "triton", "trl", "vllm", "wandb", "weaviate",
    "xformers",
    # lesson-local fragment modules (defined by the lesson itself)
    "agent_types", "analyst_agent", "base_agent", "bitblade", "chunker",
    "config", "core", "data", "drift_detection", "drift_monitor",
    "embeddings", "entity_extraction", "graph_construction", "graph_rag",
    "homelab_tools", "hybrid_search", "ingestion", "keyword_search",
    "llm_metrics", "memoria", "memory", "models", "multimodal_agent",
    "mymodule", "nn", "orchestrator", "production_rag",
    "researcher_agent", "reranker", "retrieval",
    "semantic_text_splitter", "serving", "src", "storage", "tensor",
    "tool_registry", "transformer", "tts_system", "unified_memory",
    "vector_store", "voice_assistant", "whisper_system", "writer_agent",
})


def accepted(module: str) -> bool:
    """True when module or a dotted ancestor is a classified class."""
    while module:
        if module in ACCEPTED_PREFIXES:
            return True
        module = module.rpartition(".")[0]
    return False


_verdict_cache: dict[str, str] = {}


def resolve_module(mod: str) -> str:
    """'OK' or 'ErrorType: message' for a dotted module path."""
    if mod in _verdict_cache:
        return _verdict_cache[mod]
    try:
        importlib.import_module(mod)
        verdict = "OK"
    except Exception as e:  # noqa: BLE001 - any failure means "cannot run"
        verdict = type(e).__name__ + ": " + str(e).split("\n")[0][:90]
    _verdict_cache[mod] = verdict
    return verdict


def scan_file(
    root: Path, path: Path, findings: list[tuple[str, str]], stats: list[int],
) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")
    in_fence = False
    f_char = ""
    f_len = 0
    lang = ""
    start = 0
    body: list[str] = []
    for i, raw in enumerate(lines):
        m = FENCE.match(raw)
        if m and not in_fence:
            run = m.group(1)
            in_fence = True
            f_char, f_len = run[0], len(run)
            lang = m.group(2).lower()
            start = i
            body = []
            continue
        if in_fence:
            if m:
                run = m.group(1)
                ch, n = run[0], len(run)
                if ch == f_char and n >= f_len:
                    # CommonMark: only a same-character run at least
                    # as long closes the fence
                    if lang in PYTHON_LANGS:
                        stats[1] += 1
                        src = textwrap.dedent("\n".join(body))
                        if src.strip():
                            try:
                                tree = ast.parse(src)
                            except SyntaxError:
                                in_fence = False
                                body = []
                                continue  # CB-01 owns fence syntax
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names:
                                        stats[0] += 1
                                        verdict = resolve_module(alias.name)
                                        if verdict != "OK":
                                            findings.append((alias.name,
                                                f"{rel}:{start + node.lineno + 1}: "
                                                f"IC-01 import does not resolve "
                                                f"[{verdict}] - import {alias.name}"))
                                elif isinstance(node, ast.ImportFrom):
                                    if node.level > 0 or node.module is None:
                                        stats[3] += 1  # relative: no context
                                        continue
                                    stats[0] += 1
                                    verdict = resolve_module(node.module)
                                    if verdict != "OK":
                                        findings.append((node.module,
                                            f"{rel}:{start + node.lineno + 1}: "
                                            f"IC-01 import does not resolve "
                                            f"[{verdict}] - from {node.module} "
                                            f"import ..."))
                                    else:
                                        module = importlib.import_module(node.module)
                                        for alias in node.names:
                                            if alias.name == "*":
                                                continue
                                            if hasattr(module, alias.name):
                                                continue
                                            # implicit submodule import
                                            # (from os import path): the
                                            # name may be a submodule the
                                            # bare `import module` has not
                                            # loaded yet - real Python
                                            # resolves it, so must the gate
                                            sub = f"{node.module}.{alias.name}"
                                            if resolve_module(sub) == "OK":
                                                continue
                                            findings.append((node.module,
                                                f"{rel}:{start + node.lineno + 1}: "
                                                f"IC-01 name absent from module "
                                                f"[AttributeError: {node.module} "
                                                f"has no attribute "
                                                f"'{alias.name}'] - from "
                                                f"{node.module} import "
                                                f"{alias.name}"))
                    in_fence = False
                    body = []
                    continue
                # a marker line that is not a valid closer is fence
                # CONTENT (an inner 3-run inside a 4-outer)
                body.append(raw)
                continue
            body.append(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[tuple[str, str]] = []
    stats = [0, 0, 0, 0]  # import statements, python fences, unused, relative imports
    files_seen: set[str] = set()
    for path in sorted(docs.rglob("*.md")):
        before = len(findings)
        try:
            scan_file(args.root, path, findings, stats)
        except (UnicodeDecodeError, OSError):
            continue
        if len(findings) > before:
            files_seen.add(path.relative_to(args.root).as_posix())
    real = [(m, t) for m, t in findings if not accepted(m)]
    accepted_n = len(findings) - len(real)
    for _, text in real:
        print(text.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"fence_import_check: {len(real)} unresolvable imports "
          f"(IC-01) outside the accepted census in {len(files_seen)} "
          f"files across docs/; {accepted_n} accepted by the class "
          f"allowlist ({stats[0]} import statements in {stats[1]} "
          f"python fences, {stats[3]} relative imports skipped) - hard "
          f"gate since tick-325 (census 424 classified tick-324)")
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main())
