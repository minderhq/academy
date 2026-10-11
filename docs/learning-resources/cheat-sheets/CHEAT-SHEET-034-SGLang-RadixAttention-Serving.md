---
Document ID: CHEAT-SHEET-034
Title: "CHEAT-SHEET-034: SGLang RadixAttention Serving"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'llmops', 'serving', 'sglang']
---

# CHEAT-SHEET-034: SGLang RadixAttention Serving

**Quick Reference for:** the radix prefill ledger that turns one shared 768-token prefix into a 95% prefill saving across nine requests, the KV budget arithmetic (144 KB per token, one 8k sequence 1.2 GB, 9.35 GB usable on an 11GB card), the one-constraint rule that keeps json_schema, regex and ebnf mutually exclusive per request, the TTFT radix dividend (17x lower first-token latency on the tree walk), the cache_hit_rate zones that tell you whether RadixAttention is paying for itself on your traffic, and the speculation bet where EAGLE lands 1.69x at acceptance 0.8 but 0.81x - slower than no speculation at all - at 0.3. CHEAT-SHEET-007 carries the vLLM serving recipes; this sheet owns the reuse engine: vLLM's PagedAttention solved KV allocation, RadixAttention attacks KV reuse across requests - the cache is a radix tree keyed by token id, and any request whose prefix was seen before walks it instead of re-prefilling. The closing rule: the radix dividend only exists if your traffic actually shares prefixes - read cache_hit_rate before crediting the engine.

## The Radix Prefill Ledger

Workload: one 512-token system prompt plus a 256-token few-shot block - a 768-token prefix every request carries - three users, three turns each, every turn adding a 48-token user message and generating a 200-token answer whose KV becomes cached context too. Without a cache every request re-prefills its whole context; with the radix tree only the delta past the longest cached prefix is computed:

| request | cold prefill (tok) | warm prefill (tok) |
|---|---:|---:|
| r01 / r04 / r07 (turn 1) | 816 | 48 |
| r02 / r05 / r08 (turn 2) | 1064 | 48 |
| r03 / r06 / r09 (turn 3) | 1312 | 48 |

Cold total **9576**, warm total **432**, saved **9144 tokens - 95%** of all prefill work eliminated by one shared prefix. Two rules the tree imposes: the cache is **exact** (a hit requires a true token-prefix match - no semantic similarity) and **evictable** (LRU, bounded by the same memory budget as everything else - a near-zero hit rate means you are paying tree bookkeeping for nothing).

## The KV Budget on an 11GB GPU

The knobs differ from vLLM's by name and behave the same in kind - `--mem-fraction-static` (not `gpu-memory-utilization`) fixes the weights + KV budget up front, and the KV/token cost is model geometry, not engine choice:

| budget line | value | note |
|---|---|---|
| KV per token (Qwen3-8B, fp16, GQA) | 144 KB | 2 (K+V) x 36 layers x 1024 kv-dim x 2 bytes |
| one 8192-token sequence | 1152 MB | ~= 1.2 GB |
| 0.85 x 11GB budget | 9.35 GB | weights ~6.1 GB + KV pool + activations/graphs |
| `--kv-cache-dtype fp8_e4m3` | 72 KB/token | halves the pool - a latency-quality tradeoff to measure |

## The One-Constraint Rule

Constrained decoding is a first-class sampling param with xgrammar as the default grammar backend (Outlines via `--grammar-backend`). The constraint triple is **exactly one** of `json_schema`, `regex`, `ebnf` per request - the server rejects a request carrying two with a 400, never a silent ignore:

| invalid pair | why it is rejected |
|---|---|
| json_schema + regex | two grammars cannot both own the mask |
| json_schema + ebnf | the same mask-owner conflict |
| regex + ebnf | the same mask-owner conflict |

Because the grammar is compiled and enforced per token, the output *cannot* violate the schema - no retry loop, no parse-and-pray. CHEAT-SHEET-013 owns the producer-side 2x2; this is the serving-side enforcement of the same contract.

