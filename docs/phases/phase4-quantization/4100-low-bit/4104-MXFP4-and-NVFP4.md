---
Document ID: 4104
Title: "4104: MXFP4 and NVFP4 - Microscaling Formats as Working Code"
Phase: 4
Module: 4100
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Tags: ['quantization', 'mxfp4', 'nvfp4', 'compression']
---

# 4104: MXFP4 and NVFP4 - Microscaling Formats as Working Code

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Microscaling: The Idea Both Formats Share](#microscaling-the-idea-both-formats-share)
- [e2m1: The Element Grid](#e2m1-the-element-grid)
- [MXFP4: e8m0 Scales and the Pow2 Tax](#mxfp4-e8m0-scales-and-the-pow2-tax)
- [NVFP4: Finer Blocks, e4m3 Scales, a Second Level](#nvfp4-finer-blocks-e4m3-scales-a-second-level)
- [Containment: What One Outlier Can Do](#containment-what-one-outlier-can-do)
- [The Production Surface: gpt-oss Selective MXFP4](#the-production-surface-gpt-oss-selective-mxfp4)
- [torchao: The Research and Training Surface](#torchao-the-research-and-training-surface)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After reading this lesson, you will be able to:

- Explain the microscaling recipe both formats share: tiny quantized scales recomputed per block of 4-bit elements
- Read the e2m1 element grid `{0, 0.5, 1, 1.5, 2, 3, 4, 6}` and emulate its round-to-nearest in plain `torch`
- Contrast MXFP4's power-of-2 `e8m0` scale per 32 elements against NVFP4's `e4m3` scale per 16 plus an fp32 per-tensor second level
- Measure the pow2 tax and the containment property that separates the two formats on real tensors
- Decode the gpt-oss-20b `quantization_config` and compute its 38.9 GB to 12.8 GB memory ledger
- Drive `transformers`' `Mxfp4Config` and `torchao`'s `MXTensor` as the two surfaces where MXFP4 actually runs

**Estimated Time:** 4 hours (1 hour reading, 3 hours hands-on with the fences)

## Abstract

[4101](./4101-GGUF-Physics.md) taught the block-quantization idea with GGUF's integer grids; [4102](./4102-EXL2-and-AWQ.md) taught calibration-driven 4-bit; [4103](./4103-Double-Quantization.md) taught nesting quantization inside itself. This lesson is the hardware-native generation of 4-bit: **MXFP4**, the OCP Microscaling spec's format, and **NVFP4**, NVIDIA's finer-grained variant. They differ from GGUF in kind, not degree - their element and scale types are real IEEE-style dtypes (`torch.float4_e2m1fn_x2`, `torch.float8_e8m0fnu`) that tensor cores multiply natively, so the quantized tensor is the working tensor, not a file format to be dequantized at load. OpenAI's gpt-oss models ship in MXFP4 and NVIDIA's Blackwell tensor cores execute NVFP4; you will quantize with both scale rules in plain `torch`, measure why the differences exist, and finish at the two production surfaces - `transformers` for the shipped checkpoints, `torchao` for research and training.

## Microscaling: The Idea Both Formats Share

Both formats split each weight into two parts with independent dtypes:

```text
        element                    scale
MXFP4   e2m1  (4-bit FP)           e8m0  (power-of-2 FP8)     one per 32 elements
NVFP4   e2m1  (4-bit FP)           e4m3  (standard FP8)       one per 16 elements
                                   + one fp32 per-tensor scale (second level)

dequantized = element * scale        (MXFP4)
dequantized = element * scale * tensor_scale   (NVFP4)
```

The move that makes 4 bits work: never let one value's range govern the whole tensor. A per-block scale absorbs each block's magnitude first, then the 4-bit grid only has to cover `[-6, 6]` in relative terms. This is the same idea [4101](./4101-GGUF-Physics.md) built with `Q4_0`'s integer grid and fp16 block scale - but the ingredients changed from file-format conventions to real float types:

| Ingredient | GGUF `Q4_0` (4101) | MXFP4 | NVFP4 |
|------------|--------------------|-------|-------|
| element grid | 16 linear ints `-8..7` | e2m1: nonlinear FP grid | e2m1: nonlinear FP grid |
| block size | 32 | 32 | 16 |
| scale dtype | fp16 (any value) | e8m0 (powers of 2 only) | e4m3 (full FP8 grid) |
| second level | none | none | fp32 per-tensor |
| runs natively on | CPU via llama.cpp | Blackwell/gpt-oss stack | Blackwell tensor cores |

The linear grid encodes `code * scale`; e2m1 encodes an actual floating-point number with a sign, exponent, and mantissa. That is what lets the hardware's multiply path consume the 4-bit values directly.

## e2m1: The Element Grid

e2m1 means 1 sign bit, 2 exponent bits, 1 mantissa bit - four magnitudes times two sub-normal-style rungs, one sign:

```text
magnitude grid:  0.0  0.5  1.0  1.5  2.0  3.0  4.0  6.0     (x sign)
relative gaps:        50%  33%  33%  33%  50%  33%  50%
```

Round-to-nearest on this grid is ten lines of `torch`, which is also exactly what the hardware kernel does:

```python
import torch


def e2m1_qdq(x):
    grid = torch.tensor([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0])
    sign, mag = x.sign(), x.abs()
    idx = (mag.unsqueeze(-1) - grid).abs().argmin(-1)
    return sign * grid[idx]


torch.manual_seed(0)
x = torch.randn(8) * 2
print(list(zip(x.tolist(), e2m1_qdq(x).tolist())))
```

Two honest notes before the fences. First, `torch.float4_e2m1fn_x2` exists in torch 2.12 as a dtype object, but casting a CPU tensor to it raises `NotImplementedError: copy_kernel` - the storage type is real, the CPU cast path is not (the same honest-boundary pattern as 3103's Inductor-on-MSVC gap). The fences therefore emulate the element step with the grid above and use the *real* dtypes for everything they can - the scales. Second, the grid's largest step, `4 -> 6`, is a 50% relative jump: anything a block quantizes near 6 pays the grid's worst relative error, which is why the scale rule that follows rounds **up**.

## MXFP4: e8m0 Scales and the Pow2 Tax

The OCP MX spec's scale rule: take the block's `amax/6`, round **up** to the next power of 2, store as e8m0. Powers of 2 survive any float round-trip exactly, so the fence can prove its scale arithmetic with the real dtype:

```python
import torch


def e2m1_qdq(x):
    grid = torch.tensor([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0])
    sign, mag = x.sign(), x.abs()
    idx = (mag.unsqueeze(-1) - grid).abs().argmin(-1)
    return sign * grid[idx]


torch.manual_seed(0)
W = torch.randn(64, 64)

b32 = W.reshape(-1, 32)
amax32 = b32.abs().amax(dim=1, keepdim=True).clamp_min(1e-12)
scale_m = torch.pow(2.0, torch.ceil(torch.log2(amax32 / 6.0)))
scale_m = scale_m.to(torch.float8_e8m0fnu).to(torch.float32)  # the real MX scale dtype
assert torch.equal(scale_m, torch.pow(2.0, torch.ceil(torch.log2(amax32 / 6.0))))
Qm = e2m1_qdq(b32 / scale_m) * scale_m
err_m = (W - Qm.view_as(W)).norm() / W.norm()

b16 = W.reshape(-1, 16)
amax16 = b16.abs().amax(dim=1, keepdim=True).clamp_min(1e-12)
scale_n = (amax16 / 6.0).to(torch.float8_e4m3fn).to(torch.float32).clamp_min(1e-12)
Qn = e2m1_qdq(b16 / scale_n) * scale_n
err_n = (W - Qn.view_as(W)).norm() / W.norm()

print(f"MXFP4 (e2m1 + e8m0/32)  rel err: {err_m:.4f}")
print(f"NVFP4 (e2m1 + e4m3/16)  rel err: {err_n:.4f}   ({err_m / err_n:.2f}x tighter)")
```

```text
MXFP4 (e2m1 + e8m0/32)  rel err: 0.1172
NVFP4 (e2m1 + e4m3/16)  rel err: 0.0930   (1.26x tighter)
```

Same elements, same seed - the whole 1.26x gap is the scale side. Where does it come from? The pow2 scale can only take values `... 0.25, 0.5, 1, 2, 4, 8 ...`, so a block whose ideal scale is 5.9 gets 8: after scaling, its `amax` lands at `6 * 5.9/8 = 4.4` - using 73% of the grid's top and stranding the resolution below. The next fence measures the tax across all blocks:

```python
import torch

torch.manual_seed(0)
W = torch.randn(64, 64)
b32 = W.reshape(-1, 32)
scale_m = torch.pow(2.0, torch.ceil(torch.log2(b32.abs().amax(dim=1, keepdim=True).clamp_min(1e-12) / 6.0)))
scale_m = scale_m.to(torch.float8_e8m0fnu).to(torch.float32)
b16 = W.reshape(-1, 16)
scale_n = (b16.abs().amax(dim=1, keepdim=True).clamp_min(1e-12) / 6.0).to(torch.float8_e4m3fn).to(torch.float32)

use_m = (b32.abs().amax(dim=1, keepdim=True) / scale_m).flatten()
use_n = (b16.abs().amax(dim=1, keepdim=True) / scale_n).flatten()
print(f"e8m0: mean scale-use {use_m.mean():.2f} of 6.0, {(use_m < 4.5).float().mean():.0%} of blocks waste >25% of the grid")
print(f"e4m3: mean scale-use {use_n.mean():.2f} of 6.0, {(use_n < 4.5).float().mean():.0%} waste")
```

```text
e8m0: mean scale-use 4.37 of 6.0, 59% of blocks waste >25% of the grid
e4m3: mean scale-use 6.02 of 6.0, 0% waste
```

The e4m3 scale - a full FP8 grid with its own exponent and mantissa - can sit within 2% of the ideal scale for essentially every block. The e8m0 scale cannot: 59% of blocks waste more than a quarter of the grid's range. That is the pow2 tax, and it is the price MXFP4 pays for scales that cost one exponent byte, shift-and-multiply in hardware, and never overflow.

## NVFP4: Finer Blocks, e4m3 Scales, a Second Level

NVFP4 attacks the same tax from two directions. Halving the block to 16 elements means the scale tracks local magnitude twice as tightly - a block no longer pays for a neighbor's outlier. Giving the scale e4m3 instead of e8m0 restores the mantissa the pow2 rule throws away, as the 6.02 mean scale-use above shows. What e4m3 costs is range: its finite exponent cannot cover e8m0's reach from `2^-127` to `2^127`, so NVFP4 adds a **second level** - one fp32 per-tensor scale folded in before the per-block scales are computed. [4103](./4103-Double-Quantization.md) nested quantization to save scale bytes; NVFP4 nests the other way - it spends a fp32 scalar to keep every per-block scale inside e4m3's sweet range. The two-level rule also bounds the arithmetic: every product stays representable because the global magnitude lives in the fp32 level, not in the 4-bit elements.

The tables in [4101](./4101-GGUF-Physics.md) compared formats by bits-per-weight; MXFP4 and NVFP4 both store the same `0.5 byte/element` for elements - the entire quality difference lives in the scale column: 1 byte per 32 elements (e8m0) versus 1 byte per 16 (e4m3). NVFP4's scales cost one extra `1/16 byte/element` of storage to buy back the pow2 tax.

## Containment: What One Outlier Can Do

The real test of a block format is not clean Gaussian weights - it is the outlier. Plant one `100.0` in a std-1 matrix and watch where the damage lands:

```python
import torch


def e2m1_qdq(x):
    grid = torch.tensor([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0])
    sign, mag = x.sign(), x.abs()
    idx = (mag.unsqueeze(-1) - grid).abs().argmin(-1)
    return sign * grid[idx]


torch.manual_seed(0)
W = torch.randn(64, 64)
W[0, 0] = 100.0  # one outlier lands in exactly one block

b32 = W.reshape(-1, 32)
s32 = torch.pow(2.0, torch.ceil(torch.log2(b32.abs().amax(dim=1, keepdim=True).clamp_min(1e-12) / 6.0)))
Q32 = e2m1_qdq(b32 / s32) * s32
b16 = W.reshape(-1, 16)
s16 = (b16.abs().amax(dim=1, keepdim=True).clamp_min(1e-12) / 6.0).to(torch.float8_e4m3fn).to(torch.float32).clamp_min(1e-12)
Q16 = e2m1_qdq(b16 / s16) * s16

nbr32, nbr16 = Q32[0, 1:], Q16[0, 1:]  # the outlier's neighbors share its scale
print(f"neighbors flushed to zero: MXFP4 {(nbr32 == 0).sum().item()}/31  NVFP4 {(nbr16 == 0).sum().item()}/15")
print(f"poisoned-block share     : MXFP4 1/{b32.shape[0]}  NVFP4 1/{b16.shape[0]}")
```

```text
neighbors flushed to zero: MXFP4 31/31  NVFP4 15/15
poisoned-block share     : MXFP4 1/128  NVFP4 1/256
```

The outlier's block takes a scale of `2^5 = 32`; its neighbors, natural values near `0.3`, now divide to `0.01` and round straight to zero - every neighbor in the poisoned block is destroyed. But the destruction **stops at the block boundary**: every other block keeps its own clean scale, and halving the block halves the poisoned share. Scales are recomputed per block precisely so that damage has a blast radius. (The fence counts zeros, not tensor norms - the tensor-level relative error would *drop* when you plant the outlier, because the outlier dominates the norm and quantizes near-exactly. Norm-level metrics hide local damage; per-block audits expose it.)

## The Production Surface: gpt-oss Selective MXFP4

OpenAI's gpt-oss-20b is the reference deployment of MXFP4, and its `config.json` is a philosophy statement:

```json
{
  "quantization_config": {
    "modules_to_not_convert": [
      "model.layers.*.self_attn",
      "model.layers.*.mlp.router",
      "model.embed_tokens",
      "lm_head"
    ],
    "quant_method": "mxfp4"
  }
}
```

Not "quantize everything" - quantize the expert MLPs and nothing else. The fence rebuilds the parameter census from the config's own constants and prices the decision:

```python
HIDDEN, LAYERS, EXPERTS, INTER = 2880, 24, 32, 2880
HEADS, KV_HEADS, HEAD_DIM, VOCAB = 64, 8, 64, 201088  # openai/gpt-oss-20b config.json

qo = HEADS * HEAD_DIM
per_expert = 3 * INTER * HIDDEN             # gate_proj, up_proj, down_proj
expert_p = LAYERS * EXPERTS * per_expert
attn_p = LAYERS * (2 * HIDDEN * qo + 2 * HIDDEN * KV_HEADS * HEAD_DIM)
router_p = LAYERS * HIDDEN * EXPERTS
embed_p = 2 * VOCAB * HIDDEN                # embed_tokens + lm_head (tie_word_embeddings: false)
total_p = expert_p + attn_p + router_p + embed_p

GB = 1024 ** 3
bf16_gb = total_p * 2 / GB
mx_bytes = expert_p * (0.5 + 1 / 32)        # e2m1 packed two-per-byte + one e8m0 byte per 32
rest_p = total_p - expert_p
mx_gb = mx_bytes / GB + rest_p * 2 / GB     # excluded modules stay bf16

print(f"expert params    : {expert_p / 1e9:.2f}B  ({expert_p / total_p:.1%} of {total_p / 1e9:.2f}B total)")
print(f"bf16 whole model : {bf16_gb:.1f} GB")
print(f"mxfp4 experts    : {mx_gb:.1f} GB   ({bf16_gb / mx_gb:.2f}x smaller, rest stays bf16)")
```

```text
expert params    : 19.11B  (91.4% of 20.91B total)
bf16 whole model : 38.9 GB
mxfp4 experts    : 12.8 GB   (3.04x smaller, rest stays bf16)
```

The MoE architecture is what makes selective quantization rational: 32 experts per layer means 91.4% of all parameters live in expert MLPs - matrices whose weights are the most statistically ordinary tensors in the network. Attention's weight matrices and the router decide *which* expert runs; disturbing them disturbs everything. The ledger shows the payoff: 38.9 GB of bf16 shrinks to 12.8 GB - the shipped checkpoint's actual size - while every sensitive module keeps bf16. This is [4102](./4102-EXL2-and-AWQ.md)'s calibration insight in config form: *which* tensors you quantize matters as much as *how*.

`transformers` exposes the config as a class, constructible locally with no network:

```python
from transformers import GptOssConfig, Mxfp4Config

EXCLUDES = [
    "model.layers.*.self_attn",
    "model.layers.*.mlp.router",
    "model.embed_tokens",
    "lm_head",
]
qcfg = Mxfp4Config(modules_to_not_convert=list(EXCLUDES))
model_cfg = GptOssConfig(num_local_experts=32, num_experts_per_tok=4, quantization_config=qcfg)
qc = model_cfg.quantization_config
print("quantization_config:", type(qc).__name__, "-", qc.quant_method.name)
for e in qc.modules_to_not_convert:
    print("  not converted:", e)
```

```text
quantization_config: Mxfp4Config - MXFP4
  not converted: model.layers.*.self_attn
  not converted: model.layers.*.mlp.router
  not converted: model.embed_tokens
  not converted: lm_head
```

`Mxfp4Config` carries `modules_to_not_convert` and a `dequantize: bool` flag; the load-time quantizer class is `Mxfp4HfQuantizer`, which validates that the target device is cuda, xpu, or cpu and that `accelerate` is installed, then swaps the expert weights through the MX kernels.

## torchao: The Research and Training Surface

Where `transformers` loads shipped checkpoints, `torchao` builds MX tensors from scratch - and composes with [5405](../../phase5-finetuning/5400-distributed-training/5405-FSDP2-and-torchao.md)'s `DTensor` world via `local_map`. The API hands back an `MXTensor` whose element dtype is the real `torch.float4_e2m1fn_x2`:

```python
import torch
from torchao.prototype.mx_formats.config import ScaleCalculationMode
from torchao.prototype.mx_formats.mx_tensor import MXTensor

W = torch.randn(256, 128)
W_mx = MXTensor.to_mx(
    W,
    torch.float4_e2m1fn_x2,
    block_size=32,
    scaling_mode=ScaleCalculationMode.RCEIL,  # the OCP spec's round-up; the API default is FLOOR
)
W_back = W_mx.to_dtype(torch.float32)
print("mx shape:", tuple(W_mx.shape), "elem dtype:", W_mx.elem_dtype)
print("round-trip rel err:", f"{((W - W_back).norm() / W.norm()).item():.4f}")
```

> **Environment gap:** `torchao` is an optional third-party package the QA environment does not install; this fence documents the install requirement (`pip install torchao`) and is accepted as `ENV-GAP:torchao` in the exec census.

The `scaling_mode=` line is the fence's whole point: torchao's default is `ScaleCalculationMode.FLOOR`, which rounds the scale *down* and violates the OCP spec's round-up - the same pow2-tax geometry measured above, but self-inflicted. Pass `RCEIL` (round-ceiling) to match the spec and the gpt-oss checkpoints. NVFP4 lives on the same prototype path with the e4m3/two-level machinery; its fast kernels are Blackwell (SM100) targets, so on other hardware the `MXTensor` runs in emulated mode - correct math, reference speed.

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `NotImplementedError: copy_kernel` casting `torch.float4_e2m1fn_x2` on CPU | the dtype exists but torch 2.12 has no CPU cast path for 4-bit storage | emulate the element step with the e2m1 grid (as the fences do); real casts need the CUDA kernels |
| e8m0 scales come out rounded-to-nearest, small blocks clip | `.to(torch.float8_e8m0fnu)` rounds to nearest, but the OCP spec says round the scale **up** | compute the pow2 ceiling yourself (`2^ceil(log2(amax/6))`), then pass through e8m0 to prove representability |
| torchao MX quantization quietly worse than expected | `MXTensor.to_mx` defaults to `ScaleCalculationMode.FLOOR`, not the spec's round-up | pass `scaling_mode=ScaleCalculationMode.RCEIL` explicitly |
| tensor-level relative error *improves* after planting an outlier | the outlier dominates the Frobenius norm and quantizes near-exactly, masking destroyed neighbors | audit per-block (zeros count, per-block rel err), never per-tensor, when outliers are in play |
| `ImportError: cannot import name 'Mxfp4HQQQuantizer'` | the requant backends are optional extras; the loadable surface is `Mxfp4Config` + `Mxfp4HfQuantizer` | import `Mxfp4Config` from `transformers`; add the HQQ/GPTQ extras only for requantization workflows |
| `ValueError` at `from_pretrained` with an MXFP4 checkpoint | `Mxfp4HfQuantizer.validate_environment` requires device cuda/xpu/cpu and `accelerate` installed | load on a supported device; `pip install accelerate` |
| `dequantize=True` blows the memory budget back up | the flag loads MXFP4 checkpoints as bf16 (for fine-tuning/QAT) - the 3.04x win is opt-in and reversible | keep `dequantize=False` for serving; accept bf16 memory only when you will train |
| NVFP4 `MXTensor` runs but benchmarks look awful | NVFP4's fast kernels are Blackwell (SM100) targets; elsewhere it runs emulated | benchmark only on SM100, or compare against the emulated baseline, never against BF16 kernels |
| GGUF `Q4_0` and MXFP4 treated as interchangeable "4-bit" | same bit budget, different geometry: linear integer grid vs nonlinear FP grid with FP8 scales | convert through fp16/bf16 intermediates; never assume per-block parameters transfer between format families |

## Summary

MXFP4 and NVFP4 are one idea in two calibrations: split every weight into 4-bit e2m1 elements and tiny quantized scales, recomputed per block. The fences make the differences arithmetic instead of folklore - the pow2 scale tax costs MXFP4 1.26x relative error and strands 59% of its blocks below 75% of the grid, while NVFP4's e4m3 scales-per-16 plus fp32 second level recovers it; containment bounds any single outlier's blast radius to its own block. gpt-oss-20b shows the deployment thesis: quantize the 91.4% that is expert MLPs, keep the decision-making 8.6% in bf16, and 38.9 GB becomes 12.8 GB. `transformers`' `Mxfp4Config` loads the shipped artifacts; `torchao`'s `MXTensor` builds new ones - with the trap that its default scale mode floors where the spec ceils. The through-line with [4101](./4101-GGUF-Physics.md) and [4103](./4103-Double-Quantization.md): block quantization is always a negotiation between scale precision and scale bytes, and the MX formats are the point where the negotiation moved into the hardware.

## References

### Related Minder Academy Documents

- [4101: GGUF Physics](./4101-GGUF-Physics.md) - the block-grid ancestor: `Q4_0`'s integer grid and fp16 scales
- [4102: EXL2 and AWQ](./4102-EXL2-and-AWQ.md) - calibration-driven 4-bit; the selective-quantization instinct MXFP4 configs inherit
- [4103: Double Quantization](./4103-Double-Quantization.md) - nesting quantization levels; NVFP4's second level in reverse
- [4301: QAT Foundations](../4300-quantization-aware-training/4301-QAT-Foundations.md) - training through a quantizer; the bridge from post-training MXFP4 to quantization-aware training
- [5405: FSDP2 and torchao](../../phase5-finetuning/5400-distributed-training/5405-FSDP2-and-torchao.md) - the `DTensor` world `MXTensor` composes with via `local_map`
- [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) - serving engines for the shipped MXFP4 checkpoints

### Primary Sources

- OCP Microscaling Formats (MX) Specification - the e2m1/e8m0 element-scale pair and the 32-element block, scale round-up rule.
- NVIDIA NVFP4 announcement and docs (`docs.nvidia.com`) - e4m3 scales per 16 elements, fp32 per-tensor second level, Blackwell SM100 kernels.
- PyTorch docs: `torch.float4_e2m1fn_x2`, `torch.float8_e8m0fnu`, `torch.float8_e4m3fn` - the dtype surface the fences run on.
- torchao (`github.com/pytorch/ao`), `torchao.prototype.mx_formats.mx_tensor` - `MXTensor.to_mx`, `ScaleCalculationMode`, the in-source admission that the FLOOR default should be RCEIL.
- transformers docs: `Mxfp4Config`, `Mxfp4HfQuantizer` - the load-time surface for gpt-oss checkpoints.
- `openai/gpt-oss-20b` model card and `config.json` - the selective-quantization config and the parameter census constants.

---

## Next Steps

- Next Module: **[4200: KV Cache](../4200-kv-cache/README.md)**
- Continue with: **[4301: QAT Foundations](../4300-quantization-aware-training/4301-QAT-Foundations.md)** - train through the quantizer instead of quantizing after
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Reproduce the pow2 tax at your own scale: quantize a real `nn.Linear` weight both ways, then plot per-block scale-use histograms for e8m0/32 and e4m3/16 - find the block size where the tax gap disappears.
