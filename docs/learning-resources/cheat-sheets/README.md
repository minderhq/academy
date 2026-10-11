---
Document ID: CHEAT-SHEETS-README
Title: "Quick Reference Cheat Sheets"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Beginner
Tags: ['cheatsheet', 'reference']
---

# Quick Reference Cheat Sheets

Thirty-one single-page references: twenty-four tool cheat sheets (Docker, Python, Git, Linux, RAG, Kubernetes, vLLM, Reasoning, llama.cpp, Alignment, Evaluation, Guardrails, Structured Output, Sampling, Quantization, LoRA, KV Cache, Speculative Decoding, Tokenizers, Flash Attention, RoPE Positional Encoding, Multimodal Models, ReAct Agent Loop, Multi-Agent Orchestration) and seven volume quick-references, one per curriculum volume. Keep them open while working through labs and projects - every command is copy-paste ready.

## Tool Cheat Sheets

### [CHEAT-SHEET-001: Docker Commands](./CHEAT-SHEET-001-Docker.md)
Containers, images, volumes and networking in one page.

### [CHEAT-SHEET-002: Python for AI/ML](./CHEAT-SHEET-002-Python-AI.md)
The Python idioms, libraries and snippets used across the curriculum.

### [CHEAT-SHEET-003: Git & Version Control](./CHEAT-SHEET-003-Git.md)
Everyday Git for AI projects - branching, remotes, history surgery.

### [CHEAT-SHEET-004: Linux Commands for AI/ML](./CHEAT-SHEET-004-Linux.md)
Shell commands, permissions and process management on the lab machines.

### [CHEAT-SHEET-005: RAG Systems](./CHEAT-SHEET-005-RAG-Systems.md)
Chunking, embedding, retrieval and generation parameters at a glance.

### [CHEAT-SHEET-006: Kubernetes for LLM Deployment](./CHEAT-SHEET-006-Kubernetes.md)
Deployments, services, scaling and GPU scheduling for LLM serving.

### [CHEAT-SHEET-007: vLLM Serving & Inference](./CHEAT-SHEET-007-vLLM-Serving.md)
Serving, quantization, parallelism and tuning flags for the vLLM inference server.

### [CHEAT-SHEET-008: Reasoning Models & Test-Time Compute](./CHEAT-SHEET-008-Reasoning-Models.md)
Reasoning-effort levels, thinking budgets, reasoning parsers and self-consistency patterns for reasoning models.

### [CHEAT-SHEET-009: Local Inference with llama.cpp & Ollama](./CHEAT-SHEET-009-Local-Inference.md)
GGUF downloads, llama.cpp build/serve flags, Ollama run and Modelfile customization, and offload tuning for local machines.

### [CHEAT-SHEET-010: Alignment Methods — DPO, RLHF & GRPO](./CHEAT-SHEET-010-Alignment-Methods.md)
DPO's implicit-reward loss, RLHF's three-stage pipeline, and GRPO's verifiable-reward loop with the knobs each family tunes.

### [CHEAT-SHEET-011: Evaluation & Benchmarking](./CHEAT-SHEET-011-Evaluation-Benchmarking.md)
The everyday benchmark map, lm-evaluation-harness commands, pass@k estimator math, and LLM-as-judge hygiene rules.

### [CHEAT-SHEET-012: LLM Guardrails & Agent Security](./CHEAT-SHEET-012-LLM-Guardrails-Agent-Security.md)
The guardrail map from input filter to signed agent bus, Presidio operator vocabulary, and the window-seam rate-limit trap.

### [CHEAT-SHEET-013: Structured Output & Function Calling](./CHEAT-SHEET-013-Structured-Output-Function-Calling.md)
The grammar-to-mask mechanism, the schema knob per serving stack, and the syntax-guarantees-semantics-trains ledger.

### [CHEAT-SHEET-014: Decoding & Sampling Strategies](./CHEAT-SHEET-014-Decoding-Sampling-Strategies.md)
The sampler stack order rule, temperature's reshape invariant, and the rank-vs-mass-vs-ratio truncation map.

