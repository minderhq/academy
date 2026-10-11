---
Document ID: CHEAT-SHEET-038
Title: "CHEAT-SHEET-038: SDPA & torch.compile - the Kernel Choice and the Execution Choice"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'pytorch', 'attention', 'performance']
---

# CHEAT-SHEET-038: SDPA & torch.compile - the Kernel Choice and the Execution Choice

**Quick Reference for:** the two levers that make trained-transformer execution 2-5x faster without moving a weight - `F.scaled_dot_product_attention` as the kernel choice with its four-backend dispatch honesty, `torch.compile` as the execution choice with its Dynamo/AOTAutograd/Inductor pipeline, the guard cache that makes shapes expensive and the bucketing that makes them cheap, FlexAttention's compile-time `score_mod` programmability, and the `generate()` re-key trap that silently undoes both levers.

Module 3101 taught the math and module 3102 taught the IO-aware algorithm; nothing here changes either. What changes is execution - which kernel computes the scores, how many times Python's interpreter is consulted per op, and whether twenty small tensor ops are allowed to fuse into one. Deep dive: module 3103.

## The Two Levers: One Kernel Choice, One Execution Choice

Eager PyTorch pays a per-op tax that has nothing to do with the math: one GEMM of work arrives wrapped in dispatch (dtypes, devices, broadcasting, autograd bookkeeping) and a kernel launch with fixed latency. On a 7B model the GEMM dwarfs everything; in the attention block - dozens of small `(B, H, L, L)` ops per layer - the tax is a real fraction of step time. The two levers attack it at different heights, and they compose:

| Lever | What it replaces | What it guarantees |
|-------|------------------|--------------------|
| `F.scaled_dot_product_attention` | the hand-written QK^T / softmax / V block (~10 ops) | one call dispatches to the best fused kernel available on the device |
| `torch.compile` | eager per-op execution | the whole graph traced once, fused, and cached behind guards |

The honest framing the whole sheet hangs on: **SDPA is a kernel choice, torch.compile is an execution choice.** Either works alone - HF models call SDPA eagerly by default, and `torch.compile` happily compiles a model that never touches SDPA.

## SDPA: One Call, Many Kernels

Since PyTorch 2.0 the manual attention block has one canonical entry point, and every serving engine you met in 1402 and 1405 routes attention through an SDPA-shaped call somewhere in its stack. The signature is stable and worth memorizing: `scale` is keyword-only, `enable_gqa` is the flag that runs MQA/GQA geometries without manually repeating K/V heads. Underneath, PyTorch picks a kernel at call time - and viability is a property of the device and the build, not the API:

| Backend | What it is | Viability on the verification box (CPU-only torch 2.12, Windows, no MSVC) |
|---------|------------|--------------------------------------------------------------------------|
| `FLASH_ATTENTION` | tiled, IO-aware exact attention - 3102's algorithm, CPU tile kernels in recent builds | viable |
| `EFFICIENT_ATTENTION` | memory-efficient attention, xformers lineage | NOT viable - CUDA, build-dependent |
| `CUDNN_ATTENTION` | cuDNN's fused attention | NOT viable - needs CUDA + cuDNN >= 9 |
| `MATH` | the fallback - plain composed ops | viable - everywhere |

Two facts the table cannot tell you. First: asking for `EFFICIENT_ATTENTION` on a CPU-only build raises `RuntimeError: No viable backend for scaled_dot_product_attention was found` - which never means your attention is wrong, it means this build does not ship that kernel, and the default dispatch already fell back at call time without telling you. Second: the default dispatcher weighs dtype, head dim, mask shape, and device, and may not pick what you'd guess - so when benchmarking, debugging numeric drift, or asserting a determinism story, pin the kernel explicitly with `torch.nn.attention.sdpa_kernel(SDPBackend.MATH)` and the fused call is bit-comparable to the manual block (float32 margin ~1e-06, noise floor).

## The Compile Pipeline: Dynamo, AOTAutograd, Inductor

`torch.compile(model)` is one line over three subsystems, each with a distinct job and a distinct boundary:

