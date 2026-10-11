---
Document ID: CHEAT-SHEET-017
Title: "CHEAT-SHEET-017: KV Cache"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'kv-cache', 'vllm', 'inference']
---

# CHEAT-SHEET-017: KV Cache

## Quick Reference for KV Cache

**Version:** 1.0

Long-context serving is one formula plus four disciplines: the
per-token memory arithmetic, the budget that turns it into an
OOM verdict, the paging and sharing machinery that squeezes the
waste out, and the scheduler that keeps decodes fair. This sheet
maps the formula, the head ledger, the block table, and the
prefix-caching rules — the whole KV surface on one page.

---

## The Per-Token Formula

Every cached token costs `2 × layers × kv_heads × head_dim × bytes`
bytes — the 2 is K and V. Multiply by sequence length and batch and
the cache grows LINEARLY in both; it, not the weights, is what OOMs
a long-context run. Batch-size-1 bills at fp16: Llama-2-7B
(32 layers, 32 KV heads, head_dim 128) carries 2.00 GB at 4k
context and doubles per context doubling; Phi-2 lands at 1.25 GB
(head_dim 80); Mixtral-8x7B at 0.50 GB because GQA gives it 8 KV
heads, not 32.

```python
H100 = 80 * 2**30

def kv_bytes_per_token(layers, kv_heads, head_dim, bytes_per=2):
    return 2 * layers * kv_heads * head_dim * bytes_per

CONFIGS = [
    ("Llama-2-7B   MHA", 32, 32, 128),
    ("Llama-3-8B   GQA-8", 32, 8, 128),
    ("Falcon-7B    MQA", 32, 1, 64),
]
for name, L, H, D in CONFIGS:
    per = kv_bytes_per_token(L, H, D)
    total = per * 8192 * 32
    verdict = "fits H100" if total <= H100 else "OOM on H100"
    print("%s: %d KB/token -> %.1f GB @8k x batch 32 (%s)"
          % (name, per / 1024, total / 2**30, verdict))

b1 = kv_bytes_per_token(32, 32, 128) * 4096
print("cross-check, batch 1 @4k: %.2f GB (the 4201 number)" % (b1 / 2**30))

kv4k = b1 / 2**30
print("fp16 budget: %.0f GB (14 w + %.2f kv + 1 act) vs 11 GB GPU -> OOM"
      % (14 + kv4k + 1, kv4k))
print("int8 cache: %.0f GB | 4-bit cache: %.1f GB -> fit"
      % (7 + kv4k / 2 + 1, 3.5 + kv4k / 4 + 1))
```

---

## The OOM Budget

Weights + KV + activations is the whole verdict. Llama-2-7B at 4k:
14 + 2 + 1 = 17 GB — past an 11 GB GPU before a single request
arrives. Two INDEPENDENT knobs attack it: weights via
`BitsAndBytesConfig` at load time, the cache via
`cache_implementation="quantized"` with
`cache_config={"nbits": 8, "backend": "hqq"}` (int8) or
`{"nbits": 4, "backend": "quanto"}` (4-bit — the hqq cache stops at
int8). There is NO model-load flag for a quantized cache; it is a
per-generate() setting. The same run: int8 everywhere is 9 GB, 4-bit
weights + 4-bit cache is 5 GB. Latency trade-off: a quantized cache
adds dequantize work EVERY step — with a short context and free
VRAM, fp16 is faster. Reach for it when context length, not compute,
pushes you into OOM.

---

## The Head Ledger: MHA, GQA, MQA

The formula is linear in KV heads, so the architecture choice prices
the serving fleet. Real configs: Llama-2-7B runs MHA with 32 KV
heads; Llama-3-8B ships GQA with 8 key-value heads (paper Table 3:
32 layers, 32 query heads, dim 4096); Falcon-7B's config sets
`"multi_query": true` — one KV head across 71 query heads,
head_dim 4544/71 = 64. At 8k context and batch 32 the fence's ledger
prices them; the fence's cross-check at batch 1 and 4k reproduces
4201's 2.00 GB exactly. GQA's quality cost is bought back by
uptraining from the MHA checkpoint (Ainslie et al.) — which is why
GQA ate the industry.