## The TTFT Radix Dividend

First turn of a fresh chat in an agent fleet: shared prefix 768 tokens plus the 48-token user message. At a canonical 2000 tok/s prefill throughput:

| path | prefill tokens | TTFT |
|---|---:|---:|
| cold (tree miss) | 816 | 0.408 s |
| warm (tree hit) | 48 | 0.024 s |

**17x lower first-token latency** on the tree walk - and multi-turn follow-ups re-prefill only the new tokens, never the whole conversation.

## Reading sglang:cache_hit_rate

`--enable-metrics` serves Prometheus on the server port. `sglang:cache_hit_rate` is the metric vLLM has no answer to - the direct read on whether RadixAttention is paying for itself on your traffic:

| hit rate | zone | action |
|---|---|---|
| 3% | radix tree is pure overhead | random-ish traffic - disable the cache |
| 47% | mixed | long tails only; check the prompt distribution |
| 91% | agent fleet | the radix dividend is real - keep the cache on |

```text
sglang:num_running_reqs             gauge     executing now
sglang:num_queue_reqs               gauge     queued (KV or scheduler bound)
sglang:token_usage                  gauge     KV pool fill fraction
sglang:cache_hit_rate               gauge     THE RadixAttention metric
sglang:prompt_tokens_total          counter   rate() it for prefill tok/s
sglang:generation_tokens_total      counter   rate() it for gen tok/s
sglang:time_to_first_token_seconds  histogram prefix hits should crush this
sglang:e2e_request_latency_seconds  histogram p99 via histogram_quantile()
```

## The Speculation Bet

EAGLE speculation (`--speculative-algorithm EAGLE`, topk 1, 3 steps, 4 draft tokens) is a bet priced by acceptance rate. A draft ~4x smaller costs 0.25 target-steps per draft pass, so a step costs `1 + 0.25 x 3 = 1.75` target-steps, and the expected tokens per step is the geometric sum `1 + p + p^2 + p^3` (the first token always verifies):

| acceptance p | E[tokens/step] | speedup | verdict |
|---|---:|---:|---|
| 0.3 | 1.417 | 0.81x | SLOWER - disable on this distribution |
| 0.8 | 2.952 | 1.69x | FASTER - templated, code-heavy text |

Code-heavy or templated text accepts well; high-temperature creative text can end slower than the plain engine - measure acceptance before shipping the flags.

## Known Failure Modes

| failure | lesson |
|---|---|
| Install sglang into the training venv | the hard stack pins (torch 2.13.0, sglang-kernel, flashinfer) collide - fresh environment, do not fight the pins |
| Benchmark with shared prompts and the cache on | identical prompts become hits - you measure the generator's repetitiveness; random-input comparisons need `--disable-radix-cache` |
| Two constraint params in one request | the triple is exclusive - exactly one, else a 400 |
| Enable speculation on creative sampling | acceptance 0.3 lands 0.81x - slower than the plain engine |
| Reach for PD disaggregation first | it solves measured bottlenecks - saturate the radix cache and batching knobs before the role split |

## References

- Repository, *Module 1405: SGLang RadixAttention Serving - the reuse engine with runnable code*
- Zheng et al., 2023, *SGLang: Efficient Execution of Structured Language Model Programs* - RadixAttention
- SGLang documentation, *docs.sglang.io* - server arguments, offline engine API, frontend DSL, production metrics
- Repository, *Module 4202: Speculative Decoding* - the acceptance-rate theory behind the bet

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| `torch==2.13.0 is not installed` at install | stack pins collide with your venv | fresh environment - do not fight the pins |
| CUDA 12 driver, image exits immediately | `v0.5.21-cu130` needs CUDA 13 | `dev-cu12` (the frozen CUDA 12 line) or upgrade the driver |
| OOM at startup | mem-fraction-static too high for weights + graphs | drop to 0.8, smaller `--context-length`, check `nvidia-smi` |
| Latency rose after enabling speculation | low acceptance on your text distribution | measure acceptance; disable on creative sampling |
| Benchmark numbers impossibly good | radix cache hit on repeated prompts | `--disable-radix-cache` for random-input comparisons |
| PD setup hangs at bootstrap | prefill bootstrap port 8998 unreachable from decode | open the port; check transfer backend prerequisites |

