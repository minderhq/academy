---
Document ID: 3103
Title: "3103: SDPA and torch.compile - The Same Math, Faster"
Phase: 3
Module: 3100
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'attention', 'pytorch', 'performance']
---

# 3103: SDPA and torch.compile - The Same Math, Faster

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Eager Tax](#the-eager-tax)
- [SDPA: One API, Many Kernels](#sdpa-one-api-many-kernels)
- [torch.compile: Dynamo, AOTAutograd, Inductor](#torchcompile-dynamo-aotautograd-inductor)
- [Guards and the Recompilation Tax](#guards-and-the-recompilation-tax)
- [FlexAttention: Compile-Time Attention Programmability](#flexattention-compile-time-attention-programmability)
- [Transformers Integration](#transformers-integration)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After reading this lesson, you will be able to:

- Explain why eager PyTorch pays a per-op overhead that has nothing to do with the math
- Call `F.scaled_dot_product_attention` instead of hand-rolled attention and know which kernel actually runs
- Pin a backend with `sdpa_kernel` and read a "No viable backend" error honestly
- Describe the Dynamo → AOTAutograd → Inductor pipeline and what each stage contributes
- Predict when `torch.compile` recompiles from guards - and cap that tax with shape buckets
- Use FlexAttention's `score_mod` to define custom attention semantics in plain Python

**Estimated Time:** 4 hours (1 hour reading, 3 hours hands-on with the fences)

## Abstract

Everything 3101 taught you about attention is math: scores, softmax, weighted values.
Nothing in this lesson changes that math. What changes is execution - which kernel
computes the scores, how many times Python's interpreter is consulted per operation,
and whether the framework is allowed to fuse twenty small tensor ops into one.

PyTorch gives you two levers, and they compose:

| Lever | What it replaces | What it guarantees |
|-------|------------------|--------------------|
| `F.scaled_dot_product_attention` (SDPA) | your hand-written QK^T/softmax/V block | one call dispatches to the best fused kernel available on the device |
| `torch.compile` | eager per-op execution | the whole model traced once, fused, and cached behind guards |

The honest framing: **SDPA is a kernel choice, torch.compile is an execution choice.**
You can use either without the other - HF models call SDPA eagerly by default, and
`torch.compile` happily compiles a model that never touches SDPA. Together they are
how a trained transformer stops leaving 2-5x of throughput on the table without a
single weight moving.

## The Eager Tax

Run one attention-math line eagerly - `scores = q @ k.transpose(-2, -1) / (D ** 0.5)`,
the first line of the manual block below. Three things happen. The math (one GEMM,
one scalar divide). The dispatch (PyTorch
figures out dtypes, devices, broadcasting rules, autograd bookkeeping). And the
launch (a kernel is enqueued; on GPU each launch has fixed latency). For a
7B-parameter model the GEMM dwarfs everything. For the *attention block* - dozens of
small ops per layer, each shaped `(B, H, L, L)` - dispatch and launch overhead is a
real fraction of step time, and none of it is your math.

Eager mode sells debuggability for that overhead: every op runs alone, you can print
any intermediate. Compilers buy the overhead back by looking at the whole graph at
once. The two levers in this lesson are the two places PyTorch collects (and fence 1
below times both sides of the line you just read):

```text
per-op eager execution
  └─ op-level fix:  SDPA - replace ~10 ops with 1 fused kernel call
  └─ graph-level fix: torch.compile - trace once, fuse across ops, replay behind guards
```

## SDPA: One API, Many Kernels

Since PyTorch 2.0, the manual attention block has a single canonical entry point:

```python
import torch
import torch.nn.functional as F

query = torch.randn(2, 8, 128, 64)   # (B, H, L, E)
key = torch.randn(2, 8, 128, 64)     # (B, H, S, E)
value = torch.randn(2, 8, 128, 64)   # (B, H, S, Ev)

out = F.scaled_dot_product_attention(
    query,
    key,
    value,
    attn_mask=None,
    dropout_p=0.0,
    is_causal=False,
    scale=None,         # overrides 1/sqrt(E); keyword-only
    enable_gqa=False,   # grouped-query attention: fewer K/V heads than Q heads
)
print(out.shape)  # (2, 8, 128, 64)
```

The signature is stable and worth memorizing, because every serving engine you met in
1402 and 1405 - vLLM, SGLang, HF - routes its attention through an SDPA-shaped call
at some layer of its stack. `enable_gqa` is the flag that makes MQA/GQA configs (3101
covered the math; 4102's AWQ checkpoints ship GQA geometries) work without manually
repeating K/V heads.

Underneath, PyTorch picks a kernel at call time:

| Backend | What it is | Where it lives |
|---------|------------|----------------|
| `FLASH_ATTENTION` | tiled, IO-aware exact attention (3102's algorithm) | CUDA; CPU tile kernels in recent builds |
| `EFFICIENT_ATTENTION` | memory-efficient attention (xformers lineage) | CUDA (build-dependent) |
| `CUDNN_ATTENTION` | cuDNN's fused attention | CUDA with cuDNN ≥ 9 |
| `MATH` | the fallback - plain composed ops | everywhere |
| `OVERRIDEABLE` | marker for backends a custom dispatcher may replace | - |

Two facts the table cannot tell you, and both bite in practice:

1. **Viability is a property of the device and the build, not the API.** Asking for
   `EFFICIENT_ATTENTION` on a CPU-only build raises
   `RuntimeError: No viable backend for scaled_dot_product_attention was found`.
   The fence below probes every backend on *your* box and prints which ones live -
   on this lesson's verification box (torch 2.12.0, CPU-only), `FLASH_ATTENTION`
   (CPU tiles) and `MATH` run, `EFFICIENT_ATTENTION` and `CUDNN_ATTENTION` do not.
2. **The default dispatcher may not pick what you'd guess.** Auto-selection weighs
   dtype, head dim, mask shape, and device. When you are benchmarking, debugging a
   numeric drift, or asserting a determinism story, pin the kernel explicitly with
   the context manager:

```python
import torch
import torch.nn.functional as F
from torch.nn.attention import sdpa_kernel, SDPBackend

q = torch.randn(1, 4, 64, 32)
k = torch.randn(1, 4, 64, 32)
v = torch.randn(1, 4, 64, 32)

with sdpa_kernel(SDPBackend.MATH):
    out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
print(out.shape)  # (1, 4, 64, 32) - same math, pinned kernel
```

The fence: first prove the fused call is *bit-comparable* to the manual math, then
probe each backend's viability on this device, then time forced-MATH against the
auto-selected default:

```python
import time
import torch
import torch.nn.functional as F
from torch.nn.attention import sdpa_kernel, SDPBackend

torch.manual_seed(0)
B, H, L, D = 2, 8, 256, 64
q = torch.randn(B, H, L, D)
k = torch.randn(B, H, L, D)
v = torch.randn(B, H, L, D)

# (1) equivalence: manual math vs the fused SDPA call
scores = q @ k.transpose(-2, -1) / (D ** 0.5)
mask = torch.triu(torch.ones(L, L, dtype=torch.bool), diagonal=1)
scores = scores.masked_fill(mask, float("-inf"))
manual = scores.softmax(dim=-1) @ v
fused = F.scaled_dot_product_attention(q, k, v, is_causal=True)
assert torch.allclose(manual, fused, atol=1e-5), (manual - fused).abs().max()
print("equivalence: max abs diff %.2e" % (manual - fused).abs().max().item())

# (2) dispatch honesty: backends are hardware/build-dependent - probe each one
for backend in (SDPBackend.FLASH_ATTENTION, SDPBackend.EFFICIENT_ATTENTION,
                SDPBackend.CUDNN_ATTENTION, SDPBackend.MATH):
    try:
        with sdpa_kernel(backend):
            out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        ok = torch.allclose(out, fused, atol=1e-5)
        print(f"{backend.name}: viable, output matches = {ok}")
    except RuntimeError as exc:
        msg = str(exc).split(". ")[0]
        print(f"{backend.name}: NOT viable on this device/build -> {msg[:60]}")

# (3) timing: forced MATH vs the auto-selected default backend
def bench(fn, iters=50):
    fn()
    t0 = time.perf_counter()
    for _ in range(iters):
        fn()
    return (time.perf_counter() - t0) / iters * 1e3

with sdpa_kernel(SDPBackend.MATH):
    math_ms = bench(lambda: F.scaled_dot_product_attention(q, k, v, is_causal=True))
default_ms = bench(lambda: F.scaled_dot_product_attention(q, k, v, is_causal=True))
print(f"per-call ms: MATH {math_ms:.3f} vs default dispatch {default_ms:.3f}")
```

The equivalence margin (~1e-6) is float32 noise; the interesting line is the probe
table, because it is different on every machine you will ever own. Reading it is a
skill: *no viable backend* never means your attention is wrong - it means the build
on this box does not ship that kernel, and SDPA will have fallen back at call time
without telling you.

## torch.compile: Dynamo, AOTAutograd, Inductor

`torch.compile` takes a module or function and returns a compiled callable:

```text
torch.compile(model,
              fullgraph=False,    # True: raise on any graph break instead of splitting
              dynamic=None,       # True: trace shapes symbolically from call one
              backend="inductor", # the code generator ('eager'/'aot_eager' always exist)
              mode="default",     # 'reduce-overhead' | 'max-autotune' | 'default'
              options=None,       # backend-specific dict
              disable=False)      # True: no-op - un-compile without touching call sites
```

One line, three subsystems, each with a distinct job:

```text
model.forward (Python bytecode)
   │
   ▼
Dynamo     traces bytecode into an FX graph, installing GUARDS -
           cheap runtime checks (shapes, dtypes, constants, no side effects)
           that decide "reuse the cached graph" vs "retrace"
   │
   ▼
AOTAutograd runs autograd on the *joint* forward+backward graph ahead of time,
           so the backward pass is compiled too - not reconstructed op-by-op
   │
   ▼
Inductor   code-generates fused kernels: Triton on CUDA/Linux,
           C++ on CPU - and needs a working toolchain for the latter
```

The `mode` table, because the names undersell the mechanics:

| Mode | Mechanism | When it pays |
|------|-----------|--------------|
| `default` | Inductor fusion, normal kernel launches | always safe; the baseline |
| `reduce-overhead` | CUDA Graph Trees - record kernel launches once, replay | inference-heavy serving on fixed shapes; kernel-launch-bound workloads |
| `max-autotune` | benchmark many candidate kernels (incl. GEMM autotuning) at compile time | long-lived training runs; worth minutes of compile for weeks of stepping |

And the backend honesty that most tutorials skip: `inductor` is the default, but it
is *not* free to run. Its CPU code path shells out to a C++ compiler (`cl.exe` on
Windows, gcc/clang elsewhere); its GPU path needs Triton, which is Linux/CUDA-only.
The verification box for this lesson - Windows, CPU-only torch 2.12, no MSVC on
PATH - raises exactly:

```text
torch._inductor.exc.InductorError: RuntimeError: Compiler: cl is not found.
```

That is not a broken install; it is the toolchain boundary. `backend="eager"` (Dynamo
capture, eager execution of the captured graph) and `backend="aot_eager"` (capture +
AOTAutograd, still no codegen) work on any platform and demonstrate the tracing,
guards, and caching - everything except the fusion. The fence below uses
`backend="eager"` so it runs anywhere, and `torch._dynamo.explain` to report the
graph-break count without executing compiled code:

```python
import torch
import torch.nn as nn

torch.manual_seed(0)

class Block(nn.Module):
    def __init__(self, d=256, h=8):
        super().__init__()
        self.ln1 = nn.LayerNorm(d)
        self.attn = nn.MultiheadAttention(d, h, batch_first=True)
        self.ln2 = nn.LayerNorm(d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d))

    def forward(self, x):
        a, _ = self.attn(self.ln1(x), self.ln1(x), self.ln1(x), need_weights=False)
        x = x + a
        return x + self.mlp(self.ln2(x))

model = Block()
x = torch.randn(8, 128, 256)

# backend='eager': Dynamo captures the graph, then runs it eagerly -
# no Inductor codegen needed, so this works on any platform
compiled = torch.compile(model, backend="eager")
out_eager = model(x)
out_compiled = compiled(x)
print("equivalence: max abs diff %.2e" % (out_eager - out_compiled).abs().max().item())

# second call hits the guard-checked cache instead of re-tracing
out_again = compiled(x)
assert torch.allclose(out_compiled, out_again)
print("second call: served from the guard-checked compiled cache")

# explain(): trace without executing - report the graph-break count
from torch._dynamo import explain
exp = explain(model)(x)
print(f"explain: graph breaks = {exp.graph_break_count}, ops captured = {exp.op_count}")
```

`graph breaks = 0` is the sound of a compilable module: every op fit one FX graph.
A `print()`, a data-dependent `if`, or a `.item()` in the forward would split the
graph - legal under the default `fullgraph=False` (Dynamo compiles the pieces it
can and runs the rest eagerly), fatal under `fullgraph=True`, and a silent
speedup-killer everywhere in between. That is why 3102's rule of thumb extends here:
**measure, don't assume.** On the box where Inductor runs, the same block under the
default backend typically lands 1.5-3x faster per call; with `backend="eager"` it
will not be faster at all, because eager capture fuses nothing.

## Guards and the Recompilation Tax

Dynamo's cache is keyed by guards, and tensor shapes are guards. Compile for
`(8, 128, 256)`, feed it `(8, 192, 256)`, and Dynamo re-traces - the graph is
*specialized* to the shape it saw. Two config knobs bound the damage:

- `torch._dynamo.config.cache_size_limit` - recompiles allowed per code object before
  Dynamo gives up and falls back to eager (**default 8**)
- `torch._dynamo.config.accumulated_cache_size_limit` - total guards across all
  recompiles (**default 256**)

Diagnostic and escape hatches, in the order you should reach for them:

```bash
# see every recompilation and its trigger
TORCH_LOGS="recompiles" python serve.py

# or, for shape decisions specifically
TORCH_LOGS="dynamic" python serve.py
```

```python
import torch
import torch.nn as nn

model_dyn = nn.Linear(16, 16)
x_dyn = torch.randn(4, 32, 16)

# one graph for all lengths - dynamic dim traced symbolically
compiled_dyn = torch.compile(model_dyn, dynamic=True)  # everything symbolic
torch._dynamo.mark_dynamic(x_dyn, 1)                   # or pin just one dim
                                                       # (tracing-time, before the call)

# pay one compile per bucket instead of one per length
compiled_static = torch.compile(model_dyn)             # static shapes, padded inputs
print("compiled both ways; wrap is lazy - codegen fires on the first call")
```

`dynamic=True` trades per-call speed (symbolic shapes defeat some fusion and all
CUDA-graph replay) for compile-count certainty. Production serving usually prefers
the opposite trade: **static shapes + input padding into buckets** - which is
precisely what vLLM's `--max-num-seqs` batching and SGLang's scheduler do under the
flag surfaces you already know from 1405. The fence makes the economics concrete:

```python
"""Pure-python fence: why dynamic input shapes recompile - and how padding fixes it."""
from random import Random

rng = Random(42)
incoming_lengths = [rng.randint(8, 512) for _ in range(64)]


class CompileCache:
    """Toy model of Dynamo's guard cache: one compiled graph per distinct shape key."""

    def __init__(self):
        self.compiles = 0
        self.graphs = {}

    def run(self, seq_len):
        if seq_len not in self.graphs:
            self.compiles += 1
            self.graphs[seq_len] = f"graph_L{seq_len}"
        return self.graphs[seq_len]


# (1) naive: compile eagerly for every arriving length
naive = CompileCache()
for n in incoming_lengths:
    naive.run(n)
print(f"naive static shapes: {len(set(incoming_lengths))} distinct lengths "
      f"-> {naive.compiles} compiles (each one a full Dynamo+Inductor pass)")

# (2) serving fix: pad every request up to the next bucket edge
BUCKETS = [64, 128, 256, 512]


def bucket_of(seq_len):
    for edge in BUCKETS:
        if seq_len <= edge:
            return edge
    raise ValueError(f"length {seq_len} exceeds the largest bucket {BUCKETS[-1]}")


bucketed = CompileCache()
for n in incoming_lengths:
    bucketed.run(bucket_of(n))
print(f"bucketed to {BUCKETS}: {len(BUCKETS)} possible keys "
      f"-> {bucketed.compiles} compiles total")

assert bucketed.compiles <= len(BUCKETS)
print(f"compile count {naive.compiles} -> {bucketed.compiles} "
      f"({naive.compiles // bucketed.compiles}x fewer guard-cold starts)")
```

The HF serving shape of the same idea - compile the forward once, pad batches into
buckets at the collator:

```python
model.forward = torch.compile(model.forward, mode="reduce-overhead", dynamic=True)
```

```text
DataCollatorWithPadding(tokenizer, pad_to_multiple_of=64)   # collator-level buckets:
# every batch lands on one of a small set of shapes, the guard cache stays
# small, and the compile cost is paid once per bucket instead of once per batch
```

`pad_to_multiple_of=64` is the collator-level version of the fence's buckets: every
batch lands on one of a small set of shapes, the guard cache stays small, and the
compile cost is paid once per bucket instead of once per batch.

## FlexAttention: Compile-Time Attention Programmability

SDPA covers the standard score. The moment you need ALiBi biases, attention sinks,
sliding windows with per-layer widths, or document masks, the options were: fall
back to slow eager code, or hand-write a Triton kernel. FlexAttention (stable since
torch 2.5) closes that gap by *using the compiler as the kernel generator*:

```python
from torch.nn.attention.flex_attention import flex_attention

def score_mod(score, b, h, q_idx, kv_idx):
    # score is the pre-softmax QK^T/sqrt(d) entry for one query-key pair;
    # return any function of it and the indices - FlexAttention compiles
    # this Python into the fused kernel's inner loop
    return score
```

The fence: an identity `score_mod` must reproduce SDPA exactly (proof the plumbing
adds nothing), then an ALiBi-style per-head decay must diverge (proof the
modification is real):

```python
import torch
from torch.nn.attention.flex_attention import flex_attention

torch.manual_seed(0)
B, H, L, D = 2, 4, 64, 32
q = torch.randn(B, H, L, D)
k = torch.randn(B, H, L, D)
v = torch.randn(B, H, L, D)

# plain SDPA as the reference
ref = torch.nn.functional.scaled_dot_product_attention(q, k, v)

# identity score_mod must reproduce SDPA exactly
def identity(score, b, h, q_idx, kv_idx):
    return score

out = flex_attention(q, k, v, score_mod=identity)
print("identity score_mod vs SDPA: max abs diff %.2e" % (out - ref).abs().max().item())

# ALiBi-style: a per-head static slope decays scores with distance
# (slopes 1/4, 1/16, 1/64, 1/256 for the 4 heads - the ALiBi ladder for H=4;
# the slope is inlined because a score_mod closing over a module-level
# tensor breaks under exec'd namespaces - see the failure table)
def alibi(score, b, h, q_idx, kv_idx):
    return score + (1.0 / 2 ** (2 * (h + 1))) * (q_idx - kv_idx)

out_alibi = flex_attention(q, k, v, score_mod=alibi)
assert out_alibi.shape == ref.shape
assert not torch.allclose(out_alibi, ref)  # the modification actually changed attention
print("alibi score_mod: shape", tuple(out_alibi.shape),
      "| diverged from plain attention as designed")
```

FlexAttention reaches full speed only *through* `torch.compile` (wrap it:
`compiled_flex = torch.compile(flex_attention)`); eagerly it runs correctly but
slowly - which is exactly what this fence does on a box without the codegen
toolchain, and why the fence passes anywhere. Sparsity belongs to the sibling API:
`create_block_mask` builds the mask side (sliding window, document masking) without
materializing an `(L, L)` boolean tensor - 3404's MLA and hybrid-SSM models are the
consumers of exactly that trick at long context.

## Transformers Integration

Training-side, the integration is a flag pair - verified fields on transformers
5.10.2's `TrainingArguments`:

```python
from transformers import TrainingArguments

args = TrainingArguments(
    output_dir="./out",
    torch_compile=True,               # compile the forward+loss
    torch_compile_mode="reduce-overhead",  # or 'default' / 'max-autotune'
    # torch_compile_backend="inductor"  # only if you need a non-default backend
)
print(args.torch_compile, args.torch_compile_mode)  # True reduce-overhead
```

Inference-side, compile the forward and keep the shapes static:

```python
import torch
import torch.nn as nn

serving_head = nn.Linear(64, 64)
serving_head.forward = torch.compile(serving_head.forward, mode="reduce-overhead")
print("forward wrapped - codegen fires on the first fixed-shape call")
```

The honest caveat, because `model.generate()` will betray both levers if you let it:
autoregressive decoding grows the KV length every step, so naive `generate` re-keys
the guard cache once per token. Compilation helps generation only when something
pins the shapes - padded batch buckets, or a serving engine (1402, 1405) whose
scheduler already batches at fixed shapes and leaves the HF generate loop behind.

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `InductorError: Compiler: cl is not found` (Windows) | Inductor CPU codegen shells out to MSVC; not installed | install VS Build Tools (C++ workload), or use `backend="eager"`/`"aot_eager"` for capture-only semantics |
| Triton errors on Windows/CPU | Inductor's GPU path needs Triton, Linux/CUDA only | run Inductor on Linux/CUDA; keep `backend="eager"` elsewhere |
| `No viable backend for scaled_dot_product_attention` | pinned backend not viable on this device/build | probe with `sdpa_kernel` and let the default dispatch choose, or switch dtype/head-dim to a viable kernel |
| Compiled model is *slower* than eager | compile time amortized over too few calls, or graph breaks split the work | profile with `TORCH_LOGS="recompiles"`; check `explain(...).graph_break_count`; compile once at startup, not per request |
| Recompile on every batch, then `torch._dynamo.exc.RecompileLimitExceeded` | varying shapes exhausting `cache_size_limit` (default 8) | `dynamic=True` / `mark_dynamic`, or pad inputs into buckets |
| `fullgraph=True` raises `TorchDynamoException` on a data-dependent `if` | control flow that tracing cannot express as graph ops | restructure the condition into tensor ops, or accept the break and drop `fullgraph` |
| CUDA graph replay errors under `mode="reduce-overhead"` with varying shapes | CUDA Graphs replay fixed memory addresses; dynamic shapes invalidate them | keep shapes bucketed/static under `reduce-overhead`, or fall back to `mode="default"` |
| `generate()` shows no speedup despite `torch.compile` | KV length grows per token; guard cache re-keys each step | pin shapes via buckets or move serving to an engine with fixed-shape batching |
| `InternalTorchDynamoError: module '__main__' has no attribute ...` when a `score_mod` runs | the function closes over a module-level tensor while the code executes through `exec` (notebook kernels, doc runners) - Dynamo resolves the closure as a module attribute and misses | inline the constant into the function body (params + literals only), or define and call the `score_mod` from a plain script at top level |

## Summary

SDPA ends the hand-rolled era: one call, and PyTorch dispatches to the fastest viable
kernel - FlashAttention where the hardware supports it, a math fallback where it does
not - and the backend-probe fence makes the choice visible instead of guessed.
torch.compile attacks the other tax, the per-op Python overhead: Dynamo traces,
AOTAutograd partitions, Inductor lowers, and guards decide how long any of it stays
valid. The working rule this lesson leaves: profile before pinning - the default
dispatch already chooses well, compilation pays off only when shapes repeat, and
every escape hatch (`sdpa_kernel`, `dynamic=True`, `backend="eager"`) exists because
the fast path has boundaries this lesson hit honestly on a Windows/CPU box - no MSVC
for Inductor codegen, no Triton, no CUDA.

## References

### Related Minder Academy Documents

- [3101: Self-Attention Deep Dive](./3101-Self-Attention-DeepDive.md) - the math this lesson executes
- [3102: Flash Attention](./3102-Flash-Attention.md) - the IO-aware algorithm behind the `FLASH_ATTENTION` backend
- [3404: Beyond Attention - SSMs and MLA](../3400-architectures/3404-Beyond-Attention-SSMs-and-MLA.md) - the models that need `create_block_mask` and long-context tricks
- [1405: SGLang RadixAttention Serving](../../phase1-infra/1400-llmops/1405-SGLang.md) - production schedulers that keep shapes static for you

### Primary Sources

- [PyTorch docs: `scaled_dot_product_attention`](https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html) - the call surface, `scale` keyword-only.
- [PyTorch docs: `sdpa_kernel`](https://docs.pytorch.org/docs/stable/generated/torch.nn.attention.sdpa_kernel.html) - the backend-pinning context manager.
- [PyTorch tutorial: Introduction to `torch.compile`](https://docs.pytorch.org/tutorials/intermediate/torch_compile_tutorial.html) - Dynamo/AOTAutograd/Inductor as a pipeline, modes and `fullgraph` semantics.
- [PyTorch blog: FlexAttention](https://pytorch.org/blog/flexattention/) - the `score_mod` programmability model this lesson closes on.

---

## Next Steps

- Next Module: **[3200: Embeddings](../3200-embeddings/)**
- Continue with: **[3201: RoPE](../3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Turn the backend probe into a benchmark: time all four SDPA backends at your own
  head counts and dtypes, and find where the default dispatch stops picking the winner.
