---
Document ID: CHEAT-SHEETS-README
Title: "Quick Reference Cheat Sheets"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Beginner
Tags: ['cheatsheet', 'reference']
---

# Quick Reference Cheat Sheets

Sixty single-page references: fifty-three tool cheat sheets and seven volume quick-references, one per curriculum volume. Keep them open while working through labs and projects - every command is copy-paste ready.

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
The two-generation split, CLIP's contrastive objective, the VLM recipe with its token math, and the audio spectrogram/codec split behind the voice pipeline.

### [CHEAT-SHEET-023: ReAct Agent Loop](./CHEAT-SHEET-023-ReAct-Agent-Loop.md)
The Thought-Action-Observation loop, the tool contract that feeds errors back as observations, and the hard iteration cap that bounds the agent.

### [CHEAT-SHEET-024: Multi-Agent Orchestration](./CHEAT-SHEET-024-Multi-Agent-Orchestration.md)
The specialist roster and review-retry flow, the message envelope and handoff capsule, delivery semantics with the dedup ledger, and the mid-run human gate.

### [CHEAT-SHEET-025: Agent Memory Systems](./CHEAT-SHEET-025-Agent-Memory-Systems.md)
The four-tier memory map, the recency-relevance-importance blend, the write and read paths behind their token budgets, and the consolidation lifecycle.

### [CHEAT-SHEET-026: Agent Security](./CHEAT-SHEET-026-Agent-Security.md)
The five-layer defense stack, the regex-floor and NER-ceiling PII pipeline, the HMAC-nonce identity contract, and the deterministic-testing ledger.

### [CHEAT-SHEET-027: Tool Calling and MCP](./CHEAT-SHEET-027-Tool-Calling-and-MCP.md)
The N+M integration economics, the JSON-RPC wire with its two error doors, the v2 decorator contract, and the caller-side resilience stack.

### [CHEAT-SHEET-028: Agent Evaluation and Observability](./CHEAT-SHEET-028-Agent-Evaluation-and-Observability.md)
The three-rung evaluation ladder, trajectories as the unit of record, the four deterministic scorers, the pairwise judge's swap cure, and the trace schema.

### [CHEAT-SHEET-029: Function Calling Training and Constrained Decoding](./CHEAT-SHEET-029-Function-Calling-Training-and-Constrained-Decoding.md)
The grammar-to-mask mechanism and its per-state legal-set ladder, prompting versus masking, and the one-time train bill that buys every later request its speedup.

### [CHEAT-SHEET-030: Multi-Agent Communication Protocols](./CHEAT-SHEET-030-Multi-Agent-Communication-Protocols.md)
The typed message envelope and its correlation contract, the topology ledger, voting versus the judge model, and jitter against synchronized retry waves.

### [CHEAT-SHEET-031: Multi-Agent Framework Comparison](./CHEAT-SHEET-031-Multi-Agent-Framework-Comparison.md)
The comparison matrix and its boolean scorecards, the version reality behind the frameworks, the executable decision table, and the hybrid split of graph-owns-flow and agent-owns-talk.

### [CHEAT-SHEET-032: Code Interpreter Sandbox](./CHEAT-SHEET-032-Code-Interpreter-Sandbox.md)
The four-tier sandbox ladder under the weakest-tier rule, the resource limits that bind the child, the import-line screen, and the Jupyter kernel's persistent scratch memory.

### [CHEAT-SHEET-033: LLM Observability](./CHEAT-SHEET-033-LLM-Observability.md)
The four LLM-specific metric families and their alert thresholds, the timing trio with its decode-rate trap, the hallucination ladder, and the nearest-rank percentile rule.

### [CHEAT-SHEET-034: SGLang RadixAttention Serving](./CHEAT-SHEET-034-SGLang-RadixAttention-Serving.md)
The radix-tree KV reuse engine and its prefill ledger, the KV budget on one card, the one-constraint output rule, and the EAGLE speculation bet.
### [CHEAT-SHEET-035: Beyond Attention - SSMs and MLA](./CHEAT-SHEET-035-Beyond-Attention-SSMs-and-MLA.md)
The fixed-state SSM recurrence, Mamba's selectivity gate, the recall weakness that makes production models hybrid, and MLA's compressed cache.
### [CHEAT-SHEET-036: Vector Memory - the Embedding-Backed Store](./CHEAT-SHEET-036-Vector-Memory-Embedding-Backed-Store.md)
The four memory types and their storage shapes, the write and read paths behind their gates and budgets, the Qdrant contract, and the lifecycle jobs.
### [CHEAT-SHEET-037: Reflection & Self-Correction - the Loop That Grades Its Own Work](./CHEAT-SHEET-037-Reflection-Self-Correction.md)
The draft-critique-revise loop, self-consistency as the plurality amplifier, the intrinsic-versus-informed boundary, and the campaign ledger that prices critique discipline.
### [CHEAT-SHEET-038: SDPA & torch.compile - the Kernel Choice and the Execution Choice](./CHEAT-SHEET-038-SDPA-and-torch-compile.md)
SDPA as the kernel choice, torch.compile as the execution choice, FlexAttention's compile-time programmability, and the generate() re-key trap that undoes both.

