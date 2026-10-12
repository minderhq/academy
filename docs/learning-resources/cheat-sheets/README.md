---
Document ID: CHEAT-SHEETS-README
Title: "Quick Reference Cheat Sheets"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Beginner
Tags: ['cheatsheet', 'reference']
---

# Quick Reference Cheat Sheets

Fifty-five single-page references: forty-eight tool cheat sheets (Docker, Python, Git, Linux, RAG, Kubernetes, vLLM, Reasoning, llama.cpp, Alignment, Evaluation, Guardrails, Structured Output, Sampling, Quantization, LoRA, KV Cache, Speculative Decoding, Tokenizers, Flash Attention, RoPE Positional Encoding, Multimodal Models, ReAct Agent Loop, Multi-Agent Orchestration, Agent Memory Systems, Agent Security, Tool Calling and MCP, Agent Evaluation and Observability, Function Calling Training and Constrained Decoding, Multi-Agent Communication Protocols, Multi-Agent Framework Comparison, Code Interpreter Sandbox, LLM Observability, SGLang RadixAttention Serving, Beyond Attention - SSMs and MLA, Vector Memory - the Embedding-Backed Store, Reflection & Self-Correction - the Loop That Grades Its Own Work, SDPA & torch.compile - the Kernel Choice and the Execution Choice, Word Embeddings - the Tradition That Turned Co-occurrence into Coordinates, Model Merging - the Arithmetic That Combines Trained Models, Activations & Normalization - the Nonlinearity and the Statistics, Extreme Quantization - the Method Choice, the File Choice, the Training-Time Frontier, 4-Bit Residuals - the Metadata Squeeze and the Hardware-Native Grid, Quantization-Aware Training - the Straight-Through Estimator and the Layer Map, Synthetic Data & Advanced Training - the Distilled Student, the Federated Fleet, and the Recursion Tax, Advanced Optimization - the Optimizer Memory Ledger, the Schedule Arc, and the Failure Toolbox, Retrieval Strategies - the Two-Channel Fusion, the Rerank Funnel, and the Diversity Dial, Semantic Vectors - the HNSW Ledger, the Recall Dial, and the Truncation Contract) and seven volume quick-references, one per curriculum volume. Keep them open while working through labs and projects - every command is copy-paste ready.

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
### [CHEAT-SHEET-041: Activations & Normalization - the Nonlinearity and the Statistics](./CHEAT-SHEET-041-Activations-and-Normalization.md)
The nonlinearity and the statistics every transformer block stands on: ReLU's three named deaths against the smooth curve family, GELU exact versus the GPT-2 tanh approximation (max err 0.000473, r = 0.99999999), SwiGLU's third projection and its 1.5x bill with the LLaMA 8/3 sizing rule on the 256 grid, the gate zoo (GEGLU, ReGLU, SwiGLU) kept apart from the MoE router that picks experts rather than gating activations, LayerNorm versus RMSNorm at cosine 0.9987 with the mean surviving at +0.050273, Pre-LN's random-walk stream against Post-LN's pin and DeepNorm's alpha-squared fixed point, and the fp32-upcast law - RMSNorm without it zeroes every activation at offset 1000.
### [CHEAT-SHEET-042: Extreme Quantization - the Method Choice, the File Choice, the Training-Time Frontier](./CHEAT-SHEET-042-Extreme-Quantization.md)
What happens below 4 bits: GPTQ moves rounding error forward through the upper Cholesky onto coordinates that absorb it (weight error up, output error down 0.9541x), AWQ spends the FP16 budget where the activation-weighted salience says (34% overlap with the magnitude top, 0.8409x vs 0.9269x on the same budget), the file choice is deployment not math (GGUF two-step with --imatrix over F16 for CPU/Apple, EXL2's per-layer 2-8 bit mix for NVIDIA), sparsity pays index bits until the break-even (67% at FP16+CSR, 89% at INT4+CSR, 2:4 on Ampere+), and ternary is a training-time commitment - H = log2(3) = 1.58496 on 2 storage bits, BitLinear's absmean scale taking a planted +8.0 outlier at 1.04x where absmax zeroes the whole row, and the XNOR+popcount identity making 1-bit matmul exact.

### [CHEAT-SHEET-043: 4-Bit Residuals - the Metadata Squeeze and the Hardware-Native Grid](./CHEAT-SHEET-043-4-Bit-Residuals.md)
The 4-bit price that moved outside the elements: double quantization quantizes the scales themselves (32768 fp16 scales become 32770 bytes at max deviation one 8-bit step, <0.5% ppl, ~0.5 GB banked at 70B), the two grids (NF4\'s sixteen normal-matched levels at mean distance 0.0391, e2m1\'s eight magnitudes with a 4-to-6 leap that forces scale round-UP), MXFP4\'s pow2 tax against NVFP4\'s answer (rel err 0.1163 vs 0.0947 = 1.23x tighter, mean scale-use 4.48 vs 5.94 of 6.0), one planted 100.0 flushing 31/31 block neighbors at a 1/128 blast radius versus 15/15 at 1/256, and gpt-oss-20b\'s selective census: 19.11B expert parameters (91.4%) carrying MXFP4 to 12.8 GB against bf16\'s 38.9 GB (3.04x) while attention, router and embeddings keep bf16.
### [CHEAT-SHEET-044: Quantization-Aware Training - the Straight-Through Estimator and the Layer Map](./CHEAT-SHEET-044-Quantization-Aware-Training.md)
The training pass that makes low bit-widths survivable: fake quantization\'s round trip maxing out at half a step (mean abs err 0.00374) with the straight-through estimator passing gradients through a rounding whose true derivative is exactly 0 (64/64 census; RoundSTE 1000/1000, ClampedSTE 930/1000, HardTanhSTE 965/1000 grads survive), the momentum-0.01 observer whose first batch must seed against inf buffers (sym 0.021631 vs asym 0.021492, 1e-5 floor, eval freezes by design), the priced decision (INT8 routes inside 0.3 of each other, QAT earning its bill at INT4 91.5 and INT3 88.2), the transformer layer map where 6 Linears carry 99.967% of the block\'s weights while softmax/GELU/LayerNorm stay FP32 (per-channel ~1% vs per-tensor ~5% at 4 bits), the outlier tax (one planted 100.0 inflating the min-max scale 32x over the quantile scale), the progressive 8->4->3 schedule at [5, 5, 10] epochs with KL*T^2 distillation, and the six config dimensions behind the Conservative/Balanced/Aggressive templates.
### [CHEAT-SHEET-045: Synthetic Data & Advanced Training - the Distilled Student, the Federated Fleet, and the Recursion Tax](./CHEAT-SHEET-045-Synthetic-Data-Advanced-Training.md)
The two-axis closure of the 5300-synthetic track - what the model trains on and where it trains: distillation\'s temperature law (top 0.986/dark 0.014 at T=1 vs top 0.478/dark 0.522 at T=5, Hinton blend 0.1420), FedAvg\'s sample weighting ([1.1850, 0.8550] weighted vs [1.2000, 0.8833] unweighted, FedProx 0.000681), the fleet arithmetic (4x2x4 = 32, Amdahl s=0.176 predicting 3.58x at N=8, FSDP wrap at the 100k threshold), DP-SGD per-sample clipping (noised sum 5.1702 to avg 1.0340, the rank-16 adapter 38 MB vs 14,000 MB = 371x), the self-instruct bootstrap (keep-rate 32/120 = 0.267 at Jaccard 0.7), the model-collapse walk (types 1082 to 557 in 4 ungated cycles, the 10% anchor buying +165 types at gen 4) and the four-bill campaign (human $524,450, self-instruct $1,603 = 327x, anchored $54,043, ungated collapse $238,608 = 4.4x the anchored bill).
### [CHEAT-SHEET-046: Advanced Optimization - the Optimizer Memory Ledger, the Schedule Arc, and the Failure Toolbox](./CHEAT-SHEET-046-Advanced-Optimization.md)
The per-step stack of the 5500-advanced-optimization track - what moves the weights, when the step size moves, and which tool repairs which failure: the optimizer memory ledger (16N = 112.0 GB at 7B with 84.0 overhead; AdamW8bit ~14.0, Lion 28.0, Adafactor ~56.0, the 8-bit route 70.0 with 10.0 headroom, LoRA 0.84 on the frozen base), Adam\'s scale-free first step (0.00010000 at gradient norm 0.3 and 30.0 alike) and the decay that lives outside (Adam+L2 rides the normalization at a 0.0100 ratio, AdamW uniform 1.000e-06), the schedule arc (cosine lingers 2056 vs linear 951 steps above 0.9 = 2.16x, floor 0.1000 vs 0.0001; LLRD 0.95 embeddings 0.5404), the failure toolbox (norm-clip cosine 1.000000 vs value-clip 0.5149, accumulation 12+1 windows x3 = 39 vs naive 37, undivided loss = lr x8), SAM\'s flat-minima search (per-tensor rho over-perturbs 100.00x, the missing zero_grad trains the SUM at 1.9836x) and the LR range test (steepest 2.057e-04, max_lr 5.214e-04, OneCycle start max_lr/25).
### [CHEAT-SHEET-047: Retrieval Strategies - the Two-Channel Fusion, the Rerank Funnel, and the Diversity Dial](./CHEAT-SHEET-047-Retrieval-Strategies.md)
The retrieval core of the 6200-retrieval track - what joins the two channels, what refines the candidate list, and what shapes the final list: BM25\'s exact-term arithmetic (the tie 0.8338 at the same df=2/dl=6, the rare-term idf lever 1.5694, the dense paraphrase \'feline found resting\' scoring 0), RRF rank fusion 1/(k+rank+1) at k=60 (B 0.032522 over A 0.032266 - ranks enter the sum, raw scales never meet) and the alpha dial over per-query min-max channels (winner A at 0.9, B at 0.5, D at 0.1 - sweep on MAP@10), the rerank funnel (retrieve_n=100 through the bi-encoder, the cross-encoder\'s 200-800 ms dominating the ~1.5 s budget, top_k=10 kept; ColBERT MaxSim 1.9000 vs 0.4000), AP and NDCG on one labeled window (good 1.0000/1.0000; bad 0.5833/0.6653 with both relevant documents found), the MMR dial over the redundancy corpus (cosine five-paraphrase coverage 1/4 ILS 0.89; lam 0.5 all four facts at rel_sum 2.13 ILS 0.15; lam 0.0 admits D8 at cosine -0.661) and the provenance boost placement (fused +0.30 flips 0.90 vs 0.88; clause +0.25 rewrites effective alpha and loses - boost reorders, it never conjures), closing the 6200 track.
### [CHEAT-SHEET-048: Semantic Vectors - the HNSW Ledger, the Recall Dial, and the Truncation Contract](./CHEAT-SHEET-048-Semantic-Vectors.md)
The vector core of the 6100-vector track - what the vector is, how closeness is measured, and how the nearest one is found among a million: the brute-force bill (768.0M MACs per query at 1M x 768, 0.768 s at a 1e9 MAC/s budget, 3.07 GB fp32 resident), the HNSW ledger (P(l)=0.5^l census 0.4906 at L0, per-layer neighbor lists, efConstruction > M or the graph fragments into disconnected cliques, the bounded update that evicts the farthest neighbor), the ef dial (ef=1 caps recall at 0.0233 because ef < k cannot return k results, 0.8633 at ef=32 - the last +21 recall points cost 2x the beam width), the metric dial (dot 300.0 vs cos 1.0000 - magnitude is not meaning; king-queen 0.88/0.9877 against king-man 0.66/0.9830; normalize_L2 both sides + METRIC_INNER_PRODUCT because 1-L2 is NOT cosine), the truncation contract (the MRL-trained order keeps recall@5 at 0.95 with 4 of 64 dims where the shuffled control lands 0.00 - truncation is a property of orderings; 1536->256 deletes 0.8333 of the 6.14 GB bill) and the anisotropy trap (193/200 unrelated raw pairs over a 0.9 threshold against 0/200 centered, related pair 0.9797->0.9762, margin 0.0223 raw vs 0.9924 centered - rank on raw, gate on centered), closing the 6100 track.

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

**Total Cheat Sheets:** 55 documents
