#!/usr/bin/env python3
"""tag vocabulary census (TV-01..TV-03) for Minder Academy.

The platform will drive filtering and related-content navigation
from the Tags field, so the vocabulary must stay closed and
single-form. Tick-403 measured the corpus: 111 docs carry Tags,
216 distinct tags, 0 in-document duplicates, 0 case clashes -
but 7 single-form variants of majority forms were found
(fine-tuning vs finetuning 8, vector-database vs vector-db 2,
knowledge-graph vs knowledge-graphs, transformer vs transformers
11, federated vs federated-learning, benchmarking vs benchmarks,
chromadb vs chroma).

TV-01  tag outside the frozen birth vocabulary (WHITELIST). New
       tags are deliberate edits - add them to WHITELIST in the
       same commit.
TV-02  duplicate tag within one document's list.
TV-03  tag in a known non-canonical variant form; the message
       names the canonical form. HARD - drained tick-404: all 7
       birth sites canonicalized (transformer, fine-tuning,
       benchmarking, federated, knowledge-graph, vector-database,
       chromadb) and the variant forms removed from WHITELIST,
       so the birth vocabulary is now 209 single-form tags.
       VARIANTS is kept as a correcting map: a future variant
       form gets the pointed TV-03 message (naming the canonical
       spelling) instead of the generic TV-01 unknown-tag one,
       and fails the gate either way.
       First deliberate extension (tick-449): 'phase' and
       'checkpoint' genre tags added for the nav-node tagging
       standard (phase README / CHECKPOINT are platform pages;
       'module' / 'prerequisites' were already in). Vocabulary
       209 -> 211.
       Second deliberate extension (tick-456): 27 genre/facet tags
       for the TG-04 corpus-wide coverage drain ('roadmap',
       'cheatsheet', 'career', 'flashcards', 'faq', 'glossary',
       'quickstart', 'setup', 'reference', 'troubleshooting',
       'diagram', 'comparison', 'use-case', 'enterprise',
       'notebook', 'case-study', 'bridge', 'lab', 'project',
       'volume', 'maintenance', 'template', 'navigation', 'guide',
       'healthcare', 'finance', 'industry') - one filter facet per learner /
       maintainer directory, so the platform's tag chips can slice
       the whole corpus, not just the phases. Vocabulary
       211 -> 238.

HARD GATE - exit 1 on any finding. TV-01/TV-02 were hard from
day one (KW-03 born-at-zero pattern); TV-03 joined after the
tick-404 drain (census -> drain -> gate cycle).

Run over the whole corpus:
    python scripts/qa/tag_vocabulary_census.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
TAGS_FIELD = re.compile(r"^Tags:(.*)$")

WHITELIST = frozenset([
    'acting', 'activation', 'adamw', 'adaptation', 'advanced', 'adversarial',
    'agents', 'aliases', 'alignment', 'api-design', 'architecture', 'assessment',
    'attention', 'audio', 'autogen', 'autograd', 'autonomy', 'awq',
    'backpropagation', 'bart', 'benchmarks', 'bf16', 'binary',
    'bitnet', 'bnn', 'bpe', 'bridge', 'bridge-mode', 'cag', 'calculus',
    'case-study', 'career', 'cheatsheet', 'checkpoint', 'chroma', 'ci-cd', 'clip', 'code-interpreter', 'cognition',
    'comparison',
    'communication', 'compression', 'configuration', 'context', 'context-window', 'cpu-gpu-hybrid',
    'crewai', 'cuda', 'data-curation', 'ddp', 'deepspeed', 'deployment', 'diagram',
    'devops', 'differential-privacy', 'distillation', 'distributed', 'distributed-training', 'docker',
    'dpo', 'dynamic-batching', 'embeddings', 'encoder-decoder', 'enterprise', 'evaluation', 'exl2',
    'extreme-compression', 'faq', 'fastapi', 'federated-learning',
    'finance', 'finetuning',
    'flash-attention', 'flashcards', 'fp16', 'framework-comparison', 'framework-engineering', 'framework-selection', 'frameworks',
    'fsdp', 'function-calling', 'gelu', 'ggml', 'gguf', 'glossary', 'gpt',
    'gptq', 'grpo', 'gpu', 'gradient-clipping', 'graphrag', 'guide', 'hands-on', 'hardware', 'healthcare',
    'hnsw', 'hybrid-search', 'inference', 'infrastructure', 'industry', 'iommu', 'isp',
    'jumbo-frames', 'k3s', 'knowledge-graphs', 'kubernetes', 'kv-cache',
    'lab', 'langchain', 'langgraph', 'learning-rate', 'lifecycle', 'llama', 'llamacpp',
    'llm', 'llmops', 'long-context', 'long-term-memory', 'lora', 'maintenance', 'manufacturing',
    'math', 'mcp', 'mem0', 'memory', 'milvus', 'mixed-precision', 'mlops',
    'model-registry', 'module', 'monitoring', 'mtu', 'multi-agent', 'multi-head',
    'multimodal', 'navigation', 'neo4j', 'networking', 'nginx', 'normalization', 'notebook', 'observability',
    'offloading', 'ollama', 'optimization', 'optimizers', 'orchestration', 'peft',
    'performance', 'pgvector', 'phase', 'pii', 'pinecone', 'pipeline', 'pipeline-parallelism',
    'planning', 'plugin-architecture', 'postgresql', 'practice', 'preference', 'preference-learning',
    'preparation', 'prerequisites', 'pretraining', 'privacy', 'production', 'production-framework',
    'project', 'prometheus', 'prompt-injection', 'proxmox', 'pruning', 'pytorch', 'pytorch-lightning',
    'qat', 'qdrant', 'qlora', 'quantization', 'quantization-aware-training', 'quickstart', 'quiz',
    'rag', 'react', 'reasoning', 'reference', 'reranking', 'retrieval', 'rlhf',
    'roadmap', 'rope', 'sam', 'scheduling', 'security', 'self-attention', 'serving',
    'setup', 'similarity', 'solution', 'sparsity', 'speculative-decoding', 'star-topology', 'swiglu',
    'switch', 'synthetic-data', 't5', 'tensor-parallelism', 'tensorflow', 'tensors',
    'ternary', 'tgi', 'template', 'tokenization', 'tokenizer', 'tool-calling', 'topology',
    'training', 'transformers', 'troubleshooting', 'tts', 'tutorial', 'uplink', 'use-case',
    'vector-db', 'vector-store', 'vectors', 'versioning', 'vfio',
    'virtualization', 'vision', 'vision-language', 'vlan', 'volume', 'vllm', 'vlm',
    'wan', 'warmup', 'weaviate', 'whisper', 'xla', 'zero',
])
VARIANTS = {
    'fine-tuning': 'finetuning',
    'vector-database': 'vector-db',
    'knowledge-graph': 'knowledge-graphs',
    'transformer': 'transformers',
    'federated': 'federated-learning',
    'benchmarking': 'benchmarks',
    'chromadb': 'chroma',
    'llama.cpp': 'llamacpp',
}


def doc_tags(lines: list[str]) -> list[str] | None:
    """Top-level Tags field of one doc, or None if no front matter."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = TAGS_FIELD.match(raw)
                if m:
                    item = m.group(1).strip()
                    try:
                        vals = ast.literal_eval(item)
                    except (ValueError, SyntaxError):
                        vals = [t.strip() for t in item.strip("[]").split(",")
                                if t.strip()]
                    return [t.strip().strip("'\"") for t in vals]
            return []
    return None


def check(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    tags = doc_tags(lines)
    if tags is None:
        return
    seen: set[str] = set()
    for t in tags:
        if t in seen:
            findings.append(f"{rel}: TV-02 duplicate tag {t!r} in one doc")
        seen.add(t)
        if t in VARIANTS:
            findings.append(f"{rel}: TV-03 variant tag {t!r} -> "
                            f"canonical {VARIANTS[t]!r}")
        elif t not in WHITELIST:
            findings.append(f"{rel}: TV-01 unknown tag {t!r} "
                            f"(add to WHITELIST deliberately)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    n_docs = 0
    for path in sorted(docs.rglob("*.md")):
        try:
            before = len(findings)
            check(args.root, path, findings)
            if len(findings) > before:
                n_docs += 1
        except (UnicodeDecodeError, OSError):
            continue
    by_class = [sum(1 for f in findings if f" TV-0{i} " in f)
                for i in (1, 2, 3)]
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"tag_vocabulary_census: TV-01={by_class[0]} TV-02={by_class[1]} "
          f"TV-03={by_class[2]} across {n_docs} docs "
          f"(hard gate; vocabulary {len(WHITELIST)} single-form tags, "
          f"{len(VARIANTS)} correcting variants)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