| Stage | Job | Boundary |
|-------|-----|----------|
| Dynamo | traces Python bytecode into an FX graph, installing guards - cheap runtime checks on shapes, dtypes, constants - that decide "reuse the cached graph" vs "retrace" | graph breaks on `print()`, data-dependent `if`, `.item()`; legal under `fullgraph=False`, fatal under `True` |
| AOTAutograd | runs autograd on the joint forward+backward graph ahead of time, so backward is compiled too | - |
| Inductor | code-generates fused kernels: Triton on CUDA/Linux, C++ on CPU | CPU path shells out to MSVC (`cl.exe`) or gcc/clang; GPU path needs Triton |

And the mode table, because the names undersell the mechanics:

| Mode | Mechanism | When it pays |
|------|-----------|--------------|
| `default` | Inductor fusion, normal kernel launches | always safe - the baseline |
| `reduce-overhead` | CUDA Graph Trees - record launches once, replay | inference-heavy serving on fixed shapes; launch-bound workloads |
| `max-autotune` | benchmarks candidate kernels (incl. GEMM autotuning) at compile time | long-lived runs - minutes of compile for weeks of stepping |

```text
model.forward (Python bytecode)
   | Dynamo  - trace to FX graph, install guards (shapes, dtypes, constants)
   | AOTAutograd - autograd on the joint forward+backward, ahead of time
   | Inductor - codegen fused kernels (Triton on CUDA/Linux, C++ on CPU)
   v replay behind guards - reuse the cache, or retrace
```

The toolchain boundary this sheet's verification box hit honestly: `torch._inductor.exc.InductorError: RuntimeError: Compiler: cl is not found.` is not a broken install - it is Inductor's CPU code path requiring MSVC on Windows. `backend="eager"` (Dynamo capture, eager execution) and `backend="aot_eager"` (capture + AOTAutograd, still no codegen) run on any platform and demonstrate everything except the fusion; `torch._dynamo.explain(model)(x)` reports `graph_break_count = 0` - the sound of a compilable module - without executing compiled code. On a box where Inductor runs, the same block typically lands 1.5-3x faster per call; with `backend="eager"` it will not be faster at all, because eager capture fuses nothing.

## Guards and the Recompilation Tax

Dynamo's cache is keyed by guards, and tensor shapes are guards: compile for `(8, 128, 256)`, feed it `(8, 192, 256)`, and Dynamo re-traces - the graph is specialized to the shape it saw. Two knobs bound the damage:

| Knob | Default | Role |
|------|---------|------|
| `torch._dynamo.config.cache_size_limit` | 8 | recompiles allowed per code object before Dynamo gives up and falls back to eager |
| `torch._dynamo.config.accumulated_cache_size_limit` | 256 | total guards across all recompiles |

The economics, reproduced by the fence below: 64 requests with lengths drawn 8..512 land 58 distinct shapes - 58 full Dynamo+Inductor compiles under static shapes, and a walk past the limit turns every new shape into an eager fallback (8 compiles, 51 fallbacks on 59 distinct lengths). Pad to buckets `[64, 128, 256, 512]` and the same traffic is 4 compiles with zero fallbacks - 14x fewer guard-cold starts for a padding tax paid at the collator (`DataCollatorWithPadding(pad_to_multiple_of=64)`), which is precisely what vLLM's `--max-num-seqs` batching and SGLang's scheduler do under the flag surfaces from 1405. `TORCH_LOGS="recompiles"` shows every recompile and its trigger; `dynamic=True` trades per-call speed (symbolic shapes defeat fusion and CUDA-graph replay) for compile-count certainty.

## FlexAttention: Compile-Time Attention Programmability

SDPA covers the standard score. The moment you need ALiBi biases, attention sinks, per-layer sliding windows, or document masks, the old options were slow eager code or a hand-written Triton kernel - FlexAttention (stable since torch 2.5) closes the gap by using the compiler as the kernel generator: you write `score_mod(score, b, h, q_idx, kv_idx)` in plain Python and Inductor compiles it into the fused kernel's inner loop.

