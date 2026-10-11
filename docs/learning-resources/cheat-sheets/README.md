---
Document ID: CHEAT-SHEETS-README
Title: "Quick Reference Cheat Sheets"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Beginner
Tags: ['cheatsheet', 'reference']
---

# Quick Reference Cheat Sheets

Forty-seven single-page references: forty tool cheat sheets (Docker, Python, Git, Linux, RAG, Kubernetes, vLLM, Reasoning, llama.cpp, Alignment, Evaluation, Guardrails, Structured Output, Sampling, Quantization, LoRA, KV Cache, Speculative Decoding, Tokenizers, Flash Attention, RoPE Positional Encoding, Multimodal Models, ReAct Agent Loop, Multi-Agent Orchestration, Agent Memory Systems, Agent Security, Tool Calling and MCP, Agent Evaluation and Observability, Function Calling Training and Constrained Decoding, Multi-Agent Communication Protocols, Multi-Agent Framework Comparison, Code Interpreter Sandbox, LLM Observability, SGLang RadixAttention Serving, Beyond Attention - SSMs and MLA, Vector Memory - the Embedding-Backed Store, Reflection & Self-Correction - the Loop That Grades Its Own Work, SDPA & torch.compile - the Kernel Choice and the Execution Choice, Word Embeddings - the Tradition That Turned Co-occurrence into Coordinates, Model Merging - the Arithmetic That Combines Trained Models) and seven volume quick-references, one per curriculum volume. Keep them open while working through labs and projects - every command is copy-paste ready.

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

### [CHEAT-SHEET-025: Agent Memory Systems](./CHEAT-SHEET-025-Agent-Memory-Systems.md)
The four-tier memory map and the two readers, the recency-relevance-importance blend, write and read paths, the consolidation lifecycle, MemGPT-style context paging, the reflexion loop, and the TTL-eviction-checkpoint contract.

### [CHEAT-SHEET-026: Agent Security](./CHEAT-SHEET-026-Agent-Security.md)
The five-layer defense stack with the honest 5/7 red-team bill, the regex-floor and NER-ceiling PII pipeline, the FGSM flip rule, the HMAC-nonce identity contract and the beacon-CV egress monitor, and the T=0 versus pass@k deterministic-testing ledger.

### [CHEAT-SHEET-027: Tool Calling and MCP](./CHEAT-SHEET-027-Tool-Calling-and-MCP.md)
The N+M integration economics, the JSON-RPC wire with its two error doors, the v2 decorator contract and the client-side validation gate, the result triple, the v1 to v2 rename ledger, and the caller-side resilience stack.

### [CHEAT-SHEET-028: Agent Evaluation and Observability](./CHEAT-SHEET-028-Agent-Evaluation-and-Observability.md)
The three-rung evaluation ladder, trajectories as the unit of record, the four deterministic scorers and the bootstrap CI, the pairwise judge's position bias and swap cure, the OpenTelemetry GenAI trace schema, and the two-tripwire regression gate.

### [CHEAT-SHEET-029: Function Calling Training and Constrained Decoding](./CHEAT-SHEET-029-Function-Calling-Training-and-Constrained-Decoding.md)
The grammar-to-mask mechanism and its per-state legal-set ladder, prompting (0.7940) versus masking (1.0000), the Gorilla pair-training walk to 0.8917, the 1.0000-valid / 0.3033-correct 2x2 trap, and the $2.3760 one-time train bill that buys every later request its 2.1x.

### [CHEAT-SHEET-030: Multi-Agent Communication Protocols](./CHEAT-SHEET-030-Multi-Agent-Communication-Protocols.md)
The typed message envelope and its correlation contract, the topology ledger at N=8 (orchestrator 8 / peer-to-peer 28 / hierarchical 10), voting versus the judge model, the max_rounds=2 debate loop, the context-capsule handoff at 0-of-4 rework, jitter against synchronized retry waves, and budget propagation with fail-fast children.

### [CHEAT-SHEET-031: Multi-Agent Framework Comparison](./CHEAT-SHEET-031-Multi-Agent-Framework-Comparison.md)
The 8-row comparison matrix and its boolean scorecards (tool calling 4/4, human-in-the-loop 3/4, local models 3/4), the version reality - Swarm archived for the OpenAI Agents SDK, AG2 versus the 0.4+ rewrite - the executable decision table with its 24-combination grid sweep (AutoGen 13 / LangGraph 11 / CrewAI 0), the hybrid split of graph-owns-flow and agent-owns-talk, and the resource ledger whose ranking is stable even where the values are estimates.

### [CHEAT-SHEET-032: Code Interpreter Sandbox](./CHEAT-SHEET-032-Code-Interpreter-Sandbox.md)
The four-tier sandbox ladder - process, container, in-process, managed microVM - under the weakest-tier rule, the resource limits that bind the child via preexec_fn (setrlimit in-process never restores), the regex screen over real import lines with the position-versus-os false positive, the ok/failed/blocked envelope, the Jupyter kernel's IOPUB protocol and persistent scratch memory, and the duration-plus-success-rate telemetry that catches runaway agents.

