---
Document ID: 1405
Title: "1405: SGLang RadixAttention Serving"
Phase: 1
Module: 1400
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'llmops', 'sglang', 'serving', 'vllm']
---

# 1405: SGLang RadixAttention Serving

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Comparison](#comparison)
- [RadixAttention](#radixattention)
- [Installation](#installation)
- [Launching the Server](#launching-the-server)
- [Memory Budget](#memory-budget)
- [Offline Engine API](#offline-engine-api)
- [The Frontend DSL](#the-frontend-dsl)
- [Structured Outputs](#structured-outputs)
- [Speculative Decoding](#speculative-decoding)
- [Prefill-Decode Disaggregation](#prefill-decode-disaggregation)
- [Production Deployment](#production-deployment)
- [Benchmarking Honestly](#benchmarking-honestly)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Place SGLang in the 2026 serving landscape: the RadixAttention engine that turns shared prompt prefixes into a cache hit
- Explain the radix-tree KV reuse and compute the prefill savings on a multi-turn, shared-system-prompt workload
- Launch the server with the flags that matter on an 11GB-class GPU (mem-fraction-static, context-length, kv-cache-dtype)
- Drive the offline Engine API and the fork/gen frontend DSL for multi-call programs
- Constrain generation with xgrammar-backed JSON schema — at the sampling-params level and the OpenAI response_format level
- Read the PD-disaggregation and router topology (cache-aware policy) that large fleets run, and the Prometheus metrics that watch them

---

## Abstract

SGLang is a fast serving framework for large language models and vision-language models, Apache 2.0, from the paper *Efficiently Programming Large Language Models using SGLang* (Zheng et al., 2023). Two ideas carry it: **RadixAttention**, which stores the KV cache in a radix tree so any request whose token prefix was seen before reuses it instead of recomputing, and a **zero-overhead CPU scheduler** overlapped with GPU execution. Around that core it ships the production set — continuous batching, paged attention, speculative decoding, prefill-decode (PD) disaggregation, structured outputs, FP8/FP4/INT4/AWQ/GPTQ quantization, and multi-LoRA batching — behind an OpenAI-compatible API on port 30000. Where 1402's vLLM is the general-purpose default, SGLang's edge is workloads that *share prefixes*: multi-turn chat, agents that re-send a long system prompt every step, few-shot templates, and fork/join generation programs. The runnable examples in this lesson serve the same 11GB constraint as 1402 — an AWQ 4-bit checkpoint — because fp16 7B weights (~15GB) do not fit.

## Comparison

| Feature | vLLM (1402) | TGI (1402) | SGLang (this lesson) |
|---------|-------------|------------|----------------------|
| KV prefix reuse | prefix caching (auto) | No | RadixAttention (radix tree, on by default) |
| Continuous batching | Yes | Yes | Yes |
| Structured output | guided decoding | — | xgrammar/outlines backends (JSON schema, regex, EBNF) |
| Speculative decoding | Yes | Experimental | EAGLE / EAGLE3 + MTP heads |
| PD disaggregation | — | — | first-class (prefill/decode roles + transfer backends) |
| Programmatic multi-call DSL | No | No | Yes (fork/gen/select frontend) |
| Status (Oct 2026) | default engine | archived Mar 2026 | active, aggressive release cadence (0.5.x) |
| License | Apache 2.0 | Apache 2.0 | Apache 2.0 |

All three expose an HTTP API; SGLang's is OpenAI-compatible (`/v1`) plus a native `/generate` with richer sampling params. The honest positioning: pick vLLM for breadth and ecosystem, SGLang when prefix sharing dominates your traffic — and measure, because the winner is workload-shaped (see Benchmarking Honestly).

## RadixAttention

vLLM's PagedAttention solved KV *allocation* (pages instead of contiguous buffers). RadixAttention attacks the other axis: KV *reuse across requests*. The cache is a radix tree keyed by token id; a new request walks the tree as far as its prompt matches, and every matched node's KV comes back for free — no re-prefill. Anything that shares a prefix hits it:

```text
Radix tree after a day of traffic (one shared system prompt, three chats):

                 [system prompt KV]          ← computed once, reused by all
                /               \
        [chat A turn 1]     [chat B turn 1]
             |                   |
        [chat A turn 2]     [chat B turn 2]

TTFT for chat C's first turn = 0 prefill tokens for the shared prefix —
the tree walk finds it. Multi-turn chat B's second request re-prefills
only the new tokens, not the whole conversation.
```

The arithmetic below is the whole feature in miniature — a shared system prompt plus a few-shot block dominates real agent traffic, and the radix cache turns that dominance into savings:

```python
# Prefill arithmetic with and without a radix cache.
# Workload: one 512-token system prompt, one 256-token few-shot block,
# three users x three turns, each turn adding a 48-token user message
# and generating a 200-token answer (KV for generated tokens is cached too).

SYSTEM, FEW_SHOT, USER_MSG, GEN = 512, 256, 48, 200
BASE = SYSTEM + FEW_SHOT          # prefix every request carries

def turn_tokens(with_cache):
    """Prefill tokens paid per turn, across 3 users x 3 turns."""
    total = 0
    for _ in range(3):            # users
        context = BASE
        for _ in range(3):        # turns within one conversation
            context += USER_MSG   # the new user message joins the context
            # without a cache every request re-prefills its whole context;
            # with the radix cache only the delta past the longest cached
            # prefix is computed (context minus what the tree already holds)
            total += context if not with_cache else USER_MSG
            context += GEN        # the answer becomes cached context too
    return total

cold = turn_tokens(with_cache=False)   # every request re-prefills all
warm = turn_tokens(with_cache=True)    # only unseen deltas are prefilled
print(f"requests: 9 (3 users x 3 turns)")
print(f"prefill without cache: {cold} tokens")
print(f"prefill with radix cache: {warm} tokens")
print(f"saved: {cold - warm} tokens ({100 * (cold - warm) / cold:.0f}%)")
```

Two rules the tree imposes: the cache is **exact** (a hit requires a true token-prefix match — no semantic similarity), and it is **evictable** (LRU, bounded by the same memory budget as everything else — a hit rate near zero on random prompts means you are paying tree bookkeeping for nothing, which is why random-input benchmarks disable it).

## Installation

```bash
# PyPI wheel (Linux + CUDA; Python >= 3.10). sglang pins its stack hard —
# as of 0.5.21 it wants torch==2.13.0, sglang-kernel, flashinfer and
# flash-attn 4, so install into a fresh environment, not your training venv.
uv pip install "sglang[all]"

# Verify
python -c "import sglang; print(sglang.__version__)"
```

```bash
# Docker is the reproducible path — pin a versioned tag, not latest:
#   v0.5.21-cu130   current release line (CUDA 13, Hopper/Blackwell)
#   dev-cu12        frozen final CUDA 12 build (Ampere and older drivers)
docker pull lmsysorg/sglang:v0.5.21-cu130
```

The hard pins are deliberate: the engine's kernels (`sglang-kernel`, flashinfer) are compiled against specific torch/CUDA pairs. On an 11GB-class single GPU this lesson stays at `--tp 1`; larger topologies (`--tp 2/4/8`, `--dp`, expert parallelism) follow the same flags.

## Launching the Server

```bash
# One command, OpenAI-compatible server on port 30000.
# python -m sglang.launch_server is the long form; `sglang serve` is the
# newer alias for the same entrypoint.
python -m sglang.launch_server \
  --model-path Qwen/Qwen3-8B-AWQ \  # pre-quantized AWQ: ungated, fits 11GB
  --mem-fraction-static 0.85 \                 # fraction of VRAM for weights + KV
  --context-length 8192 \                      # slice below the checkpoint's ceiling
  --port 30000

# --model is accepted as the short alias of --model-path.
# --served-model-name overrides the name the API advertises (defaults to
# the model path) — set it before clients hard-code the string.
```

```bash
# Native endpoint: /generate takes flat sampling_params. Among them the
# structured-output triple json_schema / regex / ebnf (exactly one):
curl -s http://localhost:30000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The capital of France is",
    "sampling_params": {"temperature": 0, "max_new_tokens": 64}
  }'
```

```python
# Same server through the OpenAI client — base_url carries /v1 and the
# model name must match what the server advertises (1402's rule again).
from openai import OpenAI

client = OpenAI(base_url="http://localhost:30000/v1", api_key="dummy")

response = client.chat.completions.create(
    model="Qwen/Qwen3-8B-AWQ",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=512,
)
```

## Memory Budget

The knobs differ from vLLM's by name and behave the same in kind: `--mem-fraction-static` (not `gpu-memory-utilization`) fixes the weights + KV budget up front; the remainder is left for activations and CUDA graphs. The 11GB arithmetic from 1402 carries over unchanged — the KV/token cost is model geometry, not engine choice:

```text
GPU VRAM (11GB, --mem-fraction-static 0.85 → ~9.35GB budget):
┌────────────────────────────────────────────────────┐
│ Model weights           ~6.1GB (Qwen3-8B AWQ 4-bit)│
├────────────────────────────────────────────────────┤
│ Radix-tree KV cache   ~1.5-2.5GB (the reuse pool)  │
├────────────────────────────────────────────────────┤
│ Activations + graphs  ~1-2GB                       │
└────────────────────────────────────────────────────┘

KV math (Qwen3-8B, fp16 KV, GQA): 2 (K+V) × 36 layers × 1024
kv-dim × 2 bytes ≈ 144KB per token — one 8k sequence ≈ 1.2GB.
The radix tree spends this same budget, but re-sells it as
prefix hits. Halve the cache bytes with --kv-cache-dtype fp8_e4m3
(latency-quality tradeoff: measure before shipping it).
```

## Offline Engine API

Batch jobs skip the HTTP server entirely — `sgl.Engine` runs the scheduler in-process:

```python
import sglang as sgl

# Offline engine: same scheduler, no HTTP layer.
llm = sgl.Engine(
    model_path="Qwen/Qwen3-8B-AWQ",  # ungated pre-quantized AWQ
    mem_fraction_static=0.85,                    # server flags become ctor kwargs,
    context_length=8192,                         # dashes -> underscores
)

sampling_params = {"temperature": 0.8, "top_p": 0.95, "max_new_tokens": 128}
prompts = [
    "The capital of France is",
    "The largest ocean on Earth is",
    "Photosynthesis converts",
]

outputs = llm.generate(prompts, sampling_params)  # batch -> list of dicts
for prompt, out in zip(prompts, outputs):
    print(f"{prompt} -> {out['text'].strip()[:60]!r}")

llm.shutdown()   # release the GPU - the engine owns scheduler processes
```

The response dict carries `text` plus `meta_info` (prompt/completion token counts — the honest-throughput inputs). An `async_generate` mirror exists for asyncio code; `sgl.Engine` is the only entrypoint batch jobs need.

## The Frontend DSL

SGLang's original contribution beyond the engine is a small embedded language for *programs of generation calls* — forks, joins, choices — that the runtime compiles into batched scheduling. `@sgl.function` decorates a generator over a state `s`; `sgl.gen` is non-blocking, so consecutive calls issue in parallel and RadixAttention makes their shared prefix cheap:

```python
import sglang as sgl

@sgl.function
def tip_suggestion(s):
    s += sgl.system("You are a helpful assistant.")       # shared prefix ->
    s += sgl.user("Give two tips for staying healthy.\n") # cached once for both forks
    forks = s.fork(2)                                     # branch the conversation
    for i, f in enumerate(forks):
        f += sgl.assistant(
            f"Expand tip {i + 1} into one paragraph: "
            + sgl.gen("detailed_tip", max_tokens=256, stop="\n\n")
        )
    s += sgl.assistant("Tip 1:" + forks[0]["detailed_tip"])
    s += sgl.assistant("Tip 2:" + forks[1]["detailed_tip"])
    s += sgl.assistant(                                   # join: both branches
        "To summarize: " + sgl.gen("summary", max_tokens=512)  # feed the summary
    )

# run against a default runtime (an Engine or server URL);
# the state object is a dict keyed by every gen() name
state = tip_suggestion.run()
print(state["summary"])
```

The named `gen(...)` calls are the DSL's contract: results land in the returned state by name, which is also what makes these programs unit-testable — swap the runtime for a mock and the control flow still runs.

## Structured Outputs

Constrained decoding is a first-class sampling param, not a bolt-on. The default grammar backend is **xgrammar** (Outlines is the alternative via `--grammar-backend`), and the constraint triple is exactly one of `json_schema`, `regex`, `ebnf` per request. Build the request body and you can read the whole contract without a server:

```python
import json

# The native /generate contract: sampling_params carries at most ONE of
# json_schema / regex / ebnf - the server rejects a request with two.
schema = {
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "population": {"type": "integer"},
    },
    "required": ["city", "population"],
}

body = {
    "text": "Give the population of the capital of France in JSON.\n",
    "sampling_params": {
        "temperature": 0,
        "max_new_tokens": 64,
        "json_schema": json.dumps(schema),   # the schema travels as a JSON string
    },
}
assert sum(k in body["sampling_params"] for k in
           ("json_schema", "regex", "ebnf")) == 1   # the one-constraint rule
print(json.dumps(body, indent=2))

# OpenAI-client shape of the same constraint (chat completions):
# response_format={"type": "json_schema", "json_schema": {"name": ..., "schema": <dict>}}
```

Because the grammar is compiled and enforced per token, the output *cannot* violate the schema — no retry loop, no parse-and-pray. This is the reliable layer under every "structured agent output" claim (7203's elicitation forms consume exactly this kind of contract).

## Speculative Decoding

The flags mirror 4202's theory — a small draft model proposes, the target verifies in one forward pass:

```bash
# EAGLE-family speculation: topk 1 draft path, 3 steps, 4 draft tokens
python -m sglang.launch_server \
  --model-path Qwen/Qwen3-8B-AWQ \
  --speculative-algorithm EAGLE \
  --speculative-eagle-topk 1 \
  --speculative-num-steps 3 \
  --speculative-num-draft-tokens 4
```

`--speculative-algorithm EAGLE3` adds the standalone EAGLE3 draft head (`--speculative-draft-model-path`); models shipping an MTP head can ride the same EAGLE path with the head bundled. Acceptance-rate reality from 4202 applies verbatim: speculation is a bet — code-heavy or templated text accepts well, high-temperature creative text can end *slower* than the plain engine.

## Prefill-Decode Disaggregation

At fleet scale, prefill (compute-bound, bursty) and decode (memory-bandwidth-bound, steady) contend for the same GPUs. SGLang's answer is role-split servers plus a KV-transfer backend:

```bash
# Prefill-only node
python -m sglang.launch_server --model-path <MODEL> \
  --disaggregation-mode prefill --port 8000

# Decode-only node
python -m sglang.launch_server --model-path <MODEL> \
  --disaggregation-mode decode --port 8001

# The router in front (sgl-router), cache-aware: it routes requests to
# the prefill node already holding their prefix in the tree
python -m sglang_router.launch_router \
  --pd-disaggregation \
  --policy cache_aware \
  --prefill http://<prefill-ip>:8000 8998 \
  --decode http://<decode-ip>:8001 \
  --host 0.0.0.0 --port 6688
```

`--disaggregation-transfer-backend` defaults to `mooncake` (InfiniBand/RDMA-oriented; `nixl` and vendor backends exist). The prefill node's bootstrap port (default 8998) is the KV-handoff rendezvous. This is one tier above single-node serving — do not reach for it before the radix cache and batching knobs are actually saturated; the cache-aware router and PD split exist to solve measured bottlenecks, not anticipated ones.

## Production Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sglang
  namespace: ai-services
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sglang
  template:
    metadata:
      labels:
        app: sglang
    spec:
      nodeSelector:
        accelerator: nvidia   # must match the GPU node label (see 1301)
      containers:
      - name: sglang
        image: lmsysorg/sglang:v0.5.21-cu130   # pinned release, not latest
        args:
          - --model-path
          - Qwen/Qwen3-8B-AWQ   # ungated pre-quantized AWQ
          - --mem-fraction-static
          - "0.85"
          - --context-length
          - "8192"
          - --enable-metrics
        ports:
        - containerPort: 30000
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "12Gi"
        volumeMounts:
        - name: models
          mountPath: /root/.cache/huggingface
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: hf-model-cache
```

Metrics follow the same pattern as vLLM's: `--enable-metrics` serves Prometheus at `/metrics` on the server port. The names to alert on:

```text
sglang:num_running_reqs          gauge — executing now
sglang:num_queue_reqs            gauge — queued (KV or scheduler bound)
sglang:token_usage               gauge — KV pool fill fraction
sglang:cache_hit_rate            gauge — THE RadixAttention metric: near zero
                                 means the tree is pure overhead for this traffic
sglang:prompt_tokens_total       counter — prefill; rate() it for prefill tok/s
sglang:generation_tokens_total   counter — decode; rate() it for gen tok/s
sglang:time_to_first_token_seconds   histogram — prefix hits should crush this
sglang:e2e_request_latency_seconds   histogram — p99 via histogram_quantile()

--enable-mfu-metrics adds estimated-FLOP/byte counters for MFU math.
```

`sglang:cache_hit_rate` is the metric 1402 has no answer to — it is the direct read on whether RadixAttention is paying for itself on your traffic.

## Benchmarking Honestly

The rules are 1402's, plus one SGLang-specific trap: **the radix cache is a benchmark-invalidating instrument**. Identical prompts, multi-turn replays, and shared few-shot blocks all become cache hits — you would be measuring your generator's repetitiveness, not the engine. Random-input benchmarks disable it:

```bash
# For fair engine-vs-engine numbers on random prompts:
python -m sglang.launch_server --model-path <MODEL> --disable-radix-cache
```

Measure on your own hardware, with your own prompt distribution, both with and without the cache — the delta *is* your workload's radix dividend, and it ranges from nothing (random prompts) to dominant (agent fleets re-sending the same 10k-token system prompt every step).

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `torch==2.13.0 is not installed` at install | sglang's hard stack pins collide with your training venv | fresh environment; do not fight the pins |
| CUDA 12 driver, image exits immediately | `v0.5.21-cu130` needs CUDA 13 | `dev-cu12` (frozen CUDA 12 line) or upgrade the driver |
| OOM at startup | `mem-fraction-static` too high for weights + graphs | drop to 0.8; smaller `--context-length`; check `nvidia-smi` |
| Latency *rose* after enabling speculation | low acceptance rate on your text distribution | 4202's rule: measure acceptance; disable on creative sampling |
| Benchmark numbers impossibly good | radix cache hit on repeated prompts | `--disable-radix-cache` for random-input comparisons |
| Two constraint params in one request → 400 | the json_schema/regex/ebnf triple is exclusive | exactly one per request |
| PD setup hangs at bootstrap | prefill bootstrap port (8998) unreachable from decode | open the port; check transfer backend prerequisites |

## Summary

SGLang is the serving engine whose organizing idea is reuse: RadixAttention keeps the KV cache in a radix tree so shared prompt prefixes pay prefill once, and the fork/gen frontend lets programs express multi-call generation that the scheduler batches and the tree discounts. The production surface — OpenAI-compatible server on 30000, xgrammar structured outputs, EAGLE speculation, PD disaggregation behind a cache-aware router, Prometheus metrics with the one metric vLLM lacks (`cache_hit_rate`) — sits on the same 11GB constraint as 1402, where the AWQ checkpoint is the price of admission. The through-line with its sibling lesson: the engine choice is workload-shaped, the winner is measured, and the radix dividend only exists if your traffic actually shares prefixes.

## References

### Primary Sources

- SGLang documentation — docs.sglang.io (server arguments, offline engine API, frontend tutorial, structured outputs, production metrics)
- Zheng et al., 2023 — *SGLang: Efficient Execution of Structured Language Model Programs* (RadixAttention, SGVM)
- PyPI `sglang` 0.5.21 (stack pins, extras) · Docker Hub `lmsysorg/sglang` (v0.5.21-cu130, dev-cu12)

### Related Minder Academy Documents

- [1402: vLLM and TGI High-Concurrency Inference](1402-vLLM-and-TGI.md)

---

## Next Steps

- Next Module: **[1500: Monitoring](../1500-monitoring/README.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related Documents:**

- [1302: GPU Scheduler](../1300-kubernetes/1302-GPU-Scheduler.md)
- [1402: vLLM and TGI](./1402-vLLM-and-TGI.md)
- [4202: Speculative Decoding](../../phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md)
- [4102: EXL2 and AWQ](../../phase4-quantization/4100-low-bit/4102-EXL2-and-AWQ.md)