## Quick Reference for

| target | role on this surface |
|---|---|
| [Module 1405: SGLang RadixAttention Serving](../../phases/phase1-infra/1400-llmops/1405-SGLang.md) | this sheet's source module - the full engine surface with runnable code |
| [Module 1402: vLLM and TGI High-Concurrency Inference](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) | the sibling default engine - PagedAttention allocation vs radix reuse |
| [Module 4202: Speculative Decoding](../../phases/phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md) | the acceptance-rate theory behind the speculation bet |
| [CHEAT-SHEET-018: Speculative Decoding](CHEAT-SHEET-018-Speculative-Decoding.md) | the single-page sibling of the speculation surface |

```python
"""CHEAT-SHEET-034 canonical numbers - stdlib only, deterministic."""

PREFILL_TPS = 2000  # canonical prefill throughput for the TTFT math

print("F1  Radix prefill ledger (3 users x 3 turns, one shared prefix)")
SYSTEM, FEW_SHOT, USER_MSG, GEN = 512, 256, 48, 200
BASE = SYSTEM + FEW_SHOT
cold_turns, warm_turns = [], []
for _ in range(3):                # users
    context = BASE
    for _ in range(3):            # turns within one conversation
        context += USER_MSG       # the new user message joins the context
        cold_turns.append(context)
        warm_turns.append(USER_MSG)
        context += GEN            # the answer becomes cached context too
cold, warm = sum(cold_turns), sum(warm_turns)
for i, (c, w) in enumerate(zip(cold_turns, warm_turns), 1):
    print(f"    r{i:02d}  cold prefill {c:4d} tok   warm prefill {w:3d} tok")
print(f"    cold total {cold}   warm total {warm}   saved {cold - warm}"
      f" ({100 * (cold - warm) / cold:.0f}%)")

print()
print("F2  KV-token cost and the 11GB budget (Qwen3-8B geometry)")
kv_bytes = 2 * 36 * 1024 * 2      # K+V x 36 layers x 1024 kv-dim x fp16
print(f"    KV per token: {kv_bytes} B = {kv_bytes / 1024:.0f} KB (fp16)")
seq8k_mb = kv_bytes * 8192 / 1024 / 1024
print(f"    one 8192-token sequence: {seq8k_mb:.0f} MB ~= 1.2 GB")
budget = 0.85 * 11
print(f"    --mem-fraction-static 0.85 x 11GB = {budget:.2f} GB budget")
print(f"    --kv-cache-dtype fp8_e4m3 halves it: {kv_bytes / 1024 / 2:.0f} KB/token,"
      f" {seq8k_mb / 2:.0f} MB per 8k sequence")

print()
print("F3  The one-constraint rule (json_schema / regex / ebnf)")
TRIPLE = ("json_schema", "regex", "ebnf")
pairs = [(a, b) for i, a in enumerate(TRIPLE) for b in TRIPLE[i + 1:]]
print(f"    constraint triple: {TRIPLE}")
print(f"    invalid two-at-once requests the server must 400: {len(pairs)} -> {pairs}")
print(f"    valid requests carry exactly {1} of the three")

print()
print("F4  The TTFT radix dividend (first turn of a fresh chat)")
miss_tok, hit_tok = BASE + USER_MSG, USER_MSG   # 816 vs 48 prefill tokens
t_cold = miss_tok / PREFILL_TPS
t_warm = hit_tok / PREFILL_TPS
print(f"    shared prefix {BASE} tok + user msg {USER_MSG} tok = {miss_tok} tok")
print(f"    cold TTFT: {miss_tok}/{PREFILL_TPS} = {t_cold:.3f} s")
print(f"    warm TTFT: {hit_tok}/{PREFILL_TPS} = {t_warm:.3f} s")
print(f"    radix dividend: {t_cold / t_warm:.0f}x lower first-token latency")

print()
print("F5  Reading sglang:cache_hit_rate (the metric vLLM lacks)")
for h in (3, 47, 91):
    if h < 5:
        zone = "radix tree is pure overhead - random-ish traffic, disable it"
    elif h < 50:
        zone = "mixed - long tails only; check the prompt distribution"
    else:
        zone = "agent fleet - the radix dividend is real, keep the cache on"
    print(f"    hit {h:2d}%  {zone}")

print()
print("F6  The speculation bet (EAGLE: topk 1, 3 steps, 4 draft tokens)")
draft_ratio = 0.25                # draft model ~4x smaller => 0.25 target-step cost
cost = 1 + draft_ratio * 3        # target pass + 3 draft passes per step
print(f"    step cost: 1 target pass + 3 draft passes = {cost:.2f} target-steps")
for p in (0.3, 0.8):
    expected = sum(p ** k for k in range(4))   # first token always verifies
    speedup = expected / cost
    verdict = "FASTER" if speedup > 1 else "SLOWER - disable on this distribution"
    print(f"    acceptance p={p:.1f}: E[tokens/step]={expected:.3f}"
          f"  speedup={speedup:.2f}x  {verdict}")

print("DETERMINISTIC-OK")
```