### [CHEAT-SHEET-033: LLM Observability](./CHEAT-SHEET-033-LLM-Observability.md)
The four LLM-specific metric families and their alert thresholds, the timing trio with the decode-rate formula trap (16.7x inflated on long prompts), the TTFT=0.0 histogram guard that keeps fake sub-ms samples out of the percentiles, the quality heuristics with their honest limits, the four-indicator hallucination ladder with its 0.4/0.7 confidence steps, the nearest-rank rule that keeps p95 from being p100 on small samples, and the seven-day cost rollup with its three levers.

### [CHEAT-SHEET-034: SGLang RadixAttention Serving](./CHEAT-SHEET-034-SGLang-RadixAttention-Serving.md)
The radix tree KV reuse engine: the 9576->432 prefill ledger behind one shared 768-token prefix (95% saved), the KV budget on an 11GB card, the one-constraint rule that keeps json_schema, regex and ebnf exclusive, the 17x TTFT radix dividend, the cache_hit_rate zones, and the EAGLE speculation bet priced 0.81x versus 1.69x by acceptance rate.
### [CHEAT-SHEET-035: Beyond Attention - SSMs and MLA](./CHEAT-SHEET-035-Beyond-Attention-SSMs-and-MLA.md)
The post-attention architectures: the fixed-state SSM recurrence and its ZOH discretization, Mamba's selectivity gate where delta_t decides write versus forget, Mamba-2's SSD trade, the MQAR recall weakness that makes every production model a hybrid, the six-model hybrid landscape, and MLA - DeepSeek's compressed cache at 576 elements per token, 56.9x below full MHA and 3.6x below GQA-8.
### [CHEAT-SHEET-036: Vector Memory - the Embedding-Backed Store](./CHEAT-SHEET-036-Vector-Memory-Embedding-Backed-Store.md)
The embedding-backed store: the four memory types and their storage shapes, the write path that extracts one atomic statement per memory behind an importance gate, the read path ranked by similarity x decay x importance and stopped at a token budget, the Qdrant contract of guarded create and payload indexes and versioned collections, the three lifecycle jobs, and the ledger where 1M memories cost ~1.5 GB but 300-500 recall tokens per turn are the real currency.
### [CHEAT-SHEET-037: Reflection & Self-Correction - the Loop That Grades Its Own Work](./CHEAT-SHEET-037-Reflection-Self-Correction.md)
The in-run self-improvement family: the draft-critique-revise loop whose gains track the critique's recall on surface defects, self-consistency as the plurality amplifier that never consults the truth, the intrinsic-versus-informed boundary where hunt-mode rewrites decay and verifier-gated repairs climb, the retry split that prices new information over re-rolls, and the campaign ledger where the same 900-call bill lands +0.130 or -0.160 depending entirely on critique discipline.
### [CHEAT-SHEET-038: SDPA & torch.compile - the Kernel Choice and the Execution Choice](./CHEAT-SHEET-038-SDPA-and-torch-compile.md)
The two execution levers that leave the math untouched: SDPA as the kernel choice with its four-backend dispatch honesty and the sdpa_kernel pin, torch.compile as the execution choice with its Dynamo-AOTAutograd-Inductor pipeline, the guard cache that makes shapes expensive and bucket padding that makes them cheap (58 compiles to 4), FlexAttention's compile-time score_mod programmability, and the generate() re-key trap that silently undoes both.

### [CHEAT-SHEET-039: Word Embeddings - the Tradition That Turned Co-occurrence into Coordinates](./CHEAT-SHEET-039-Word-Embeddings-Tradition.md)
The layer beneath every embedding the curriculum uses later: the one-hot storage ledger and its dead geometry, skip-gram with negative sampling trained from scratch (2.7725 to 1.3743 with the cat-fish first-order outlier), CBOW the mirror objective and its blur, GloVe's ratio table where frequency cancels, and the analogy arithmetic that ends at the static limit the contextual turn answered.

### [CHEAT-SHEET-040: Model Merging - the Arithmetic That Combines Trained Models](./CHEAT-SHEET-040-Model-Merging.md)
The arithmetic that combines trained checkpoints without retraining: the task vector and its dose dial (5.000 to 0.000 down the lambda walk while the forgetting proxy pays the squared length of tau), TIES' trim-elect-merge against the naive sum that cancels a skill coordinate to exactly 0.0, DARE's drop-and-rescale keeping the expected tau while variance pays, SLERP's arc holding 1.0000 where the chord sags to 0.8660 at 60 degrees, and the sixteen-seed soup ledger whose guarantee is distributional - 12.2x versus the average ingredient, never versus the best seed.

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

**Total Cheat Sheets:** 47 documents