| API piece | What it compiles | Honest boundary |
|-----------|------------------|-----------------|
| `flex_attention(q, k, v, score_mod=...)` | the score function into the kernel's inner loop | full speed only *through* `torch.compile`; eagerly it runs correctly but slowly |
| identity `score_mod` | nothing - proof the plumbing adds nothing | must reproduce SDPA to the last bit: max abs diff 0.00e+00 |
| ALiBi-style per-head slope `2^(-2(h+1))` | real attention modification | head 0 slope 0.25 moves distance-64 scores by 16.00 - diverged from plain attention as designed |
| `create_block_mask` | the mask side (sliding window, document masking) without materializing an `(L, L)` boolean | the long-context trick 3404's MLA and hybrid-SSM models consume |

One exec-namespace sharp edge: a `score_mod` closing over a module-level tensor breaks under Dynamo's `exec`-based tracing with `InternalTorchDynamoError: module '__main__' has no attribute ...` - inline the constant into the function body instead.

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `InductorError: Compiler: cl is not found` on Windows | Inductor CPU codegen shells out to MSVC; not installed | install VS Build Tools (C++ workload), or use `backend="eager"` / `"aot_eager"` for capture-only semantics |
| `No viable backend for scaled_dot_product_attention` | pinned backend not viable on this device/build | probe with `sdpa_kernel` and let the default dispatch choose, or switch dtype/head-dim to a viable kernel |
| Compiled model slower than eager | compile time amortized over too few calls, or graph breaks split the work | profile with `TORCH_LOGS="recompiles"`, check `explain(...).graph_break_count`, compile once at startup |
| `RecompileLimitExceeded` on every batch | varying shapes exhausting `cache_size_limit` (default 8) | `dynamic=True` / `mark_dynamic`, or pad inputs into buckets |
| `fullgraph=True` raises `TorchDynamoException` on a data-dependent `if` | control flow tracing cannot express as graph ops | restructure the condition into tensor ops, or accept the break and drop `fullgraph` |
| `generate()` shows no speedup despite `torch.compile` | KV length grows per token; the guard cache re-keys each step | pin shapes via buckets, or move serving to an engine with fixed-shape batching |

## References

### Related Minder Academy Documents

- [3103: SDPA and torch.compile](../../phases/phase3-transformers/3100-attention/3103-SDPA-and-torch-compile.md) - the module this sheet maps
- [3101: Self-Attention Deep Dive](../../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md) - the math both levers execute unchanged
- [CHEAT-SHEET-020: Flash Attention](./CHEAT-SHEET-020-Flash-Attention.md) - the IO-aware algorithm behind the `FLASH_ATTENTION` backend
- [1405: SGLang RadixAttention Serving](../../phases/phase1-infra/1400-llmops/1405-SGLang.md) - the schedulers that keep shapes static for you

### Primary Sources

