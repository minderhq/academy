---
Document ID: 4204
Title: "4204: KV-Cache Paging and Prefix Caching"
Phase: 4
Module: 4200
Last Updated: 2026-10-07
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['quantization', 'kv-cache', 'inference', 'vllm']
---

# 4204: KV-Cache Paging and Prefix Caching

## Abstract

The KV cache does not just grow - it is allocated, mapped, shared, and scheduled, and until now none of that machinery was taught. The 4200 quiz asks what PagedAttention is for (Q5) and how GQA and MQA shrink the cache (Q6, Q11-12), and its review map leans Q5 on the vLLM engine lesson, whose PagedAttention section is an ASCII analogy, and Q6/11-12 on the optimization guide's survey table - the mechanism itself appears nowhere: the phrase "block table" is absent from the entire corpus, copy-on-write exists only as a Kubernetes storage concept, and the module README's own checklist says "use PagedAttention" and "add prefix caching" as if flipping a switch were the whole skill. The boundary is owned honestly: [4201](./4201-Context-Window-Physics.md) owns the per-token physics - the memory formula this lesson's ledger instantiates, quantization, and OOM prevention - [4202](./4202-Speculative-Decoding.md) owns speculative decoding, the [4203 guide](./guides/4203-Context-Window-Optimization.md) owns the per-model memory survey at batch 1 that this lesson's batch-32 ledger extends, [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) owns the engine surface - deployment, configuration knobs, and the paging analogy - [2302](../../phase2-foundations/2300-framework-engineering/2302-Model-Serving-Architectures.md) owns batch formation by slots inside one server, [3402](../../phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md) owns GQA as architecture, and 4204 owns the page manager itself: the fragmentation bill, the block table, the KV-head sharing ledger, prefix caching with copy-on-write, and the token-budget scheduler.

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Fragmentation Bill: Contiguous versus Paged](#the-fragmentation-bill-contiguous-versus-paged)
- [The Block Table](#the-block-table)
- [The KV-Head Sharing Ledger: MHA, GQA, MQA](#the-kv-head-sharing-ledger-mha-gqa-mqa)
- [Prefix Caching and Copy-on-Write](#prefix-caching-and-copy-on-write)
- [The Token Budget: Continuous Batching and Chunked Prefill](#the-token-budget-continuous-batching-and-chunked-prefill)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After this lesson you will be able to:

- Price what contiguous KV reservation costs against paged allocation on a real concurrent workload, and say why the savings are memory and not accuracy
- Walk a block table - logical blocks mapped onto scattered physical blocks through a free list - and explain why external fragmentation is zero
- Read a model config's layer, head, and KV-head counts into a per-token cache number, and turn that number into a fits-or-OOM verdict at a given context and batch
- Account for prefix-cache reuse and copy-on-write sharing on a workload of prompts that share a system prompt, and know the reuse is prefill-phase-only
- Schedule one engine iteration under a token budget, and show what chunked prefill buys decode latency

## The Fragmentation Bill: Contiguous versus Paged

Before PagedAttention, serving systems reserved KV memory the way C `malloc` reserved arenas: one contiguous slab per request, sized for the worst case the request might reach. The vLLM team measured the cost of that habit - existing systems "waste 60% - 80% of memory due to fragmentation and over-reservation", while PagedAttention leaves "a mere waste of under 4%". The mechanism behind those numbers is a page table for attention, and the first fence prices it on eight concurrent sequences whose actual lengths the server cannot know in advance:

```python
import math

# Eight concurrent sequences on one engine (prompt + expected generation).
LENGTHS = [512, 1337, 4096, 89, 2048, 777, 1533, 2904]
MAX_LEN = 4096   # engine max_model_len: contiguous systems reserve this per slot
BLOCK = 16       # tokens per physical block (vLLM default block size)

actual = sum(LENGTHS)
contig = len(LENGTHS) * MAX_LEN
paged = sum(math.ceil(n / BLOCK) for n in LENGTHS) * BLOCK

print(f"actual KV tokens required : {actual:,}")
print(f"contiguous reservation    : {contig:,} tokens ({len(LENGTHS)} slots x {MAX_LEN})")
print(f"  utilization {actual/contig:.1%}   waste {1 - actual/contig:.1%}")
print(f"paged reservation         : {paged:,} tokens ({BLOCK}-token blocks)")
print(f"  utilization {actual/paged:.1%}   waste {1 - actual/paged:.1%}")
print(f"reservation ratio         : {contig/paged:.2f}x more memory held for the same bytes")
worst = min(LENGTHS)
print(f"worst single slot         : the {worst}-token sequence holds {worst/MAX_LEN:.1%} of its slot")
```

The contiguous system holds 32,768 tokens for 13,296 tokens of actual work - 40.6 percent utilization, 59.4 percent waste, right at the bottom of the blog's 60-80 percent band - and its worst single slot is absurd: the 89-token sequence squats 2.2 percent of a 4,096-token slab. The paged system holds 13,328 tokens, 2.46x less reservation for the identical bytes, with 99.8 percent utilization and 0.2 percent waste - under the blog's 4 percent ceiling. Nothing about the model changed, no weights moved, no accuracy shifted: the win is purely that memory is no longer reserved for requests that were never served.

## The Block Table

Paging only pays if the blocks can live anywhere, and the data structure that lets them is the block table - "the contiguous logical blocks of a sequence are mapped to non-contiguous physical blocks via a block table", with "physical blocks allocated on demand". The blog's analogy is exact: "one can think of blocks as pages, tokens as bytes, and sequences as processes". The fence runs one: a four-token block size for display, a free list whose pop order scatters physical IDs, and two sequences growing through block boundaries:

```python
# A KV page manager: fixed-size blocks, a free list, one block table per sequence.
BLOCK = 4                              # small for display (vLLM ships 16)
free_list = [10, 3, 7, 1, 9, 4]        # physical pool in allocation order
tables = {"A": [], "B": []}            # seq -> logical-ordered physical ids
lens = {"A": 0, "B": 0}

def append(seq, n):
    for _ in range(n):
        if lens[seq] % BLOCK == 0:                 # crossed a block boundary
            tables[seq].append(free_list.pop(0))   # allocate next physical block
        lens[seq] += 1

append("A", 9)
append("B", 5)
print("after A:9, B:5")
print(f"  A table (logical -> physical): {tables['A']}")
print(f"  B table (logical -> physical): {tables['B']}")
print(f"  free list remaining          : {free_list}")
print("A appends 4 more tokens -> the 13th crosses into a 4th physical block")
append("A", 4)
print(f"  A table: {tables['A']}  ({lens['A']} tokens in {len(tables['A'])} blocks)")
print(f"  its last block holds {lens['A'] % BLOCK} of {BLOCK} token slots")
print(f"  free list now: {free_list} (pool drained)")
owner = {}
for seq, tbl in tables.items():
    for logical, phys in enumerate(tbl):
        owner[phys] = f"{seq}[{logical}]"
for phys in sorted(owner):
    print(f"  physical {phys:>2} <- {owner[phys]}")
print("A's tokens are contiguous LOGICALLY, scattered PHYSICALLY (10,3,7,4)")
print("external fragmentation: zero - every freed block fits any sequence")
```

Sequence A's nine tokens map to physical blocks 10, 3, 7 - contiguous logically, scattered physically - and B's five land on 1 and 9, interleaved with A's. When A's 13th token crosses a boundary, the manager pops block 4 from the free list; the pool is now drained and the table reads [10, 3, 7, 4] with the last block holding 1 of 4 slots. The point of the exercise is the absence of a constraint: nothing required A's blocks to sit next to each other or anywhere in particular, so a freed block is reusable by any sequence the instant it returns to the free list. That is what "external fragmentation: zero" means operationally - fragmentation inside the last partial block is bounded by one block per sequence (16 tokens in production), and nothing else ever strands.

## The KV-Head Sharing Ledger: MHA, GQA, MQA

Paging changes where the cache lives; the KV-head count changes how much cache exists at all. The per-token formula [4201](./4201-Context-Window-Physics.md) owns - two tensors (K and V), times layers, times KV heads, times head dimension, times bytes per element - is linear in KV heads, and the architecture lessons teach grouped-query attention as a modeling choice; this lesson reads its serving bill. The configs are real: Llama-2-7B runs multi-head attention with 32 KV heads, Llama-3-8B's paper specifies "grouped query attention (GQA) with 8 key-value heads" (Table 3: 32 layers, 32 query heads, model dimension 4,096, so head dimension 128), and Falcon-7B's config ships `"multi_query": true` - one KV head across 71 query heads, head dimension 4,544/71 = 64:

```python
CONTEXT = 8192
BATCH = 32
FP16 = 2   # bytes per element

CONFIGS = [
    # (name, layers, kv_heads, head_dim, note)
    ("Llama-2-7B   MHA", 32, 32, 128, "32 query heads, 32 KV heads"),
    ("Llama-3-8B   GQA-8", 32, 8, 128, "GQA with 8 key-value heads (paper Table 3)"),
    ("GQA-4 (same geometry)", 32, 4, 128, "hypothetical midpoint"),
    ("Falcon-7B    MQA", 32, 1, 64, "multi_query: true; head_dim 4544/71 = 64"),
]
H100 = 80 * 2**30

print(f"{'config':<24}{'per token':>12}{'@8k x batch 32':>16}  verdict")
for name, layers, kv, hd, note in CONFIGS:
    per = 2 * layers * kv * hd * FP16          # K and V, bytes per token
    total = per * CONTEXT * BATCH
    verdict = "fits H100 80GB" if total <= H100 else "OOM on H100 80GB"
    print(f"{name:<24}{per/1024:>10.0f}KB{total/2**30:>13.1f}GB  {verdict}")
print()
b1_4k = 2 * 32 * 32 * 128 * FP16 * 4096
print(f"cross-check, Llama-2-7B @4k batch 1: {b1_4k/2**30:.2f} GB (4201's own number)")
print(f"MHA -> GQA-8: the cache shrinks {32//8}x; GQA-8 -> MQA: another {8//1}x more")
```

The ledger at batch 32 and 8k context: the MHA model needs 512 KB per token - 128.0 GB of cache, an OOM on an 80 GB H100 before a single activation is counted - while the GQA-8 model needs 128 KB per token and 32.0 GB, a fit, for the 4x reduction; the hypothetical GQA-4 lands at 64 KB and 16.0 GB; the MQA Falcon geometry needs 8 KB per token and 2.0 GB, another 8x below GQA-8. The cross-check is the audit trail: the same formula at batch 1 and 4k prints 2.00 GB - [4201](./4201-Context-Window-Physics.md) teaches exactly that number, and the guide's survey table extends it per model. The verdict column is why GQA ate the industry: it is the difference between a serving fleet that needs 4x the accelerators for the same batch and one that does not, purchased at the price of a modest quality trade the GQA paper (Ainslie et al.) shows how to buy back by uptraining from an MHA checkpoint.

## Prefix Caching and Copy-on-Write

The block table enables one more thing a contiguous allocator cannot do: two sequences mapping logical blocks to the same physical block. vLLM's docs describe the workload form - "a new query can directly reuse the KV cache if it shares the same prefix with one of the existing queries", letting it "skip the computation of the shared part" - and are precise about the scope: automatic prefix caching "only reduces the time of processing the queries (the prefilling phase)". Decode is untouched; what is saved is recomputing the same prompt tokens a thousand times:

```python
BLOCK = 16
SYS_PROMPT = 1280                       # shared system prompt
N_REQ = 500
suffixes = [200 + (i * 97) % 801 for i in range(N_REQ)]   # 200..1000, deterministic

sys_blocks = SYS_PROMPT // BLOCK
no_cache = sum(SYS_PROMPT + s for s in suffixes)
with_cache = SYS_PROMPT + sum(suffixes)  # shared prefix computed once
saved = no_cache - with_cache
print(f"shared system prompt      : {SYS_PROMPT} tokens = {sys_blocks} blocks of {BLOCK}")
print(f"{N_REQ} requests, suffix lengths {min(suffixes)}-{max(suffixes)} tokens")
print(f"prefill without cache     : {no_cache:,} tokens")
print(f"prefill with prefix cache : {with_cache:,} tokens (prefix once + suffixes)")
print(f"recompute avoided         : {saved:,} tokens ({saved/no_cache:.1%} of all prefill)")
print()
cow_copy = BLOCK          # only the divergent block is copied at the fork
deep_copy = SYS_PROMPT
print(f"copy-on-write at the fork : {cow_copy} tokens copied vs {deep_copy} without sharing")
print(f"that is {cow_copy/deep_copy:.1%} of the prefix; the other {sys_blocks - 1} blocks stay shared (refcount 2)")
```

Five hundred requests carrying the same 1,280-token system prompt - 80 blocks - prefill 939,492 tokens without a cache and 300,772 with it: 638,720 tokens of recomputation avoided, 68.0 percent of the entire prefill bill, for prompts whose suffixes run 200-999 tokens. The sharing has a hazard, and the page manager answers it with refcounts: when two beams fork at the end of a shared prefix, "PagedAttention keeps track of the reference counts of the physical blocks and implements the Copy-on-Write mechanism" - only the block that receives the divergent token is copied, 16 tokens against the 1,280-token prefix (1.2 percent of it), while the other 79 blocks stay shared at refcount 2. The blog prices the whole family of tricks: memory sharing cuts "the memory overhead of complex sampling algorithms, such as parallel sampling and beam search... by up to 55%", worth "up to 2.2x improvement in throughput" - which is why beam search on a paged engine is a config flag and on a contiguous one is a memory incident.

## The Token Budget: Continuous Batching and Chunked Prefill

The page manager's last job is scheduling. Static batching admits a fixed set of requests and waits for the slowest; Orca (OSDI '22) introduced iteration-level scheduling - "the batch size is determined per iteration" - and the Anyscale writeup measured what that buys: "8x throughput over naive batching by using continuous batching" on their stack, and "up to 23x" with continuous batching plus its memory optimizations on vLLM, benchmarked on OPT-13B, 1,000 requests, 512-token inputs. Continuous batching decides admission per iteration; the iteration itself needs a budget, because one 2,048-token prefill admitted whole would freeze every decode behind it. Chunked prefill splits the long prompt across iterations under the same token cap:

```python
BUDGET = 512          # max_num_batched_tokens per engine iteration
DECODES = 8           # sequences decoding 1 token per iteration
PREFILL = 2048        # one long prompt arrives

chunk = BUDGET - DECODES
iters = (PREFILL + chunk - 1) // chunk
print(f"engine token budget : {BUDGET}/iteration, {DECODES} decodes in flight")
print(f"long prompt         : {PREFILL} tokens -> chunked at {chunk}/iteration ({iters} iterations)")
left = PREFILL
for it in range(1, iters + 1):
    p = min(chunk, left)
    left -= p
    print(f"  iter {it}: prefill {p:>4} + decode {DECODES} = {p + DECODES} tokens")
print(f"max decode inter-token latency: unchunked {PREFILL} compute-units vs chunked {chunk + DECODES}")
print(f"ITL spike reduction: {PREFILL/(chunk + DECODES):.1f}x")
print("decode-stall iterations: unchunked 1 (the whole prefill) vs chunked 0 (never over budget)")
```

With 8 decodes in flight and a 512-token budget, the long prompt enters as five chunks - 504 prefill tokens plus 8 decode tokens per iteration for four iterations, then a 32-and-8 tail - and the worst inter-token latency any decode suffers is one 512-token iteration instead of one 2,048-token stall: a 4.0x ITL spike reduction, with decode-stall iterations going from 1 to 0. [2302](../../phase2-foundations/2300-framework-engineering/2302-Model-Serving-Architectures.md) owns the slot-level batch formation this scheduler sits inside, [1402](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) owns the engine flags that set the budget in production, and 6505 owns what happens when these per-server decisions are aggregated into fleet policy. The three fences together are one system: paging makes the memory tight, the block table makes it shareable, and the token budget makes the sharer fair.

## Summary

- Contiguous reservation held 32,768 tokens for 13,296 of work - 40.6 percent utilization, 59.4 percent waste; paged allocation held 13,328, 2.46x less, at 99.8 percent - the memory bill PagedAttention was invented to delete, with no change to the model.
- The block table maps contiguous logical blocks onto scattered physical blocks (A's tokens on 10, 3, 7, 4); allocation is on demand at block boundaries, internal waste is capped at one partial block per sequence, and external fragmentation is zero because every freed block fits any sequence.
- The KV-head ledger prices attention architecture in cache bytes: Llama-2-7B MHA 512 KB/token - 128.0 GB at 8k x batch 32, OOM on an H100 - against Llama-3-8B GQA-8 at 128 KB and 32.0 GB (4x) and Falcon-7B MQA at 8 KB and 2.0 GB; the same formula at batch 1 and 4k reproduces 4201's 2.00 GB.
- Prefix caching skipped 638,720 of 939,492 prefill tokens (68.0 percent) on 500 system-prompt-sharing requests - prefill phase only - and copy-on-write copied 16 tokens at the beam fork instead of 1,280 (1.2 percent), the mechanism behind the blog's 55 percent memory cut and 2.2x throughput for complex sampling.
- Chunked prefill under a 512-token budget turns one 2,048-token decode stall into five 504-token chunks - a 4.0x inter-token-latency spike reduction, zero budget-violating iterations - the scheduling half of the same page manager.

## References

- [Efficient Memory Management for Large Language Model Serving with PagedAttention (Kwon et al., SOSP 2023)](https://arxiv.org/abs/2309.06180) - the paper behind the block table, the reference counts, and the under-4-percent waste claim
- [vLLM blog: PagedAttention](https://blog.vllm.ai/2023/06/20/vllm.html) - the 60-80 percent fragmentation measurement, the blocks-as-pages analogy, and the 55 percent / 2.2x sharing numbers quoted above
- [GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints (Ainslie et al., 2023)](https://arxiv.org/abs/2305.13245) - grouped-query attention and the uptraining recipe from MHA checkpoints
- [Fast Transformer Decoding: One Write-Head is All You Need (Shazeer, 2019)](https://arxiv.org/abs/1911.02150) - multi-query attention, the one-KV-head floor of the ledger
- [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783) - Table 3: 32 layers, 32 heads, 8 KV heads, model dimension 4,096; "grouped query attention (GQA) with 8 key-value heads"
- [Falcon 7B config](https://huggingface.co/tiiuae/falcon-7b/blob/main/config.json) - `"multi_query": true`, 71 attention heads, 32 layers, hidden size 4,544
- [Anyscale: Continuous batching](https://www.anyscale.com/blog/continuous-batching-llm-inference) - the static-batching framing and the 8x / 23x throughput measurements on OPT-13B
- [vLLM: Automatic Prefix Caching](https://docs.vllm.ai/en/latest/features/automatic_prefix_caching.html) - prefix reuse and its prefill-phase-only scope

## Next Steps

- [4201: Context Window Physics and OOM Prevention](./4201-Context-Window-Physics.md) - the per-token formula and the OOM budget this lesson's ledger instantiates
- [4203: Context Window Optimization Guide](./guides/4203-Context-Window-Optimization.md) - the implementation cookbook: quantization, sliding windows, and context chunking
- [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) - the engine that ships this page manager, and the flags that configure it

**Estimated Time:** 4 hours
