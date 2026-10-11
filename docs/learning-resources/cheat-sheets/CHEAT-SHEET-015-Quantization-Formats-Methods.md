---
Document ID: CHEAT-SHEET-015
Title: "CHEAT-SHEET-015: Quantization Formats & Methods"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'quantization', 'gguf', 'exl2']
---

# CHEAT-SHEET-015: Quantization Formats & Methods

## Quick Reference for Quantization

**Version:** 1.0

Every quantization choice is two decisions stacked: the bits-per-weight
arithmetic, and the runtime the format actually executes on. This sheet
maps the block layouts behind the bpw numbers, the three GGUF families,
the GPU-only formats, and the fit rules that pick between them.

---

## Bits-Per-Weight Is the Arithmetic

A quantized block's size in bytes, times eight, divided by its weight
count — that is the whole bpw story. Q4_0 stores one FP16 scale plus 32
four-bit codes per 32-weight block: (2 + 16) x 8 / 32 = 4.5 bpw. Q4_K
stores 144 bytes per 256-weight super-block: 4.5 bpw again — the K-quant
spends the extra bytes on 8 sub-block scales instead of raw payload, which
is why it reads ~5% better perplexity at the same size. The scale d maps
the integer range back to weights (max|w|/7, codes clamped to [-8, 7]),
and the error per weight is bounded by d/2. Raw payload is not VRAM:
7B at 4.5 bpw is 3.94 GB of weights, and buffers take the footprint to
the ~4.5 GB the sizing tables quote.

```python
import math

def quantize_q4_0(weights):
    """One 32-weight block -> (fp16 scale, 4-bit codes in [-8, 7])."""
    d = max(abs(w) for w in weights) / 7.0
    if d == 0:
        d = 1e-8
    q = [max(-8, min(7, round(w / d))) for w in weights]
    return d, q

BLOCK = [0.5 * math.sin(i) for i in range(32)]
d, q = quantize_q4_0(BLOCK)
err = max(abs(w - d * c) for w, c in zip(BLOCK, q))
print("Q4_0 scale:", round(d, 4), "| max err:", round(err, 5),
      "| bound d/2:", round(d / 2, 5))

bpw_q4_0 = (2 + 16) * 8 / 32
bpw_q4_k = 144 * 8 / 256
print("bpw: Q4_0", bpw_q4_0, "| Q4_K", bpw_q4_k, "| IQ4_XS", 4.25)
print("7B raw weights @4.5 bpw: %.2f GB (buffers take VRAM to ~4.5 GB)"
      % (7e9 * 4.5 / 8 / 1e9))
```

---

## Three GGUF Families

| Family | Scheme | Best range | Trade |
| --- | --- | --- | --- |
| Legacy (Q4_0/Q5_0/Q8_0) | Linear, 1 scale per 32 | tool compatibility | keep for tools, not quality |
| K-quants (Q4_K..Q6_K) | Linear, 8 scales per 256 | 4.5-8 bpw | the default at 4.5 bpw and above |
| I-quants (IQ family) | Non-linear codebook | 1.5-4.25 bpw | wins below ~4 bpw, slower on CPU |

The I-quant codebook maps small weight groups to reference vectors —
shape information no linear scale-and-offset format expresses. Its
`imatrix` runs calibration text through the model and records, per
weight, how much its error influences activations, so fidelity is spent
where it matters; it is essential, not optional, for IQ formats. Picks:
Q4_K_M is the default balanced choice, Q4_K_S when every 100 MB matters,
Q6_K when VRAM allows (near-lossless), IQ4_XS for Q4_K_M-class quality
roughly 0.25 bpw smaller.

| Format | bpw | Typical use |
| --- | --- | --- |
| IQ1_S / IQ1_M | 1.5 / 1.75 | extreme compression, heavy quality loss |
| IQ2_XXS / IQ2_XS / IQ2_M | 2.06 / 2.31 / 2.70 | 2-bit territory where K-quants fall apart |
| IQ3_XXS / IQ3_S | 3.06 / 3.44 | low-3-bit fallback below Q3_K |
| IQ4_XS | 4.25 | Q4_K_M-class quality, ~0.25 bpw smaller |