```text
F1  Radix prefill ledger (3 users x 3 turns, one shared prefix)
    r01  cold prefill  816 tok   warm prefill  48 tok
    r02  cold prefill 1064 tok   warm prefill  48 tok
    r03  cold prefill 1312 tok   warm prefill  48 tok
    r04  cold prefill  816 tok   warm prefill  48 tok
    r05  cold prefill 1064 tok   warm prefill  48 tok
    r06  cold prefill 1312 tok   warm prefill  48 tok
    r07  cold prefill  816 tok   warm prefill  48 tok
    r08  cold prefill 1064 tok   warm prefill  48 tok
    r09  cold prefill 1312 tok   warm prefill  48 tok
    cold total 9576   warm total 432   saved 9144 (95%)

F2  KV-token cost and the 11GB budget (Qwen3-8B geometry)
    KV per token: 147456 B = 144 KB (fp16)
    one 8192-token sequence: 1152 MB ~= 1.2 GB
    --mem-fraction-static 0.85 x 11GB = 9.35 GB budget
    --kv-cache-dtype fp8_e4m3 halves it: 72 KB/token, 576 MB per 8k sequence

F3  The one-constraint rule (json_schema / regex / ebnf)
    constraint triple: ('json_schema', 'regex', 'ebnf')
    invalid two-at-once requests the server must 400: 3 -> [('json_schema', 'regex'), ('json_schema', 'ebnf'), ('regex', 'ebnf')]
    valid requests carry exactly 1 of the three

F4  The TTFT radix dividend (first turn of a fresh chat)
    shared prefix 768 tok + user msg 48 tok = 816 tok
    cold TTFT: 816/2000 = 0.408 s
    warm TTFT: 48/2000 = 0.024 s
    radix dividend: 17x lower first-token latency

F5  Reading sglang:cache_hit_rate (the metric vLLM lacks)
    hit  3%  radix tree is pure overhead - random-ish traffic, disable it
    hit 47%  mixed - long tails only; check the prompt distribution
    hit 91%  agent fleet - the radix dividend is real, keep the cache on

F6  The speculation bet (EAGLE: topk 1, 3 steps, 4 draft tokens)
    step cost: 1 target pass + 3 draft passes = 1.75 target-steps
    acceptance p=0.3: E[tokens/step]=1.417  speedup=0.81x  SLOWER - disable on this distribution
    acceptance p=0.8: E[tokens/step]=2.952  speedup=1.69x  FASTER
DETERMINISTIC-OK
```