### [CHEAT-SHEET-015: Quantization Formats & Methods](./CHEAT-SHEET-015-Quantization-Formats-Methods.md)
The bpw block arithmetic behind Q4_0/Q4_K, the three GGUF families, and the EXL2/AWQ/GPTQ GPU-only map.

### [CHEAT-SHEET-016: LoRA & QLoRA](./CHEAT-SHEET-016-LoRA-QLoRA.md)
The low-rank arithmetic and the three knobs, the QLoRA 4-bit pipeline, and the merge-on-FP16 rule.

### [CHEAT-SHEET-017: KV Cache](./CHEAT-SHEET-017-KV-Cache.md)
The per-token memory formula, the MHA/GQA/MQA head ledger, paged allocation, and prefix caching with copy-on-write.

### [CHEAT-SHEET-018: Speculative Decoding](./CHEAT-SHEET-018-Speculative-Decoding.md)
The draft-target bet with the speedup math, the acceptance mechanics, the draft ladder, and the length-tuning discipline.

### [CHEAT-SHEET-019: Tokenizers](./CHEAT-SHEET-019-Tokenizers.md)
The BPE merge loop with the byte-level twist, the Unigram contrast, SentencePiece settings, and the vocab ladder.

### [CHEAT-SHEET-020: Flash Attention](./CHEAT-SHEET-020-Flash-Attention.md)
The memory-hierarchy argument, the online-softmax block update, the FA1-FA2-FA3 ladder, the three enablement paths, and the when-not rules.

### [CHEAT-SHEET-021: RoPE Positional Encoding](./CHEAT-SHEET-021-RoPE-Positional-Encoding.md)
The three failure modes, the rotation construction, the relative-position property, the wiring discipline, and the PI/YaRN extension knobs.

### [CHEAT-SHEET-022: Multimodal Models](./CHEAT-SHEET-022-Multimodal-Models.md)
The two-generation split, CLIP's contrastive objective, the VLM recipe and its token math, LLaVA discipline, multimodal RAG, the audio spectrogram/codec split, and the voice-pipeline budget.

### [CHEAT-SHEET-023: ReAct Agent Loop](./CHEAT-SHEET-023-ReAct-Agent-Loop.md)
The Thought-Action-Observation loop, the ReAct vs chain-of-thought split, the tool contract that feeds errors back as observations, the hard iteration cap, trace-as-memory state discipline, and plan-then-execute.

### [CHEAT-SHEET-024: Multi-Agent Orchestration](./CHEAT-SHEET-024-Multi-Agent-Orchestration.md)
The specialist roster and review-retry flow, the topology complexity ledger, the message envelope and handoff capsule, delivery semantics with the dedup ledger, the wait-for-graph deadlock, the mid-run human gate, and consensus by key-voting.

## Volume Quick References

- [1: Infrastructure Fundamentals - Quick Reference](./QUICK-REF-VOLUME-1.md)
- [2: AI/ML Foundations - Quick Reference](./QUICK-REF-VOLUME-2.md)
- [3: LLM Internals - Quick Reference](./QUICK-REF-VOLUME-3.md)
- [4: Quantization & Optimization - Quick Reference](./QUICK-REF-VOLUME-4.md)
- [5: Model Adaptation - Quick Reference](./QUICK-REF-VOLUME-5.md)
- [6: Data Nexus: RAG & Memory - Quick Reference](./QUICK-REF-VOLUME-6.md)
- [7: Production Mastery - Quick Reference](./QUICK-REF-VOLUME-7.md)

One condensed page per volume: the formulas, flags and commands each volume's modules lean on.

## Related Documentation

- [Volumes](../../volumes/) - the full curriculum behind the quick references
- [Labs](../labs/) - where the commands get exercised for real
- [Troubleshooting](../troubleshooting/) - when a command does not behave

---

**Total Cheat Sheets:** 31 documents