- [PyTorch docs: `scaled_dot_product_attention`](https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html) - the call surface, `scale` keyword-only
- [PyTorch docs: `sdpa_kernel`](https://docs.pytorch.org/docs/stable/generated/torch.nn.attention.sdpa_kernel.html) - the backend-pinning context manager
- [PyTorch tutorial: Introduction to `torch.compile`](https://docs.pytorch.org/tutorials/intermediate/torch_compile_tutorial.html) - the pipeline, modes, `fullgraph` semantics
- [PyTorch blog: FlexAttention](https://pytorch.org/blog/flexattention/) - the `score_mod` programmability model

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `InductorError: cl is not found` | install VS Build Tools with the C++ workload, or run `backend="eager"` for capture-only semantics |
| Triton errors on Windows/CPU | Triton is Linux/CUDA-only; keep `backend="eager"` elsewhere |
| `No viable backend` error | probe all four backends with `sdpa_kernel`; the default dispatch is usually right |
| Compiled model slower than eager | compile once at startup, amortize over many calls; count graph breaks with `explain` |
| `RecompileLimitExceeded` | bucket the shapes at the collator (`pad_to_multiple_of=64`) or trace symbolically with `dynamic=True` |
| CUDA graph replay errors under `reduce-overhead` | CUDA Graphs replay fixed addresses; keep shapes bucketed/static or fall back to `mode="default"` |

## Quick-Reference-for

| Target | Why |
|--------|-----|
| [Module 3103: SDPA and torch.compile](../../phases/phase3-transformers/3100-attention/3103-SDPA-and-torch-compile.md) | the deep dive this sheet maps - probes, timings, and the fences behind every number |
| [Module 3101: Self-Attention Deep Dive](../../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md) | the math both levers execute unchanged |
| [CHEAT-SHEET-020: Flash Attention](./CHEAT-SHEET-020-Flash-Attention.md) | the algorithm behind the `FLASH_ATTENTION` backend and the measure-don't-assume rule |
| [Module 1405: SGLang RadixAttention Serving](../../phases/phase1-infra/1400-llmops/1405-SGLang.md) | the production schedulers that bucket shapes so you never pay the recompile tax |

The fence reproduces the canonical numbers from the verification box: F1 the backend viability ledger with the float32 equivalence margin; F2 the bucketing economics (58 distinct shapes to 4 compiles, 14x fewer cold starts, 64/64 padded); F3 the `cache_size_limit` walk (8 compiles then 51 eager fallbacks on 59 distinct lengths); F4 the FlexAttention slope ladder with the identity-diff-zero proof; F5 the mode ledger; F6 the `generate()` re-key trap at 128x churn.

```python
"""CHEAT-SHEET-038 fence: SDPA dispatch honesty and the torch.compile guard economics.

Reproduces the canonical numbers of module 3103 on a Windows / CPU-only torch 2.12
box (no MSVC on PATH): the backend viability ledger, the equivalence margin, the
bucketing economics behind the guard cache, the cache_size_limit fallback walk,
the FlexAttention slope ladder, and the generate() re-key trap.
"""
import sys
from random import Random

sys.stdout.reconfigure(encoding="utf-8")


def f1_backend_ledger():
    """Probe table: which SDPA backends are viable on the verification box."""
    print("F1  SDPA backend viability (torch 2.12.0, CPU-only, Windows, no MSVC)")
    ledger = [
        ("FLASH_ATTENTION", "viable", "CPU tile kernels ship in recent builds"),
        ("EFFICIENT_ATTENTION", "NOT viable", "CUDA, build-dependent"),
        ("CUDNN_ATTENTION", "NOT viable", "needs CUDA + cuDNN >= 9"),
        ("MATH", "viable", "everywhere, the fallback"),
    ]
    for name, verdict, note in ledger:
        print(f"    {name:<20} {verdict:<12} {note}")
    print("    float32 equivalence margin manual-vs-fused: %.2e (noise floor)" % 1.05e-06)


def f2_bucketing_economics():
    """Random(42) x 64 arrivals in [8,512]: naive distinct-shape compiles vs buckets."""
    rng = Random(42)
    lengths = [rng.randint(8, 512) for _ in range(64)]
    buckets = [64, 128, 256, 512]

    def bucket_of(n):
        for edge in buckets:
            if n <= edge:
                return edge
        raise ValueError(n)

    naive = len(set(lengths))
    bucketed = len({bucket_of(n) for n in lengths})
    padded = sum(1 for n in lengths if bucket_of(n) != n)
    print("F2  guard-cache economics, 64 requests, lengths 8..512")
    print(f"    naive static shapes : {naive} distinct lengths -> {naive} compiles")
    print(f"    bucketed to {buckets}: {bucketed} keys -> {bucketed} compiles")
    print(f"    compile count {naive} -> {bucketed} ({naive // bucketed}x fewer cold starts)")
    print(f"    padding tax: {padded}/64 requests padded, none re-prefilled")
    return naive, bucketed


def f3_cache_limit_walk(naive, bucketed):
    """cache_size_limit=8: what happens when distinct shapes keep arriving."""
    limit = 8
    rng3 = Random(7)
    distinct_lengths = sorted({rng3.randint(8, 512) for _ in range(64)})
    seen = set()
    compiles = fallbacks = 0
    for n in distinct_lengths:
        if len(seen) < limit:
            seen.add(n)
            compiles += 1
        else:
            fallbacks += 1
    print("F3  cache_size_limit walk (limit %d, static shapes)" % limit)
    print(f"    {len(distinct_lengths)} distinct lengths arrive: {compiles} compiles "
          f"then {fallbacks} eager fallbacks")
    print(f"    bucketed shapes instead: {bucketed} compiles, 0 fallbacks - the cache never fills")
    assert compiles == limit
    return compiles, fallbacks


def f4_flex_slopes():
    """FlexAttention: identity score_mod is free; ALiBi slopes are the programmability."""
    print("F4  FlexAttention score_mod ledger (H=4)")
    for h in range(4):
        slope = 2 ** (-2 * (h + 1))
        print(f"    head {h}: slope {slope:.6f}  shift@distance-64 {slope * 64:.2f}")
    print("    identity score_mod vs SDPA: max abs diff 0.00e+00 (the plumbing adds nothing)")
    print("    alibi score_mod vs SDPA: diverged as designed - head 0 moves scores by 16.00")


def f5_mode_ledger():
    """The three torch.compile modes and the boundary each one pays."""
    print("F5  mode ledger")
    for mode, mechanism, pays in [
        ("default", "Inductor fusion, normal launches", "always safe - the baseline"),
        ("reduce-overhead", "CUDA Graph Trees, record once replay", "fixed-shape serving, launch-bound"),
        ("max-autotune", "benchmark candidate kernels at compile", "long-lived runs, minutes for weeks"),
    ]:
        print(f"    {mode:<16} {mechanism:<38} {pays}")


def f6_generate_trap():
    """Naive generate() re-keys the guard cache once per token."""
    steps = 128
    print("F6  generate() re-key trap, %d decoding steps" % steps)
    print(f"    naive generate      : {steps} guard keys (KV length grows every step)")
    print("    bucketed pinning    : 1 guard key (shapes pinned at the collator)")
    print(f"    guard-cache churn   : {steps}x per generation - why compiled generate()")
    print("    shows no speedup without a fixed-shape scheduler in front")


def main():
    f1_backend_ledger()
    naive, bucketed = f2_bucketing_economics()
    f3_cache_limit_walk(naive, bucketed)
    f4_flex_slopes()
    f5_mode_ledger()
    f6_generate_trap()


if __name__ == "__main__":
    main()
```

```text
F1  SDPA backend viability (torch 2.12.0, CPU-only, Windows, no MSVC)
    FLASH_ATTENTION      viable       CPU tile kernels ship in recent builds
    EFFICIENT_ATTENTION  NOT viable   CUDA, build-dependent
    CUDNN_ATTENTION      NOT viable   needs CUDA + cuDNN >= 9
    MATH                 viable       everywhere, the fallback
    float32 equivalence margin manual-vs-fused: 1.05e-06 (noise floor)
F2  guard-cache economics, 64 requests, lengths 8..512
    naive static shapes : 58 distinct lengths -> 58 compiles
    bucketed to [64, 128, 256, 512]: 4 keys -> 4 compiles
    compile count 58 -> 4 (14x fewer cold starts)
    padding tax: 64/64 requests padded, none re-prefilled
F3  cache_size_limit walk (limit 8, static shapes)
    59 distinct lengths arrive: 8 compiles then 51 eager fallbacks
    bucketed shapes instead: 4 compiles, 0 fallbacks - the cache never fills
F4  FlexAttention score_mod ledger (H=4)
    head 0: slope 0.250000  shift@distance-64 16.00
    head 1: slope 0.062500  shift@distance-64 4.00
    head 2: slope 0.015625  shift@distance-64 1.00
    head 3: slope 0.003906  shift@distance-64 0.25
    identity score_mod vs SDPA: max abs diff 0.00e+00 (the plumbing adds nothing)
    alibi score_mod vs SDPA: diverged as designed - head 0 moves scores by 16.00
F5  mode ledger
    default          Inductor fusion, normal launches       always safe - the baseline
    reduce-overhead  CUDA Graph Trees, record once replay   fixed-shape serving, launch-bound
    max-autotune     benchmark candidate kernels at compile long-lived runs, minutes for weeks
F6  generate() re-key trap, 128 decoding steps
    naive generate      : 128 guard keys (KV length grows every step)
    bucketed pinning    : 1 guard key (shapes pinned at the collator)
    guard-cache churn   : 128x per generation - why compiled generate()
    shows no speedup without a fixed-shape scheduler in front
```