### [CHEAT-SHEET-039: Word Embeddings - the Tradition That Turned Co-occurrence into Coordinates](./CHEAT-SHEET-039-Word-Embeddings-Tradition.md)
The one-hot storage ledger and its dead geometry, skip-gram and CBOW trained from scratch, GloVe's frequency-cancelling ratios, and the analogy arithmetic's static limit.

### [CHEAT-SHEET-040: Model Merging - the Arithmetic That Combines Trained Models](./CHEAT-SHEET-040-Model-Merging.md)
The task vector and its dose dial, TIES' trim-elect-merge, DARE's drop-and-rescale, SLERP's arc, and the soup's distributional guarantee.
### [CHEAT-SHEET-041: Activations & Normalization - the Nonlinearity and the Statistics](./CHEAT-SHEET-041-Activations-and-Normalization.md)
ReLU against the smooth curve family, GELU's tanh approximation, SwiGLU's 1.5x bill, the gate zoo, LayerNorm versus RMSNorm, and the Pre-LN stream.
### [CHEAT-SHEET-042: Extreme Quantization - the Method Choice, the File Choice, the Training-Time Frontier](./CHEAT-SHEET-042-Extreme-Quantization.md)
GPTQ's forward error movement, AWQ's salience-weighted budget, the file choice as a deployment decision, sparsity's break-even, and ternary as a training-time commitment.

### [CHEAT-SHEET-043: 4-Bit Residuals - the Metadata Squeeze and the Hardware-Native Grid](./CHEAT-SHEET-043-4-Bit-Residuals.md)
Double quantization of the scales themselves, the NF4 and e2m1 grids, MXFP4 versus NVFP4, the outlier blast radius, and gpt-oss's selective census.
### [CHEAT-SHEET-044: Quantization-Aware Training - the Straight-Through Estimator and the Layer Map](./CHEAT-SHEET-044-Quantization-Aware-Training.md)
Fake quantization's round trip with the straight-through estimator, the inf-seeding observer, the transformer layer map, the outlier tax, and the progressive schedule.
### [CHEAT-SHEET-045: Synthetic Data & Advanced Training - the Distilled Student, the Federated Fleet, and the Recursion Tax](./CHEAT-SHEET-045-Synthetic-Data-Advanced-Training.md)
Distillation's temperature law, FedAvg's weighted fleet, the DP-SGD clip-noise adapter, the self-instruct bootstrap, and the model-collapse walk with its anchor.
### [CHEAT-SHEET-046: Advanced Optimization - the Optimizer Memory Ledger, the Schedule Arc, and the Failure Toolbox](./CHEAT-SHEET-046-Advanced-Optimization.md)
The optimizer memory ledger, Adam's scale-free first step, the warmup-decay schedule arc, the failure toolbox, SAM's flat-minima search, and the LR range test.
### [CHEAT-SHEET-047: Retrieval Strategies - the Two-Channel Fusion, the Rerank Funnel, and the Diversity Dial](./CHEAT-SHEET-047-Retrieval-Strategies.md)
BM25 and the dense channel, RRF and the alpha dial joining them, the cross-encoder rerank funnel, the MMR diversity dial, and the provenance boost.
### [CHEAT-SHEET-048: Semantic Vectors - the HNSW Ledger, the Recall Dial, and the Truncation Contract](./CHEAT-SHEET-048-Semantic-Vectors.md)
What the vector is, how cosine and dot measure closeness, the HNSW walk with its ef dial, the MRL truncation contract, and the anisotropy trap.

### [CHEAT-SHEET-049: Context Engineering - the Dilution Curve, the Stuffing Bet, and the Distilled Prompt](./CHEAT-SHEET-049-Context-Engineering.md)
The dilution curve behind the advertised window, the two-ledger price and the stuffing bet against retrieval, the routed budget, ring attention's group shift, and the distilled prompt.

### [CHEAT-SHEET-050: MLOps Pipelines - the Lifecycle State Machine, the Challenger Verdict, and the Fleet Bill](./CHEAT-SHEET-050-MLOps-Pipelines.md)
The MLOps pipeline surface in seven priced exhibits - lifecycle gates, challenger statistics, registry mechanics, re-embedding policy, and the fleet's three bills.
### [CHEAT-SHEET-051: Distributed Training - the Memory Bill, the Stability Wall, and the Campaign](./CHEAT-SHEET-051-Distributed-Training.md)
The per-rank memory bill, the sharding ladder, the pipeline bubble, FSDP2's three states, the float8 dead zone, and the warmup-sized LR wall with the five-bill campaign.
### [CHEAT-SHEET-052: Framework Engineering - the Registry, the Batching Flush, and the Rollout Gate](./CHEAT-SHEET-052-Framework-Engineering.md)
The registry economy, the deep-merge config resolve, the batching flush law, the paged KV bill, the limiter trio, the rollout ladder, and the chi-squared verdict.
### [CHEAT-SHEET-053: Vector Databases - the RAM Ledger, the Quantile Trap, and the Rescore Ladder](./CHEAT-SHEET-053-Vector-Databases.md)
The RAM ledger arithmetic, the distance trio, the SQ quantile trap, binary and product quantization floors, the oversample x rescore ladder, and the snapshot RPO bill.
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

**Total Cheat Sheets:** 60 documents