---

## The GPU-Only Formats

| Method | PPL vs fp16 | Speed | Sweet spot |
| --- | --- | --- | --- |
| 8-bit | +2% | fast | production near-fp16 |
| GPTQ 4b | +5% | medium | Hessian-driven PTQ, calibrated on ~128 c4 samples |
| AWQ 4b | +3% | fast | activation-aware quality |
| EXL2 4.5 | +4% | very fast | VRAM-only speed |
| GGUF Q4_K | +6% | medium | CPU/GPU hybrid |

AWQ's salient-weight rule: not all weights are equal — about 1% of
weights carry roughly half the information. Calibration activation
scales times weight magnitudes select that top 1%, which stays in fp16
while the rest quantizes; that is its 2-3% perplexity edge over GPTQ's
5-7%. GPTQ is Hessian-driven, block-wise, and calibration-dependent
(group_size 128, damp 0.01). EXL2's converter runs a measurement pass
and redistributes a per-layer 2/3/4/5/6/8-bit mix to land on ONE
average-BPW target (`-b 4.5`); there is no per-layer CLI to steer, and
`-hb` raises the head bits. Its CUDA tensor-core layout is the speed:
~90 tok/s at 8B/4.5 bpw vs ~45 for GGUF Q4_K on the same card — 2x.

---

## Fit the Runtime, Then the Card

Decode is memory-bandwidth-bound: every generated token reads every
active weight once. VRAM delivers 200-900 GB/s, system RAM 25-100 —
so partial offload falls off a cliff, not a slope (7B Q4_K_M on an
RTX 3060: -ngl 32 gives 35-45 tok/s, -ngl 24 gives 7-9, CPU-only 5-7).
Either the model fits fully on the GPU, or the CPU layers dominate.

| GPU VRAM | Fully offloaded target |
| --- | --- |
| 8 GB | 7-8B @ Q4_K_M |
| 12 GB | 13B @ Q4_K_M, or 7-8B @ Q6_K |
| 24 GB | 30B+ @ Q4_K_M, or 13B @ Q8_0 |
| 48 GB+ | 70B @ Q4_K_M |

KV cache quantization (`-ctk q8_0 -ctv q8_0`) roughly halves KV memory
for ~1% quality cost. Conversion rules: always quantize from the FP16
master (requantizing compounds error), merge LoRA adapters first —
converters do not apply them — and verify the chat template survived.

---

## Troubleshooting

| Symptom | Root cause | Fix |
| --- | --- | --- |
| Quality collapses below 3 bits | linear scale-and-offset loses fidelity; K-quants fall apart under ~4 bpw | switch to I-quants with imatrix, or stay at 4.5 bpw |
| Quantized model slower than the benchmark promised | EXL2/AWQ are GPU-only formats; the workload is hybrid offload | match format to runtime: GGUF for hybrid/CPU, EXL2 for VRAM-only |
| Partial -ngl offload barely helps | decode is bandwidth-bound; CPU layers read 25-100 GB/s vs VRAM 200-900 | fit fully or accept the cliff; measure with llama-bench |
| Requantized an already-quantized file | quantizing from Q4 compounds error | start over from the FP16 master |
| LoRA adapter missing after conversion | converters do not apply adapters | merge_and_unload() first, then convert |
| AWQ/GPTQ quality worse than advertised | calibration text mismatched the target domain | quantize with domain-representative calibration data |

---

**Quick Reference for:**

- [Module 4101: GGUF Physics](../../phases/phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)
- [Module 4102: EXL2 and AWQ](../../phases/phase4-quantization/4100-low-bit/4102-EXL2-and-AWQ.md)
- [Guide 4408: Quantizing for Production](../../phases/phase4-quantization/4400-advanced-techniques/guides/4408-Quantizing-for-Production.md)
- [CHEAT-SHEET-009: Local Inference](./CHEAT-SHEET-009-Local-Inference.md)