| Knob | Cache bill | The cost |
| --- | --- | --- |
| GQA-8 | 4x smaller than MHA | modest, uptrain-recoverable |
| MQA (1 KV head) | another 8x below GQA-8 | the quality floor |
| int8 KV cache | 50% off | dequantize work per step |
| 4-bit KV cache | 75% off | some quality loss |

Sliding-window caches cut differently: constant
`window_size × dim × layers × 2` regardless of total length —
beyond-window tokens are GONE from attention, a reach-for-memory
trade. Chunked attention caps peak at O(chunk²) instead of
O(seq²). Context extension multiplies the bill: interpolating RoPE
from 2048 to 8192 grows the KV cache 4x.

---

## Paging and Sharing

Before PagedAttention, servers reserved ONE contiguous KV slab per
request sized for the worst case it might reach. The vLLM team
measured the habit: 60-80% of memory wasted to fragmentation and
over-reservation, versus under 4% paged. On eight concurrent
sequences totalling 13,296 tokens, a contiguous allocator holds
32,768 (40.6% utilization, 59.4% waste) while the paged allocator
holds 13,328 in 16-token blocks (99.8% / 0.2%) — 2.46x less
reservation for identical bytes, with NOTHING about the model
changed. The block table maps contiguous LOGICAL blocks onto
scattered PHYSICAL blocks through a free list; a freed block fits
any sequence instantly, so external fragmentation is zero and
internal waste is capped at one partial block per sequence.

Sharing is what the block table buys. Prefix caching lets requests
sharing a system prompt skip its prefill entirely: 500 requests on
a 1,280-token prompt prefill 939,492 tokens without it and 300,772
with it — 68.0% of the prefill bill deleted — and the scope is
PREFILL-PHASE-ONLY: decode never gets faster. At the fork,
copy-on-write copies only the divergent block — 16 tokens against
the 1,280-token prefix (1.2%) — while refcounts keep the other 79
blocks shared; that mechanism is worth up to 55% memory cut and
2.2x throughput for beam search and parallel sampling.

---

## The Token Budget

Paging makes memory tight; the token budget makes it fair. Orca
(OSDI '22) introduced iteration-level scheduling — the batch is
decided PER ITERATION — worth 8x over naive batching, up to 23x on
vLLM with its memory optimizations. One 2,048-token prefill admitted
whole freezes every decode behind it; chunked prefill splits it
under the engine's `max_num_batched_tokens` cap: at a 512 budget
with 8 decodes in flight, the prompt enters as five chunks of
504 prefill + 8 decode tokens, and the worst inter-token latency
drops from one 2,048-token stall to one 512-token iteration — a 4.0x
ITL spike reduction, with zero budget-violating iterations.

---

## Troubleshooting

| Symptom | Root cause | Fix |
| --- | --- | --- |
| OOM at long context despite 4-bit weights | the cache, not the weights, is what grows with seq x batch | quantize the cache and/or cut max_model_len |
| nbits=4 rejected with the hqq backend | hqq cache values stop at int8 | switch the backend to "quanto" |
| Quantized cache SLOWER than fp16 | dequantize work on every step at short context | keep the fp16 cache while VRAM is free |
| 80 GB card OOMs at 8k batch 32 on a 7B | 512 KB/token MHA cache = 128 GB; heads, not params | fewer KV heads: GQA/MQA architecture |
| Prefix cache "hit" but tokens/s unchanged | prefix reuse is prefill-phase-only | measure TTFT, not inter-token latency |
| Beam search exhausts memory | per-sequence slabs cannot share | paged engine with copy-on-write refcounts |

---

**Quick Reference for:**

- [Module 4201: Context Window Physics and OOM Prevention](../../phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
- [Module 4204: KV-Cache Paging and Prefix Caching](../../phases/phase4-quantization/4200-kv-cache/4204-KV-Cache-Paging-and-Prefix-Caching.md)
- [Guide 4203: Context Window Optimization](../../phases/phase4-quantization/4200-kv-cache/guides/4203-Context-Window-Optimization.md)
- [CHEAT-SHEET-007: vLLM Serving](./CHEAT-SHEET-007-vLLM-Serving.md)
